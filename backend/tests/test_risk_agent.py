"""Tests for Risk Detection and Delivery Forecasting Agent."""

import pytest

from app.agents.risk_agent import RiskAgent
from app.models.agent_models import (
    MilestoneItem,
    RiskAnalysisResult,
    ScopeAnalysisResult,
)


@pytest.fixture
def sample_risk_text() -> str:
    return """
    Sprint 12 Progress Report:
    Milestone 2 is delayed by 3 weeks because integration testing revealed critical failures.
    The release is behind schedule and we cannot meet the scheduled October 15 launch date.

    Dependencies:
    - Blocked by SecOps approval for external API OAuth keys.
    - Upstream service authentication token exchange is failing.

    Budget:
    - Cloud infrastructure expenditure exceeded budget by 24% due to unoptimized cluster instances.

    Resource Constraints:
    - Team is understaffed with a critical shortage of senior database engineers.

    Bottlenecks:
    - Failing tests in staging pipeline are causing a major delivery bottleneck.
    """


def test_risk_agent_identifies_schedule_risks(sample_risk_text: str) -> None:
    agent = RiskAgent()
    result = agent.analyze(text=sample_risk_text, filename="progress.txt")

    assert isinstance(result, RiskAnalysisResult)
    assert result.schedule_risks_count >= 1
    schedule_risks = [r for r in result.risks if r.category == "Schedule"]
    assert len(schedule_risks) >= 1
    assert any("delay" in r.description.lower() for r in schedule_risks)


def test_risk_agent_classifies_severity(sample_risk_text: str) -> None:
    agent = RiskAgent()
    result = agent.analyze(text=sample_risk_text, filename="progress.txt")

    severities = [r.severity for r in result.risks]
    assert "Critical" in severities or "High" in severities
    assert result.overall_risk_level in ["Critical", "High"]


def test_risk_agent_identifies_dependency_gaps(sample_risk_text: str) -> None:
    agent = RiskAgent()
    result = agent.analyze(text=sample_risk_text, filename="progress.txt")

    assert len(result.dependency_gaps) >= 1
    assert any("secops" in gap.dependency.lower() or "blocked" in gap.dependency.lower() for gap in result.dependency_gaps)


def test_risk_agent_detects_budget_risks(sample_risk_text: str) -> None:
    agent = RiskAgent()
    result = agent.analyze(text=sample_risk_text, filename="progress.txt")

    assert result.budget_risks_count >= 1
    budget_risks = [r for r in result.risks if r.category == "Budget"]
    assert len(budget_risks) >= 1
    assert any("exceeded budget" in r.description.lower() for r in budget_risks)


def test_risk_agent_delivery_forecasting_with_scope_context(sample_risk_text: str) -> None:
    agent = RiskAgent()
    scope_ctx = ScopeAnalysisResult(
        project_title="Cloud Analytics",
        milestones=[
            MilestoneItem(
                milestone_id="MLS-002",
                name="Milestone 2",
                target_date="2026-10-15",
                status="pending",
            )
        ],
    )
    result = agent.analyze(
        text=sample_risk_text,
        filename="progress.txt",
        scope_context=scope_ctx,
    )

    assert len(result.delayed_milestones_forecast) >= 1
    forecast = result.delayed_milestones_forecast[0]
    assert "Milestone 2" in forecast.milestone_name
    assert forecast.actual_deadline == "2026-10-15"
    assert "delay" in forecast.predicted_delay_reason.lower()
    assert len(forecast.supporting_evidence) >= 1


def test_risk_agent_handles_low_risk_or_empty_text() -> None:
    agent = RiskAgent()
    safe_text = "All project deliverables are on track. Milestones are completed on schedule with no blockers."
    result = agent.analyze(text=safe_text, filename="safe.txt")

    assert result.overall_risk_level == "Low"
    assert result.schedule_risks_count == 0
    assert result.budget_risks_count == 0


def test_risk_agent_handles_empty_input() -> None:
    agent = RiskAgent()
    result = agent.analyze(text="", filename="empty.txt")

    assert result.overall_risk_level == "Low"
    assert result.risks == []
    assert result.confidence_score == 0.0


USER_TEST_DOCUMENT = """Project Title: Enterprise Cloud Analytics Platform.

Project deadline: 2026-12-15.

Current date for this sample: 2026-11-22.

Risk 1: The Cloud Telemetry Pipeline was scheduled for completion on 2026-11-20, but it is still incomplete.

Risk 2: The Unified RBAC Gateway implementation cannot begin until the Cloud Telemetry Pipeline API is ready.

Risk 3: Only one backend developer is available to work on the RBAC Gateway and dashboard integration.

Risk 4: The project budget has only 10 percent remaining, while cloud infrastructure costs are increasing.

Risk 5: Integration testing has not started, although it is required before final deployment.

The project manager is concerned that these issues may delay the 2026-12-15 delivery deadline.

Mitigation: Assign an additional backend developer, prioritize the telemetry pipeline, review cloud infrastructure spending, and begin integration test planning immediately."""


