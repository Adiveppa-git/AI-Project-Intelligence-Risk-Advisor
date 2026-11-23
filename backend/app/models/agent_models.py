from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class SourceEvidence(BaseModel):
    """Snippet of document evidence backing an extracted claim."""

    document_id: str | None = None
    filename: str = "Unknown"
    chunk_id: str | None = None
    snippet: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)


# ==========================================
# 1. Scope and Deliverables Models
# ==========================================

class DeliverableItem(BaseModel):
    deliverable_id: str
    name: str
    description: str | None = None
    owner: str = "Unknown"
    deadline: str = "Not specified"
    status: str = "pending"  # "pending", "completed", "in_progress", "unknown"
    evidence: list[SourceEvidence] = Field(default_factory=list)


class MilestoneItem(BaseModel):
    milestone_id: str
    name: str
    target_date: str = "Not specified"
    owner: str = "Unknown"
    status: str = "pending"
    deliverables: list[str] = Field(default_factory=list)
    evidence: list[SourceEvidence] = Field(default_factory=list)


class DeadlineItem(BaseModel):
    title: str
    date: str
    owner: str = "Unknown"
    evidence: list[SourceEvidence] = Field(default_factory=list)


class TeamResponsibility(BaseModel):
    role_or_person: str
    responsibility: str
    evidence: list[SourceEvidence] = Field(default_factory=list)


class ScopeAnalysisResult(BaseModel):
    project_title: str = "Unknown"
    objectives: list[str] = Field(default_factory=list)
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    expected_deliverables: list[DeliverableItem] = Field(default_factory=list)
    milestones: list[MilestoneItem] = Field(default_factory=list)
    start_date: str = "Not specified"
    end_date: str = "Not specified"
    important_deadlines: list[DeadlineItem] = Field(default_factory=list)
    team_responsibilities: list[TeamResponsibility] = Field(default_factory=list)
    assigned_owners: list[str] = Field(default_factory=list)
    pending_deliverables: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    source_documents: list[str] = Field(default_factory=list)
    evidence_snippets: list[SourceEvidence] = Field(default_factory=list)


# ==========================================
# 2. Risk Detection and Delivery Forecasting
# ==========================================

class RiskItem(BaseModel):
    risk_id: str
    title: str
    description: str
    category: str  # "Schedule", "Dependency", "Resource", "Budget", "Bottleneck", "Delivery"
    severity: Literal["Critical", "High", "Medium", "Low"]
    supporting_evidence: list[SourceEvidence] = Field(default_factory=list)
    affected_milestone_or_deliverable: str = "Not specified"
    potential_impact: str
    suggested_mitigation: str
    recommended_priority: Literal["Critical", "High", "Medium", "Low"]


class DelayedMilestoneForecast(BaseModel):
    milestone_name: str
    actual_deadline: str
    predicted_delay_reason: str
    delay_severity: Literal["Critical", "High", "Medium", "Low"]
    supporting_evidence: list[SourceEvidence] = Field(default_factory=list)


class DependencyGap(BaseModel):
    dependency: str
    impact: str
    status: str  # "Unresolved", "At risk", "Blocked", "Critical"
    supporting_evidence: list[SourceEvidence] = Field(default_factory=list)


class RiskAnalysisResult(BaseModel):
    overall_risk_level: Literal["Critical", "High", "Medium", "Low"] = "Low"
    risks: list[RiskItem] = Field(default_factory=list)
    schedule_risks_count: int = 0
    budget_risks_count: int = 0
    dependency_gaps: list[DependencyGap] = Field(default_factory=list)
    delayed_milestones_forecast: list[DelayedMilestoneForecast] = Field(default_factory=list)
    resource_constraints: list[str] = Field(default_factory=list)
    delivery_challenges: list[str] = Field(default_factory=list)
    potential_bottlenecks: list[str] = Field(default_factory=list)
    delivery_concerns_summary: str = "No critical delivery concerns detected based on evidence."
    source_documents: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)


# ==========================================
# 3. Blocker and Action Item Models
# ==========================================

class BlockerItem(BaseModel):
    blocker_id: str
    title: str
    description: str
    status: str = "active"  # "active", "unresolved", "resolved"
    affected_activities: list[str] = Field(default_factory=list)
    assigned_owner: str = "Unassigned"
    supporting_evidence: list[SourceEvidence] = Field(default_factory=list)


class UnresolvedIssue(BaseModel):
    issue_id: str
    title: str
    status: str = "unresolved"
    evidence: list[SourceEvidence] = Field(default_factory=list)


class PendingDecision(BaseModel):
    decision_id: str
    description: str
    decision_maker: str = "Unknown"
    deadline: str = "Not specified"
    evidence: list[SourceEvidence] = Field(default_factory=list)


class DelayedActivity(BaseModel):
    activity_id: str
    description: str
    reason: str = "Unknown"
    evidence: list[SourceEvidence] = Field(default_factory=list)


class ActionItem(BaseModel):
    action_id: str
    description: str
    assigned_person: str = "Unassigned"
    deadline: str = "Not specified"
    priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
    current_status: Literal["Pending", "In progress", "Completed", "Unresolved"] = "Pending"
    related_blocker: str | None = None
    source_document: str = "Unknown"
    supporting_evidence: list[SourceEvidence] = Field(default_factory=list)


class BlockerAnalysisResult(BaseModel):
    blockers: list[BlockerItem] = Field(default_factory=list)
    unresolved_issues: list[UnresolvedIssue] = Field(default_factory=list)
    pending_decisions: list[PendingDecision] = Field(default_factory=list)
    delayed_activities: list[DelayedActivity] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    unassigned_action_items_count: int = 0
    dependencies_requiring_attention: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    source_documents: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)


# ==========================================
# 4. Multi-Agent Consolidated Report
# ==========================================

class ProjectIntelligenceReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    project_title: str = "Unknown"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sources_analyzed: list[str] = Field(default_factory=list)
    executive_summary: str = ""
    project_health: Literal["Healthy", "Needs Attention", "At Risk", "Critical"] = "Healthy"
    scope_and_deliverables: ScopeAnalysisResult
    risk_and_forecasting: RiskAnalysisResult
    blockers_and_actions: BlockerAnalysisResult
    key_recommendations: list[str] = Field(default_factory=list)
    partial_failures: list[str] = Field(default_factory=list)


# ==========================================
# 5. Agent API Request & Status Schemas
# ==========================================

class AgentAnalysisRequest(BaseModel):
    query: str | None = None
    document_id: str | None = None
    text: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)


class MultiAgentAnalysisRequest(BaseModel):
    query: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    text: str | None = None
    top_k: int = Field(default=15, ge=1, le=50)


class AgentStatusResponse(BaseModel):
    status: str
    available_agents: list[str]
    rag_ready: bool
    total_indexed_chunks: int
    details: dict[str, Any] = Field(default_factory=dict)
