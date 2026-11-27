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


def test_orchestrator_health_score_and_dashboard_compatibility(enterprise_project_text: str) -> None:
    orchestrator = AgentOrchestratorService(rag_service=None)
    req = MultiAgentAnalysisRequest(text=enterprise_project_text)
    report = orchestrator.analyze_project(req)

    # 1. Health Score Validation
    assert isinstance(report.overall_health_score, int)
    assert 10 <= report.overall_health_score <= 100
    assert report.overall_health_status in ["Healthy", "Needs Attention", "At Risk", "Critical"]
    assert report.overall_health_status == report.project_health
    assert report.timestamp is not None

    # 2. Dual-Schema Compatibility Fields
    assert report.scope_analysis == report.scope_and_deliverables
    assert report.risk_analysis == report.risk_and_forecasting
    assert report.blocker_analysis == report.blockers_and_actions
    assert report.has_partial_failures is False
    assert report.partial_failure_details == []

    # 3. Serializability
    dumped = report.model_dump()
    assert "overall_health_score" in dumped
    assert "overall_health_status" in dumped
    assert "scope_analysis" in dumped
    assert "risk_analysis" in dumped
    assert "blocker_analysis" in dumped
    json_str = report.model_dump_json()
    assert isinstance(json_str, str)


def test_orchestrator_complete_multi_agent_sample_corpus() -> None:
    """Validate unified corpus extraction across Scope, Risk, and Blocker agents."""
    corpus = """Project Title: Enterprise Cloud Analytics Platform (ECAP)
Document Type: Official Project Charter & Architecture Specification

3. Key Expected Deliverables and Milestones
- Deliverable 1: Cloud Telemetry Pipeline (Owner: Alice Chen, Deadline: 2026-08-15)
- Deliverable 2: Unified RBAC Gateway (Owner: Bob Martinez, Deadline: 2026-09-30)
- Deliverable 3: Real-Time Dashboard (Owner: Carol Vance, Deadline: 2026-11-20)
- Deliverable 4: Data Warehouse Sync (Owner: David Kim, Deadline: 2026-12-01)
- Milestone 1: Architectural Foundation (Target Date: 2026-08-30, Owner: Alice Chen)
- Milestone 2: Security Sign-off (Target Date: 2026-10-15, Owner: Bob Martinez)
- Milestone 3: Production Rollout (Target Date: 2026-12-10, Owner: David Kim)

4. Scope Boundaries
In-Scope: Kubernetes clusters, Kafka streaming, OAuth2 RBAC gateway, Snowflake synchronization.
Out-of-Scope: Legacy mainframe hardware, native mobile applications, public third-party endpoints.

# Meeting Notes: Sprint 14 Technical Sync
## Current Blockers
- Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
- Blocker 2: Database migration scripts failing on staging cluster due to schema mismatch with legacy tables.
- Blocker 3: Staging cluster environment is experiencing frequent memory out-of-bounds crashes, halting integration tests.

## Pending Decisions
- Decision 1: Pending decision on selecting ClickHouse vs Snowflake for warm telemetry storage tier (Decision Maker: David Kim, Deadline: 2026-09-25).
- Decision 2: Pending decision regarding Kafka partition sizing and retention policy sign-off (Decision Maker: Alice Chen, Deadline: 2026-09-28).

## Action Items
- Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
- Action Item 2: Alice Chen to profile memory usage in telemetry worker pods by 2026-09-24 (Priority: High)
- Action Item 3: Investigate failing database migration scripts on staging (Assigned to: Unassigned, Deadline: 2026-09-22, Priority: High)
- Action Item 4: Carol Vance to mock dashboard response models by 2026-09-28 (Priority: Medium)
- Action Item 5: David Kim to configure automated pod restart policies by 2026-09-26 (Priority: Medium)
- Action Item 6: Clean up stale test accounts in staging database (Assigned to: Unassigned, Deadline: 2026-09-30, Priority: Low)

Schedule and Delivery Risks
- Milestone 2 is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.
- Target completion date of 2026-10-15 is at risk of slipping into November 2026.
- Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
- Dependency gap: The data warehouse sync pipeline depends on the completion of the Kafka brokers.
- Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.
- Resource constraint: The frontend engineering team is currently understaffed, creating a bandwidth bottleneck.
- Shortage of senior site reliability engineers has contributed to deployment pipeline instability.
- Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.
"""
    orchestrator = AgentOrchestratorService(rag_service=None)
    req = MultiAgentAnalysisRequest(text=corpus)
    report = orchestrator.analyze_project(req)

    # Scope verification: 4 deliverables, at least 3 milestones
    assert len(report.scope_and_deliverables.expected_deliverables) == 4
    assert len(report.scope_and_deliverables.milestones) >= 3

    # Risk verification: at least 8 risks detected (including cross-module blocker risks)
    assert len(report.risk_and_forecasting.risks) >= 8

    # Blocker verification: 3 blockers, action items, pending decisions
    assert len(report.blockers_and_actions.blockers) >= 3
    assert len(report.blockers_and_actions.action_items) >= 6
    assert len(report.blockers_and_actions.pending_decisions) >= 2

    # Consistency between executive summary numbers and structured findings
    assert f"{len(report.scope_and_deliverables.expected_deliverables)} deliverable(s)" in report.executive_summary
    assert f"{len(report.risk_and_forecasting.risks)} active risk(s)" in report.executive_summary
    assert f"{len(report.blockers_and_actions.blockers)} blocker(s)" in report.executive_summary
    assert f"{len(report.blockers_and_actions.pending_decisions)} pending decision(s)" in report.executive_summary

    # Overall health calculation
    assert report.overall_health_status == "Critical"
    assert report.overall_health_score < 50

    # Cross-agent blocker and risk relationship linking verification
    assert any("BLK-001" in r.related_blocker_ids or r.related_blocker_id == "BLK-001" for r in report.risk_and_forecasting.risks)
    assert any("BLK-002" in r.related_blocker_ids or r.related_blocker_id == "BLK-002" for r in report.risk_and_forecasting.risks)
    assert any("BLK-003" in r.related_blocker_ids or r.related_blocker_id == "BLK-003" for r in report.risk_and_forecasting.risks)
    assert any("RSK-001" in b.related_risk_ids or b.related_risk_id == "RSK-001" for b in report.blockers_and_actions.blockers)


