"""API Routes for AI Agents and Multi-Agent Orchestration."""

from fastapi import APIRouter, HTTPException, status

from app.api.rag_routes import rag_service
from app.models.agent_models import (
    AgentAnalysisRequest,
    AgentStatusResponse,
    BlockerAnalysisResult,
    MultiAgentAnalysisRequest,
    ProjectIntelligenceReport,
    RiskAnalysisResult,
    ScopeAnalysisResult,
)
from app.services.agent_orchestrator import AgentOrchestratorService

router = APIRouter(prefix="/agents", tags=["agents"])
orchestrator = AgentOrchestratorService(rag_service=rag_service)


@router.post(
    "/analyze-scope",
    response_model=ScopeAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Extract project scope, deliverables, and milestones",
)
def analyze_scope(request: AgentAnalysisRequest) -> ScopeAnalysisResult:
    """Run Scope and Deliverable Extraction Agent on uploaded or indexed project documentation."""
    try:
        return orchestrator.analyze_scope(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scope extraction failed: {str(exc)}",
        ) from exc


@router.post(
    "/detect-risks",
    response_model=RiskAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Detect project risks, schedule challenges, and delivery forecasts",
)
def detect_risks(request: AgentAnalysisRequest) -> RiskAnalysisResult:
    """Run Risk Detection and Delivery Forecasting Agent on project documentation."""
    try:
        return orchestrator.detect_risks(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk detection failed: {str(exc)}",
        ) from exc


@router.post(
    "/identify-blockers",
    response_model=BlockerAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Identify blockers, unresolved issues, decisions, and action items",
)
def identify_blockers(request: AgentAnalysisRequest) -> BlockerAnalysisResult:
    """Run Blocker and Action Item Identification Agent on project notes and documentation."""
    try:
        return orchestrator.identify_blockers(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Blocker identification failed: {str(exc)}",
        ) from exc


@router.post(
    "/analyze-project",
    response_model=ProjectIntelligenceReport,
    status_code=status.HTTP_200_OK,
    summary="Generate a consolidated multi-agent project intelligence report",
)
def analyze_project(request: MultiAgentAnalysisRequest) -> ProjectIntelligenceReport:
    """Coordinate Scope, Risk, and Blocker agents into a consolidated enterprise project intelligence report."""
    try:
        return orchestrator.analyze_project(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-agent project analysis failed: {str(exc)}",
        ) from exc


@router.get(
    "/status",
    response_model=AgentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check status of all AI agents and orchestrator",
)
def agent_status() -> AgentStatusResponse:
    """Inspect availability and readiness of the AI agents and underlying knowledge store."""
    try:
        return orchestrator.status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to read agent status: {str(exc)}",
        ) from exc