def test_risk_agent_user_test_document() -> None:
    agent = RiskAgent()
    result = agent.analyze(text=USER_TEST_DOCUMENT, filename="analytics_platform_risks.txt")

    assert isinstance(result, RiskAnalysisResult)

    # 1. Assert exactly five distinct findings extracted
    assert len(result.risks) == 5
    risk_titles = [r.title for r in result.risks]
    assert "Cloud Telemetry Pipeline overdue" in risk_titles
    assert "Unified RBAC Gateway dependency on the telemetry API" in risk_titles
    assert "Insufficient backend developer availability" in risk_titles
    assert "Budget constraint and increasing infrastructure costs" in risk_titles
    assert "Integration testing not started" in risk_titles

    # 2. Assert unique risk IDs
    risk_ids = [r.risk_id for r in result.risks]
    assert len(set(risk_ids)) == 5
    assert set(risk_ids) == {"RSK-001", "RSK-002", "RSK-003", "RSK-004", "RSK-005"}

    # 3. Assert categories
    categories = {r.category for r in result.risks}
    assert {"Schedule", "Dependency", "Resource", "Budget", "Delivery"}.issubset(categories)

    # 4. Assert dependency gap
    assert len(result.dependency_gaps) >= 1
    dep_gap = result.dependency_gaps[0]
    assert "Telemetry" in dep_gap.dependency and "RBAC" in dep_gap.dependency
    assert dep_gap.status == "Blocked"
    assert "Cloud Telemetry Pipeline API is ready" in dep_gap.impact

    # 5. Assert resource constraint
    assert len(result.resource_constraints) >= 1
    assert any("one backend developer" in rc.lower() for rc in result.resource_constraints)

    # 6. Assert budget risk
    assert result.budget_risks_count >= 1
    budget_risks = [r for r in result.risks if r.category == "Budget"]
    assert len(budget_risks) == 1
    assert "10 percent" in budget_risks[0].description

    # 7. Assert delivery challenge
    assert len(result.delivery_challenges) >= 1
    assert any("integration testing has not started" in dc.lower() for dc in result.delivery_challenges)

    # 8. Assert delivery forecasting: overdue deadline 2026-11-20 vs upcoming deadline 2026-12-15
    assert len(result.delayed_milestones_forecast) >= 2
    # Overdue deliverable
    overdue_forecast = next((f for f in result.delayed_milestones_forecast if f.actual_deadline == "2026-11-20"), None)
    assert overdue_forecast is not None
    assert "Cloud Telemetry Pipeline" in overdue_forecast.milestone_name
    assert overdue_forecast.delay_severity == "Critical"
    assert "2026-11-20" in overdue_forecast.predicted_delay_reason

    # Upcoming project deadline impact
    upcoming_forecast = next((f for f in result.delayed_milestones_forecast if f.actual_deadline == "2026-12-15"), None)
    assert upcoming_forecast is not None
    assert upcoming_forecast.delay_severity == "High"
    assert "2026-12-15" in upcoming_forecast.predicted_delay_reason

    # Never invent "Upcoming Project Milestone"
    assert not any("Upcoming Project Milestone" in f.milestone_name for f in result.delayed_milestones_forecast)

    # 9. Assert overall risk level is Critical
    assert result.overall_risk_level == "Critical"

    # 10. Assert delivery concerns summary category count consistency
    assert "5 risk findings: 1 schedule, 1 budget, 1 dependency, 1 resource, 1 delivery" in result.delivery_concerns_summary

    # 11. Assert potential bottlenecks populated with resource bottleneck
    assert len(result.potential_bottlenecks) >= 1
    assert any("backend developer" in pb.lower() and "rbac" in pb.lower() for pb in result.potential_bottlenecks)

    # 12. Assert concise supporting evidence snippets
    for r in result.risks:
        assert len(r.supporting_evidence) >= 1
        snippet = r.supporting_evidence[0].snippet
        assert len(snippet) < 250
        assert "Mitigation:" not in snippet  # Snippet is focused on risk, not entire doc


def test_risk_agent_single_line_swagger_payload() -> None:
    agent = RiskAgent()
    single_line = " ".join(USER_TEST_DOCUMENT.split())
    result = agent.analyze(text=single_line, filename="swagger_payload.txt")

    assert len(result.risks) == 5
    assert result.overall_risk_level == "Critical"
    assert result.schedule_risks_count == 1
    assert result.budget_risks_count == 1
    assert len(result.dependency_gaps) >= 1
    assert len(result.delayed_milestones_forecast) >= 2
    assert "5 risk findings: 1 schedule, 1 budget, 1 dependency, 1 resource, 1 delivery" in result.delivery_concerns_summary
    assert len(result.potential_bottlenecks) >= 1
    assert any("backend developer" in pb.lower() for pb in result.potential_bottlenecks)

    # Verify no risk description or evidence absorbed the entire document
    for r in result.risks:
        assert len(r.description) < 300
        assert len(r.supporting_evidence[0].snippet) < 250