def test_orchestrator_deduplication_and_cross_agent_linking_full_corpus() -> None:
    """Validate deduplication and cross-agent linking across the complete 4-document integrated corpus."""
    full_corpus = """Project Title: Enterprise Cloud Analytics Platform (ECAP)
Document Type: Official Project Charter & Architecture Specification

3. Key Expected Deliverables and Milestones
- Deliverable 1: Cloud Telemetry Pipeline (Owner: Alice Chen, Deadline: 2026-08-15)
- Deliverable 2: Unified RBAC Gateway (Owner: Bob Martinez, Deadline: 2026-09-30)
- Deliverable 3: Real-Time Dashboard (Owner: Carol Vance, Deadline: 2026-11-20)
- Deliverable 4: Data Warehouse Sync (Owner: David Kim, Deadline: 2026-12-01)
- Milestone 1: Architectural Foundation (Target Date: 2026-08-30, Owner: Alice Chen)
- Milestone 2: Security Sign-off (Target Date: 2026-10-15, Owner: Bob Martinez)
- Milestone 3: Production Rollout (Target Date: 2026-12-10, Owner: David Kim)

4. Scope Boundaries
In-Scope: Kubernetes clusters, Kafka streaming, OAuth2 RBAC gateway, Snowflake synchronization.
Out-of-Scope: Legacy mainframe hardware, native mobile applications, public third-party endpoints.

# Meeting Notes: Sprint 14 Technical Sync and Risk Review
## Current Blockers
- Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
- Blocker 2: Database migration scripts failing on staging cluster due to schema mismatch with legacy tables.
- Blocker 3: Staging cluster environment is experiencing frequent memory out-of-bounds crashes, halting integration tests.

## Pending Decisions
- Decision 1: Pending decision on selecting ClickHouse vs Snowflake for warm telemetry storage tier (Decision Maker: David Kim, Deadline: 2026-09-25).
- Decision 2: Pending decision regarding Kafka partition sizing and retention policy sign-off (Decision Maker: Alice Chen, Deadline: 2026-09-28).

## Unresolved Issues
- Issue: Intermittent network latency spikes exceeding 1200ms when querying cross-region replicas.
- Issue: Incomplete test coverage on token refresh failure modes.
- Issue: Flaky integration tests in the continuous delivery pipeline.

## Delayed Activities
- Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.
- Activity: Frontend telemetry chart rendering is behind schedule due to missing API specification.

## Action Items
- Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
- Action Item 2: Alice Chen to profile memory usage in telemetry worker pods by 2026-09-24 (Priority: High)
- Action Item 3: Investigate failing database migration scripts on staging (Assigned to: Unassigned, Deadline: 2026-09-22, Priority: High)

Enterprise Cloud Analytics Platform - Monthly Progress Report
Schedule and Delivery Risks
- Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.
- The target completion date of 2026-10-15 is at risk of slipping into November 2026.
- Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
- Dependency gap: The data warehouse sync pipeline depends on the completion of the Kafka brokers and schema validation module.

Budget and Resource Constraints
- Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.
- Resource constraint: The frontend engineering team is currently understaffed, creating a bandwidth bottleneck for dashboard widget completion.
- Shortage of senior site reliability engineers has contributed to deployment pipeline instability.

Technical Bottlenecks
- Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.

Task ID,Task Name,Deliverable,Owner,Priority,Status,Deadline,Dependencies,Notes
TSK-101,Deploy Kafka Ingestion Brokers,Cloud Telemetry Ingestion Pipeline,Alice Chen,High,Completed,2026-08-10,None,Deployed to Kubernetes cluster successfully
TSK-102,Configure RBAC OAuth Gateway,Unified RBAC Security Gateway,Bob Martinez,Critical,In progress,2026-09-28,SecOps Approval,Blocked by security compliance review
TSK-103,Design Executive Chart Components,Real-Time Executive Dashboard,Carol Vance,Medium,In progress,2026-10-15,None,UI mockups approved by stakeholders
TSK-104,Execute Staging Database Migration,Automated Data Warehouse Sync,Unassigned,High,Pending,2026-09-30,Kafka Pipeline,Migration tests failing on staging
TSK-105,Cloud Cost Containment Audit,Budget Optimization,David Kim,High,Pending,2026-10-05,None,Cloud spend exceeded budget by 22%
TSK-106,Automate Multi-Region Failover,Cloud Infrastructure,David Kim,Medium,Pending,2026-11-15,Kubernetes Clusters,Pending secondary cloud provider account setup
TSK-107,Perform Load and Stress Testing,System Reliability,Unassigned,Medium,Pending,2026-11-01,Staging Database Migration,Requires stable staging environment
"""
    orchestrator = AgentOrchestratorService(rag_service=None)
    req = MultiAgentAnalysisRequest(text=full_corpus)
    report = orchestrator.analyze_project(req)

    # 1. Deduplication: risks should be between 10 and 14 (not the inflated 19)
    assert 10 <= len(report.risk_and_forecasting.risks) <= 15, f"Unexpected risk count: {len(report.risk_and_forecasting.risks)}"

    # 2. SecOps OAuth blocker should have exactly 1 canonical risk
    secops_risks = [r for r in report.risk_and_forecasting.risks if "oauth" in r.title.lower() or "secops" in r.title.lower()]
    assert len(secops_risks) == 1
    assert secops_risks[0].severity == "Critical"
    assert "BLK-001" in secops_risks[0].related_blocker_ids

    # 3. Database migration should have exactly 1 canonical risk
    db_risks = [r for r in report.risk_and_forecasting.risks if "migration" in r.title.lower()]
    assert len(db_risks) == 1
    assert "BLK-002" in db_risks[0].related_blocker_ids

    # 4. Memory crash should have exactly 1 canonical risk
    mem_risks = [r for r in report.risk_and_forecasting.risks if "memory" in r.title.lower()]
    assert len(mem_risks) == 1
    assert "BLK-003" in mem_risks[0].related_blocker_ids

    # 5. Cloud budget overrun should have exactly 1 canonical risk
    budget_risks = [r for r in report.risk_and_forecasting.risks if "budget" in r.category.lower()]
    assert len(budget_risks) == 1

    # 6. No raw CSV titles
    for r in report.risk_and_forecasting.risks:
        assert r.title.count(",") < 3, f"Raw CSV in risk title: {r.title}"

    # 7. Blockers deduplicated to exactly 3 active blockers
    assert len(report.blockers_and_actions.blockers) == 3
    for b in report.blockers_and_actions.blockers:
        assert len(b.related_risk_ids) >= 1

    # 8. Category counts strictly match length of risks
    assert sum(report.risk_and_forecasting.category_counts.values()) == len(report.risk_and_forecasting.risks)


