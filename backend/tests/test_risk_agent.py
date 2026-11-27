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


def test_risk_agent_section_headings_not_classified_as_risks() -> None:
    text_with_headings = """
    1. Executive Delivery Summary
    The project is tracking multiple deliverables with key operational findings.

    2. Schedule and Delivery Risks
    Schedule delay: Security compliance review backlog is directly blocking the deployment of the Unified RBAC Security Gateway.

    Technical Bottlenecks:
    Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.

    3. Budget and Resource Constraints
    Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to unoptimized development cluster scaling.
    Resource constraint: The frontend engineering team is currently understaffed, creating a bandwidth bottleneck for dashboard widget completion.

    ## Delayed Activities
    Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.

    Milestone / Deliverable | Owner | Due Date | Status
    Milestone 1: Architectural Foundation | Alice Chen | 2026-08-30 | Completed
    """
    agent = RiskAgent()
    result = agent.analyze(text=text_with_headings, filename="headings_test.txt")

    extracted_titles = [r.title for r in result.risks]
    extracted_descriptions = [r.description for r in result.risks]

    # Verify invalid section headings are NOT extracted as risks
    invalid_headings = [
        "1. Executive Delivery Summary",
        "Executive Delivery Summary",
        "2. Schedule and Delivery Risks",
        "Schedule and Delivery Risks",
        "3. Budget and Resource Constraints",
        "Budget and Resource Constraints",
        "Technical Bottlenecks",
        "Technical Bottlenecks:",
        "## Delayed Activities",
        "Delayed Activities",
        "Milestone / Deliverable | Owner | Due Date | Status",
    ]
    for heading in invalid_headings:
        assert heading not in extracted_titles
        assert heading not in extracted_descriptions

    # Verify real risks under headings are correctly extracted
    categories = {r.category for r in result.risks}
    assert "Schedule" in categories
    assert "Bottleneck" in categories
    assert "Budget" in categories
    assert "Resource" in categories

    # Verify titles are complete and not abruptly cut off
    for title in extracted_titles:
        assert not title.endswith(" is d")
        assert not title.endswith(" is curren")
        assert not title.endswith(" exceeded bu")
        assert len(title) >= 10


def test_risk_agent_specific_mitigations_grounded_in_risk_types() -> None:
    test_cases = """
    Risk 1: Cloud infrastructure expenditure exceeded budget by 22% due to development cluster scaling.
    Risk 2: The frontend engineering team is currently understaffed, creating a critical bandwidth bottleneck.
    Risk 3: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange.
    Risk 4: High memory consumption in worker pods and cross-region latency spikes exceeding 1200ms.
    Risk 5: Milestone 2 target completion date of 2026-10-15 is at risk of slipping behind schedule.
    Risk 6: Integration testing has not started, although required before final deployment.
    """
    agent = RiskAgent()
    result = agent.analyze(text=test_cases, filename="mitigations_test.txt")

    assert len(result.risks) >= 5

    # Check budget mitigation
    budget_risk = next((r for r in result.risks if r.category == "Budget"), None)
    assert budget_risk is not None
    assert "cloud infrastructure" in budget_risk.suggested_mitigation.lower() or "cost monitoring" in budget_risk.suggested_mitigation.lower()

    # Check resource mitigation
    resource_risk = next((r for r in result.risks if r.category == "Resource"), None)
    assert resource_risk is not None
    assert "reallocate available engineers" in resource_risk.suggested_mitigation.lower() or "prioritize critical deliverables" in resource_risk.suggested_mitigation.lower()

    # Check dependency mitigation
    dep_risk = next((r for r in result.risks if r.category == "Dependency"), None)
    assert dep_risk is not None
    assert "secops" in dep_risk.suggested_mitigation.lower() or "approval deadline" in dep_risk.suggested_mitigation.lower()

    # Check bottleneck mitigation
    bot_risk = next((r for r in result.risks if r.category == "Bottleneck"), None)
    assert bot_risk is not None
    assert "worker memory" in bot_risk.suggested_mitigation.lower() or "network communication" in bot_risk.suggested_mitigation.lower()

    # Check schedule mitigation
    sched_risk = next((r for r in result.risks if r.category == "Schedule"), None)
    assert sched_risk is not None
    assert "rebaseline" in sched_risk.suggested_mitigation.lower() or "critical-path" in sched_risk.suggested_mitigation.lower()


