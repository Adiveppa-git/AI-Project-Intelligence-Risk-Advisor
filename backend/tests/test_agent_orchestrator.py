"""Tests for Multi-Agent Orchestrator Service."""

import pytest

from app.models.agent_models import (
    AgentAnalysisRequest,
    MultiAgentAnalysisRequest,
    ProjectIntelligenceReport,
)
from app.services.agent_orchestrator import AgentOrchestratorService


@pytest.fixture
def enterprise_project_text() -> str:
    return """
    Project Title: Global Data Hub

    Objectives:
    - Build scalable enterprise data ingestion pipelines.
    - Guarantee 99.9% uptime for business telemetry.

    Deliverables:
    - Deliverable 1: Data Pipeline Core (Owner: Alice Chen, Deadline: 2026-09-01, Status: Pending)

    Milestones:
    - Milestone 1: Core Platform Alpha - Target Date: 2026-09-15 (Owner: Alice Chen)

    Schedule and Risks:
    - Milestone 1 is delayed due to failing database integration tests on staging.
    - Cloud infrastructure expenditure exceeded budget by 20%.

    Current Blockers:
    - Ingestion pipeline blocked by SecOps approval for OAuth tokens (Owner: Bob Martinez).

    Pending Decisions:
    - Pending decision on cloud storage tier (Decision Maker: David Kim, Deadline: 2026-08-30).

    Action Items:
    - Action Item 1: Bob Martinez to resolve SecOps compliance review by 2026-08-25 (Priority: Critical)
    - Action Item 2: Investigate failing staging tests (Priority: High)
    """


def test_orchestrator_runs_individual_agents(enterprise_project_text: str) -> None:
    orchestrator = AgentOrchestratorService(rag_service=None)
    req = AgentAnalysisRequest(text=enterprise_project_text)

    scope_res = orchestrator.analyze_scope(req)
    assert scope_res.project_title == "Global Data Hub"
    assert len(scope_res.expected_deliverables) >= 1

    risk_res = orchestrator.detect_risks(req)
    assert risk_res.schedule_risks_count >= 1

    blocker_res = orchestrator.identify_blockers(req)
    assert len(blocker_res.blockers) >= 1


def test_orchestrator_multi_agent_consolidation(enterprise_project_text: str) -> None:
    orchestrator = AgentOrchestratorService(rag_service=None)
    req = MultiAgentAnalysisRequest(text=enterprise_project_text)

    report = orchestrator.analyze_project(req)
    assert isinstance(report, ProjectIntelligenceReport)
    assert report.project_title == "Global Data Hub"
    assert report.project_health in ["Critical", "At Risk", "Needs Attention"]
    assert len(report.executive_summary) > 50
    assert len(report.key_recommendations) >= 1
    assert any("SecOps" in rec or "unblock" in rec.lower() for rec in report.key_recommendations)

    # Check child structures
    assert len(report.scope_and_deliverables.milestones) >= 1
    assert len(report.risk_and_forecasting.risks) >= 1
    assert len(report.blockers_and_actions.action_items) >= 2


def test_orchestrator_status() -> None:
    orchestrator = AgentOrchestratorService(rag_service=None)
    status_res = orchestrator.status()

    assert status_res.status == "ready"
    assert len(status_res.available_agents) == 3
    assert "Scope and Deliverable Extraction Agent" in status_res.available_agents


def test_orchestrator_agent_failure_isolation(enterprise_project_text: str) -> None:
    """Validate that unexpected failure in one agent does not crash the overall orchestration report."""
    from unittest.mock import MagicMock
    orchestrator = AgentOrchestratorService(rag_service=None)

    # Simulate failure in RiskAgent
    orchestrator.risk_agent.analyze = MagicMock(side_effect=RuntimeError("Simulated neural engine timeout"))

    req = MultiAgentAnalysisRequest(text=enterprise_project_text)
    report = orchestrator.analyze_project(req)

    assert isinstance(report, ProjectIntelligenceReport)
    assert report.project_title == "Global Data Hub"
    # Scope and Blocker results should be preserved
    assert len(report.scope_and_deliverables.milestones) >= 1
    assert len(report.blockers_and_actions.action_items) >= 1
    # Risk agent should have a degraded fallback result without crashing the pipeline
    assert report.risk_and_forecasting.confidence_score == 0.0
    assert "Risk detection failed" in report.risk_and_forecasting.delivery_concerns_summary


def test_orchestrator_with_document_ids_and_query() -> None:
    """Validate that query and document_ids in MultiAgentAnalysisRequest propagate to AgentAnalysisRequest."""
    from unittest.mock import MagicMock
    orchestrator = AgentOrchestratorService(rag_service=None)

    orchestrator.analyze_scope = MagicMock(return_value=orchestrator.scope_agent.analyze(""))
    orchestrator.identify_blockers = MagicMock(return_value=orchestrator.blocker_agent.analyze(""))
    orchestrator.detect_risks = MagicMock(return_value=orchestrator.risk_agent.analyze(""))

    req = MultiAgentAnalysisRequest(
        query="identify critical security blockers",
        document_ids=["doc-charter-001", "doc-notes-002"],
        top_k=8,
    )
    report = orchestrator.analyze_project(req)
    assert isinstance(report, ProjectIntelligenceReport)

    call_args = orchestrator.analyze_scope.call_args[0][0]
    assert call_args.query == "identify critical security blockers"
    assert call_args.document_id == "doc-charter-001"
    assert call_args.top_k == 8


