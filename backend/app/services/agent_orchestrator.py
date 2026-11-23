"""Multi-Agent Orchestrator Service.

Coordinates Scope, Risk, and Blocker agents to generate consolidated
enterprise project intelligence and risk management reports.
"""

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.agents.blocker_agent import BlockerAgent
from app.agents.risk_agent import RiskAgent
from app.agents.scope_agent import ScopeAgent
from app.models.agent_models import (
    AgentAnalysisRequest,
    AgentStatusResponse,
    BlockerAnalysisResult,
    MultiAgentAnalysisRequest,
    ProjectIntelligenceReport,
    RiskAnalysisResult,
    ScopeAnalysisResult,
)
from app.services.rag_pipeline import RAGPipelineService


class AgentOrchestratorService:
    """Coordinates independent agents and consolidates cross-functional project intelligence."""

    def __init__(self, rag_service: RAGPipelineService | None = None) -> None:
        self.rag_service = rag_service or RAGPipelineService()
        self.scope_agent = ScopeAgent(rag_service=self.rag_service)
        self.risk_agent = RiskAgent(rag_service=self.rag_service)
        self.blocker_agent = BlockerAgent(rag_service=self.rag_service)

    def analyze_scope(self, request: AgentAnalysisRequest) -> ScopeAnalysisResult:
        """Execute Scope and Deliverable Extraction Agent independently."""
        return self.scope_agent.analyze(
            text=request.text,
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )

    def detect_risks(
        self,
        request: AgentAnalysisRequest,
        scope_context: ScopeAnalysisResult | None = None,
    ) -> RiskAnalysisResult:
        """Execute Risk Detection and Delivery Forecasting Agent independently."""
        return self.risk_agent.analyze(
            text=request.text,
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
            scope_context=scope_context,
        )

    def identify_blockers(self, request: AgentAnalysisRequest) -> BlockerAnalysisResult:
        """Execute Blocker and Action Item Identification Agent independently."""
        return self.blocker_agent.analyze(
            text=request.text,
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )

    def analyze_project(self, request: MultiAgentAnalysisRequest) -> ProjectIntelligenceReport:
        """Orchestrate all 3 agents to generate a consolidated Project Intelligence Report."""
        doc_id = request.document_ids[0] if request.document_ids else None
        agent_req = AgentAnalysisRequest(
            query=request.query,
            document_id=doc_id,
            text=request.text,
            top_k=request.top_k,
        )

        partial_failures: list[str] = []

        # 1. Execute Scope Agent with failure isolation
        try:
            scope_res = self.analyze_scope(agent_req)
        except Exception as exc:
            partial_failures.append(f"ScopeAgent failed: {str(exc)}")
            scope_res = ScopeAnalysisResult(
                project_title="Unknown",
                confidence_score=0.0,
                objectives=[],
                source_documents=[],
            )

        # 2. Execute Blocker Agent with failure isolation
        try:
            blocker_res = self.identify_blockers(agent_req)
        except Exception as exc:
            partial_failures.append(f"BlockerAgent failed: {str(exc)}")
            blocker_res = BlockerAnalysisResult(
                confidence_score=0.0,
                source_documents=[],
            )

        # 3. Execute Risk Agent with Scope context and failure isolation
        try:
            risk_res = self.detect_risks(agent_req, scope_context=scope_res)
        except Exception as exc:
            partial_failures.append(f"RiskAgent failed: {str(exc)}")
            risk_res = RiskAnalysisResult(
                overall_risk_level="Low",
                confidence_score=0.0,
                delivery_concerns_summary=f"Risk detection failed: {str(exc)}",
                source_documents=[],
            )

        # 4. Consolidate sources analyzed
        all_sources = list(
            dict.fromkeys(
                scope_res.source_documents
                + risk_res.source_documents
                + blocker_res.source_documents
            )
        )

        # 5. Determine Project Title
        project_title = scope_res.project_title if scope_res.project_title != "Unknown" else "Project Intelligence Analysis"

        # 6. Calculate Project Health
        project_health = self._compute_project_health(risk_res, blocker_res)

        # 7. Generate Executive Summary
        exec_summary = self._generate_executive_summary(
            project_title, project_health, scope_res, risk_res, blocker_res, partial_failures
        )

        # 8. Synthesize Key Recommendations
        recommendations = self._synthesize_recommendations(risk_res, blocker_res, partial_failures)

        return ProjectIntelligenceReport(
            report_id=str(uuid4()),
            project_title=project_title,
            generated_at=datetime.now(timezone.utc),
            sources_analyzed=all_sources,
            executive_summary=exec_summary,
            project_health=project_health,
            scope_and_deliverables=scope_res,
            risk_and_forecasting=risk_res,
            blockers_and_actions=blocker_res,
            key_recommendations=recommendations,
            partial_failures=partial_failures,
        )

    def status(self) -> AgentStatusResponse:
        """Check status of orchestrator, available agents, and underlying RAG service."""
        rag_ready = False
        chunks_count = 0
        details: dict[str, Any] = {}

        if self.rag_service:
            try:
                rag_status = self.rag_service.status()
                rag_ready = rag_status.get("status") == "ready"
                chunks_count = int(rag_status.get("indexed_chunks", 0))
                details["rag"] = rag_status
            except Exception as e:
                details["rag_error"] = str(e)

        return AgentStatusResponse(
            status="ready",
            available_agents=[
                "Scope and Deliverable Extraction Agent",
                "Risk Detection and Delivery Forecasting Agent",
                "Blocker and Action Item Identification Agent",
            ],
            rag_ready=rag_ready,
            total_indexed_chunks=chunks_count,
            details=details,
        )

    def _compute_project_health(
        self,
        risk_res: RiskAnalysisResult,
        blocker_res: BlockerAnalysisResult,
    ) -> Literal["Healthy", "Needs Attention", "At Risk", "Critical"]:
        active_blockers = [b for b in blocker_res.blockers if b.status != "resolved"]
        has_critical_risk = any(r.severity == "Critical" for r in risk_res.risks)
        has_critical_blocker = any("critical" in b.description.lower() for b in active_blockers)

        if has_critical_risk or has_critical_blocker:
            return "Critical"
        if risk_res.overall_risk_level in ["Critical", "High"] or len(active_blockers) >= 3:
            return "At Risk"
        if risk_res.overall_risk_level == "Medium" or blocker_res.unassigned_action_items_count > 0:
            return "Needs Attention"
        return "Healthy"

    def _generate_executive_summary(
        self,
        project_title: str,
        project_health: str,
        scope: ScopeAnalysisResult,
        risk: RiskAnalysisResult,
        blockers: BlockerAnalysisResult,
        partial_failures: list[str] | None = None,
    ) -> str:
        parts: list[str] = [
            f"Consolidated Project Intelligence Report for '{project_title}'.",
            f"Overall Project Health: {project_health}.",
            f"Identified {len(scope.milestones)} milestone(s) and {len(scope.expected_deliverables)} deliverable(s).",
            f"Detected {len(risk.risks)} active risk(s) ({risk.schedule_risks_count} schedule, {risk.budget_risks_count} budget).",
            f"Found {len(blockers.blockers)} blocker(s), {len(blockers.action_items)} action item(s) "
            f"({blockers.unassigned_action_items_count} unassigned), and {len(blockers.pending_decisions)} pending decision(s).",
        ]
        if risk.delayed_milestones_forecast:
            parts.append(
                f"Delivery forecasting warns of potential delays on {len(risk.delayed_milestones_forecast)} milestone(s)."
            )
        if partial_failures:
            parts.append(
                f"Warning: Partial analysis degradation detected: {'; '.join(partial_failures)}."
            )
        return " ".join(parts)

    def _synthesize_recommendations(
        self,
        risk: RiskAnalysisResult,
        blockers: BlockerAnalysisResult,
        partial_failures: list[str] | None = None,
    ) -> list[str]:
        recommendations: list[str] = []

        if partial_failures:
            recommendations.append(
                f"Attention: Re-run analysis for degraded component(s): {'; '.join(partial_failures)}."
            )

        # From blockers
        active_blockers = [b for b in blockers.blockers if b.status != "resolved"]
        if active_blockers:
            recommendations.append(
                f"Immediately unblock: {active_blockers[0].description} (Owner: {active_blockers[0].assigned_owner})."
            )

        # From unassigned action items
        if blockers.unassigned_action_items_count > 0:
            recommendations.append(
                f"Assign dedicated owners to {blockers.unassigned_action_items_count} currently unassigned action item(s)."
            )

        # From pending decisions
        if blockers.pending_decisions:
            recommendations.append(
                f"Escalate pending decision '{blockers.pending_decisions[0].description}' for executive sign-off."
            )

        # From risks
        high_critical_risks = [r for r in risk.risks if r.severity in ["Critical", "High"]]
        for r in high_critical_risks[:2]:
            recommendations.append(f"Mitigate {r.title}: {r.suggested_mitigation}")

        if not recommendations:
            recommendations.append("Continue tracking scheduled deliverables and maintain weekly syncs.")

        return recommendations