def test_risk_agent_summary_counts_and_formatting() -> None:
    text = """
    Milestone 1 is delayed by 2 weeks due to critical defects.
    Cloud spend exceeded budget by 15% due to unoptimized cluster scaling.
    Understaffed engineering team with a shortage of senior backend developers.
    Blocked by SecOps approval for external OAuth keys.
    High memory consumption in worker pods causing intermittent latency spikes.
    Integration testing has not started before final deployment.
    """
    agent = RiskAgent()
    result = agent.analyze(text=text, filename="summary_test.txt")

    assert len(result.risks) == 6
    summary = result.delivery_concerns_summary

    # Total risk count in summary
    assert "6 risk findings" in summary

    # Category counts match
    assert f"{result.schedule_risks_count} schedule" in summary
    assert f"{result.budget_risks_count} budget" in summary

    # Overall risk level mentioned
    assert result.overall_risk_level in ["Critical", "High"]
    assert f"Overall delivery risk is rated {result.overall_risk_level}" in summary

    # Key issues present
    assert "Key issues:" in summary


def test_risk_agent_document_formats_compatibility() -> None:
    from pathlib import Path
    from app.services.document_ingestion import DocumentIngestionService

    svc = DocumentIngestionService()
    agent = RiskAgent()

    # 1. Charter (clean baseline - should have 0 risks)
    charter_path = Path("backend/sample_data/project_charter.pdf")
    if charter_path.exists():
        doc = svc.ingest(charter_path.name, charter_path.read_bytes())
        res = agent.analyze(text=doc.text, filename=charter_path.name)
        assert len(res.risks) == 0
        assert res.overall_risk_level == "Low"

    # 2. Progress Report (DOCX - contains real risks, no heading risks)
    docx_path = Path("backend/sample_data/progress_report.docx")
    if docx_path.exists():
        doc = svc.ingest(docx_path.name, docx_path.read_bytes())
        res = agent.analyze(text=doc.text, filename=docx_path.name)
        assert len(res.risks) >= 5
        titles = [r.title for r in res.risks]
        assert not any("Schedule and Delivery Risks" in t for t in titles)
        assert not any("Budget and Resource Constraints" in t for t in titles)
        assert not any("Executive Delivery Summary" in t for t in titles)

    # 3. Meeting Notes (TXT - contains blockers and delays, no markdown heading risks)
    txt_path = Path("backend/sample_data/meeting_notes.txt")
    if txt_path.exists():
        doc = svc.ingest(txt_path.name, txt_path.read_bytes())
        res = agent.analyze(text=doc.text, filename=txt_path.name)
        assert len(res.risks) >= 5
        titles = [r.title for r in res.risks]
        assert not any("## Delayed Activities" in t for t in titles)
        assert not any("## Current Blockers" in t for t in titles)


def test_risk_agent_category_counts_consistency_and_breakdown() -> None:
    """Verify that category counts strictly match the individual risk findings array."""
    progress_text = """
    Enterprise Cloud Analytics Platform - Monthly Progress Report
    Reporting Period: Q3 2026
    Prepared by: Project Delivery Management

    1. Executive Project Summary
    The Enterprise Cloud Analytics Platform (ECAP) aims to build a modern telemetry and analytics infrastructure. Overall progress has slowed due to security review backlogs and technical dependencies.

    2. Schedule and Delivery Risks
    - Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.
    - The target completion date of 2026-10-15 is at risk of slipping into November 2026.
    - Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
    - Dependency gap: The data warehouse sync pipeline depends on the completion of the Kafka brokers and schema validation module.

    3. Budget and Resource Constraints
    - Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.
    - Resource constraint: The frontend engineering team is currently understaffed, creating a bandwidth bottleneck for dashboard widget completion.
    - Shortage of senior site reliability engineers has contributed to deployment pipeline instability.

    4. Technical Bottlenecks
    - Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.
    """
    agent = RiskAgent()
    result = agent.analyze(text=progress_text, filename="progress_report.docx")

    # Verify total risks count is exactly 8
    assert len(result.risks) == 8

    # Category counts calculated from findings
    cat_counts = {r.category: sum(1 for x in result.risks if x.category == r.category) for r in result.risks}
    assert cat_counts.get("Schedule", 0) == 3
    assert cat_counts.get("Budget", 0) == 1
    assert cat_counts.get("Dependency", 0) == 1
    assert cat_counts.get("Resource", 0) == 2
    assert cat_counts.get("Bottleneck", 0) == 1

    # Verify model fields agree with category counts
    assert result.schedule_risks_count == 3
    assert result.budget_risks_count == 1
    assert result.dependency_risks_count == 1
    assert result.resource_risks_count == 2
    assert result.bottleneck_risks_count == 1
    assert sum([
        result.schedule_risks_count,
        result.budget_risks_count,
        result.dependency_risks_count,
        result.resource_risks_count,
        result.bottleneck_risks_count,
    ]) == len(result.risks)

    # Verify summary paragraph matches
    assert "8 risk findings: 3 schedule, 1 budget, 1 dependency, 2 resource, 1 bottleneck" in result.delivery_concerns_summary