def test_end_to_end_multi_format_pipeline_with_real_sample_files(tmp_path) -> None:
    """Full End-to-End Test: PDF, DOCX, CSV, TXT ingestion -> RAG vector indexing -> Multi-Agent Orchestration.
    Validates that the entire system processes all four formats together and preserves document provenance.
    """
    from pathlib import Path
    from app.services.document_ingestion import DocumentIngestionService
    from app.services.rag_pipeline import RAGPipelineService

    sample_dir = Path(__file__).resolve().parents[1] / "sample_data"
    pdf_path = sample_dir / "project_charter.pdf"
    docx_path = sample_dir / "progress_report.docx"
    csv_path = sample_dir / "task_list.csv"
    txt_path = sample_dir / "meeting_notes.txt"

    assert pdf_path.exists(), f"Sample PDF missing: {pdf_path}"
    assert docx_path.exists(), f"Sample DOCX missing: {docx_path}"
    assert csv_path.exists(), f"Sample CSV missing: {csv_path}"
    assert txt_path.exists(), f"Sample TXT missing: {txt_path}"

    ingestion_service = DocumentIngestionService()
    rag_service = RAGPipelineService(
        chunk_size=500,
        chunk_overlap=50,
        storage_path=tmp_path / "chroma",
        collection_name="e2e_test_collection",
    )

    # 1. Ingest all 4 document formats
    pdf_doc = ingestion_service.ingest("project_charter.pdf", pdf_path.read_bytes())
    docx_doc = ingestion_service.ingest("progress_report.docx", docx_path.read_bytes())
    csv_doc = ingestion_service.ingest("task_list.csv", csv_path.read_bytes())
    txt_doc = ingestion_service.ingest("meeting_notes.txt", txt_path.read_bytes())

    assert pdf_doc.file_type == "pdf" and len(pdf_doc.text) > 100
    assert docx_doc.file_type == "docx" and len(docx_doc.text) > 100
    assert csv_doc.file_type == "csv" and len(csv_doc.text) > 100
    assert txt_doc.file_type == "txt" and len(txt_doc.text) > 100

    # 2. Index all 4 documents into RAG vector store
    _, pdf_stored = rag_service.index_document(pdf_doc)
    _, docx_stored = rag_service.index_document(docx_doc)
    _, csv_stored = rag_service.index_document(csv_doc)
    _, txt_stored = rag_service.index_document(txt_doc)

    assert pdf_stored > 0
    assert docx_stored > 0
    assert csv_stored > 0
    assert txt_stored > 0
    assert rag_service.vector_store.count() >= 4

    # 3. Perform semantic searches against the multi-format index
    search_scope = rag_service.search("project objectives deliverables milestones", top_k=5)
    search_risks = rag_service.search("schedule delay risks budget overrun", top_k=5)
    search_blockers = rag_service.search("blockers secops approval failing migration", top_k=5)

    assert len(search_scope) >= 1
    assert len(search_risks) >= 1
    assert len(search_blockers) >= 1

    # Verify provenance filenames in search results
    found_files = {r.metadata.get("filename") for r in search_scope + search_risks + search_blockers}
    assert len(found_files) >= 2

    # 4. Run Multi-Agent Orchestrator over the persistent RAG vector index
    orchestrator = AgentOrchestratorService(rag_service=rag_service)
    report = orchestrator.analyze_project(
        MultiAgentAnalysisRequest(
            query="Enterprise Cloud Analytics Platform scope deliverables risks blockers",
            top_k=15,
        )
    )

    assert isinstance(report, ProjectIntelligenceReport)
    assert "Enterprise Cloud Analytics Platform" in report.project_title or report.project_title != "Unknown"
    assert report.project_health in ["Critical", "At Risk", "Needs Attention"]
    assert len(report.sources_analyzed) >= 2
    assert len(report.executive_summary) > 50

    # Check Scope Agent results
    assert len(report.scope_and_deliverables.milestones) >= 1 or len(report.scope_and_deliverables.expected_deliverables) >= 1

    # Check Risk Agent results
    assert len(report.risk_and_forecasting.risks) >= 1

    # Check Blocker Agent results
    assert len(report.blockers_and_actions.blockers) >= 1
    assert len(report.blockers_and_actions.action_items) >= 1

    # Check cross-document provenance in extracted findings
    all_evidence = (
        report.scope_and_deliverables.evidence_snippets
        + [ev for r in report.risk_and_forecasting.risks for ev in r.supporting_evidence]
        + [ev for b in report.blockers_and_actions.blockers for ev in b.supporting_evidence]
    )
    evidence_filenames = {ev.filename for ev in all_evidence if ev.filename != "Unknown"}
    assert len(evidence_filenames) >= 2, f"Expected multi-format evidence filenames, got: {evidence_filenames}"