def test_risk_agent_delivery_forecast_accuracy_and_deduplication() -> None:
    """Verify delivery forecasts preserve original milestone names, avoid generic placeholders, and deduplicate."""
    progress_text = """
    2. Schedule and Delivery Risks
    - Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.
    - The target completion date of 2026-10-15 is at risk of slipping into November 2026.
    - Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
    """
    agent = RiskAgent()
    result = agent.analyze(text=progress_text, filename="progress_report.docx")

    # Verify no generic "Project Milestone" in forecast cards
    forecast_names = [f.milestone_name for f in result.delivery_forecasts]
    assert not any("Project Milestone" in name for name in forecast_names)
    assert not any("Project Scheduled Milestone" in name for name in forecast_names)

    # Verify original milestone name preserved and deduplicated into single card
    m2_forecasts = [f for f in result.delivery_forecasts if "Milestone 2" in f.milestone_name]
    assert len(m2_forecasts) == 1, "Milestone 2 should have exactly 1 consolidated forecast card, not duplicates"

    m2 = m2_forecasts[0]
    assert "Milestone 2 (Security Sign-off & Warehouse Integration)" in m2.milestone_name
    assert m2.actual_deadline == "2026-10-15"
    assert m2.forecasted_date == "November 2026"
    assert "Future predicted delay" in m2.predicted_delay_reason or "delayed" in m2.predicted_delay_reason

    # Verify OAuth Gateway forecast has actual name and clearly indicates missing date
    oauth_forecasts = [f for f in result.delivery_forecasts if "OAuth Gateway" in f.milestone_name]
    assert len(oauth_forecasts) == 1
    oauth = oauth_forecasts[0]
    assert oauth.actual_deadline == "Date not specified"


def test_risk_agent_date_aware_interpretation() -> None:
    """Verify that current date distinguishes overdue deadlines from future predicted delays."""
    from app.agents.risk_agent import interpret_schedule_risk

    # 1. Past deadline relative to current date -> Overdue
    status_overdue, sev_overdue, reason_overdue = interpret_schedule_risk(
        "Milestone 1 is delayed and incomplete.",
        deadline="2026-09-15",
        current_date="2026-11-20",
    )
    assert status_overdue == "Overdue milestone"
    assert sev_overdue == "Critical"
    assert "2026-09-15" in reason_overdue

    # 2. Future deadline relative to current date with predicted slip -> Future predicted delay
    status_future, sev_future, reason_future = interpret_schedule_risk(
        "Target completion date of 2026-12-15 is at risk of slipping into January 2027.",
        deadline="2026-12-15",
        current_date="2026-11-20",
        forecasted_date="January 2027",
    )
    assert status_future == "Future predicted delay"
    assert sev_future == "High"
    assert "January 2027" in reason_future

    # 3. Historical delay recovered -> Historical delay
    status_hist, sev_hist, _ = interpret_schedule_risk(
        "Database migration was delayed by 2 weeks but issue was resolved.",
        deadline="2026-08-01",
        current_date="2026-11-20",
    )
    assert status_hist == "Historical delay"


def test_risk_agent_structured_csv_row_parsing() -> None:
    """Validate that CSV task matrix rows are parsed into structured clean titles instead of raw commas."""
    csv_text = """
Task ID,Task Name,Deliverable,Owner,Priority,Status,Deadline,Dependencies,Notes
TSK-101,Deploy Kafka Ingestion Brokers,Cloud Telemetry Ingestion Pipeline,Alice Chen,High,Completed,2026-08-10,None,Deployed to Kubernetes cluster successfully
TSK-102,Configure RBAC OAuth Gateway,Unified RBAC Security Gateway,Bob Martinez,Critical,In progress,2026-09-28,SecOps Approval,Blocked by security compliance review
TSK-104,Execute Staging Database Migration,Automated Data Warehouse Sync,Unassigned,High,Pending,2026-09-30,Kafka Pipeline,Migration tests failing on staging
TSK-105,Cloud Cost Containment Audit,Budget Optimization,David Kim,High,Pending,2026-10-05,None,Cloud spend exceeded budget by 22%
"""
    agent = RiskAgent()
    res = agent.analyze(text=csv_text, filename="task_matrix.csv")

    # Completed task TSK-101 should not be classified as a risk
    assert not any("TSK-101" in r.description and "Completed" in r.description for r in res.risks)

    # Active risk tasks should be extracted with clean titles
    assert len(res.risks) >= 3
    for r in res.risks:
        # Title must NEVER be a raw comma-separated CSV row
        assert r.title.count(",") < 3, f"Title should not be raw CSV row: {r.title}"
        assert not r.title.startswith("TSK-102,Configure"), f"Raw CSV in title: {r.title}"

    # Verify category and severity assignment
    oauth_risk = next(r for r in res.risks if "OAuth" in r.title or "RBAC" in r.title)
    assert oauth_risk.severity == "Critical"
    assert oauth_risk.category in ["Dependency", "Schedule"]
    assert any(k in oauth_risk.title for k in ["Blocked", "Configure", "OAuth", "RBAC", "SecOps"])

    budget_risk = next(r for r in res.risks if "Cost" in r.title or "Budget" in r.title or "spend" in r.title.lower())
    assert budget_risk.category == "Budget"
    assert budget_risk.severity in ["High", "Critical"]


def test_risk_agent_semantic_deduplication_cross_document() -> None:
    """Validate semantic deduplication of overlapping risk findings across multiple documents."""
    overlapping_text = """
# Sprint 14 Meeting Notes
- Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
- Blocker 2: Database migration scripts failing on staging cluster due to schema mismatch with legacy tables.
- Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.

Enterprise Progress Report Q3
- Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
- Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.

Task Matrix CSV:
TSK-102,Configure RBAC OAuth Gateway,Unified RBAC Security Gateway,Bob Martinez,Critical,In progress,2026-09-28,SecOps Approval,Blocked by security compliance review
TSK-104,Execute Staging Database Migration,Automated Data Warehouse Sync,Unassigned,High,Pending,2026-09-30,Kafka Pipeline,Migration tests failing on staging
TSK-105,Cloud Cost Containment Audit,Budget Optimization,David Kim,High,Pending,2026-10-05,None,Cloud spend exceeded budget by 22%
"""
    agent = RiskAgent()
    res = agent.analyze(text=overlapping_text, filename="unified_project_corpus.txt")

    # 1. Exactly ONE canonical risk for OAuth SecOps approval
    secops_risks = [r for r in res.risks if any(k in f"{r.title} {r.description}".lower() for k in ["secops", "oauth gateway", "rbac oauth"])]
    assert len(secops_risks) == 1, f"Expected 1 deduplicated SecOps risk, found {len(secops_risks)}"
    canonical_secops = secops_risks[0]
    assert canonical_secops.severity == "Critical"  # Highest justified severity
    assert len(canonical_secops.supporting_evidence) >= 2  # Evidence merged across multiple mentions

    # 2. Exactly ONE canonical risk for Database Migration failure/delay
    migration_risks = [r for r in res.risks if "migration" in f"{r.title} {r.description}".lower()]
    assert len(migration_risks) == 1, f"Expected 1 deduplicated Migration risk, found {len(migration_risks)}"
    assert migration_risks[0].severity in ["Critical", "High"]

    # 3. Exactly ONE canonical risk for Cloud Budget overrun
    budget_risks = [r for r in res.risks if "budget" in r.category or "budget" in f"{r.title} {r.description}".lower()]
    assert len(budget_risks) == 1, f"Expected 1 deduplicated Budget risk, found {len(budget_risks)}"

    # 4. Strict consistency between category counts and total findings
    assert sum(res.category_counts.values()) == len(res.risks)


def test_risk_agent_compound_bottleneck_splitting() -> None:
    """Validate that technical bottleneck findings accurately capture memory and latency issues."""
    compound_text = """
    Technical Bottlenecks:
    - Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.
    """
    agent = RiskAgent()
    res = agent.analyze(text=compound_text, filename="progress.docx")

    assert len(res.risks) >= 1
    assert any("memory" in r.description.lower() for r in res.risks)
    assert any("latency" in r.description.lower() for r in res.risks)
    assert res.category_counts.get("Bottleneck", 0) >= 1



