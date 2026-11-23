"""Tests for AI Agent API Endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"


def test_agent_status_endpoint() -> None:
    response = client.get("/api/agents/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert len(data["available_agents"]) == 3
    assert "Scope and Deliverable Extraction Agent" in data["available_agents"]


def test_analyze_scope_endpoint() -> None:
    payload = {
        "text": """
        Project Title: Cloud Intelligence Platform
        Objectives:
        - Modernize cloud reporting pipelines.
        Deliverables:
        - Deliverable 1: Reporting Dashboard (Owner: Carol Vance, Deadline: 2026-11-20, Status: Pending)
        Milestones:
        - Milestone 1: Core Service Alpha - Target Date: 2026-08-30 (Owner: Alice Chen)
        """
    }
    response = client.post("/api/agents/analyze-scope", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Cloud Intelligence Platform" in data["project_title"]
    assert len(data["expected_deliverables"]) == 1
    assert data["expected_deliverables"][0]["owner"] == "Carol Vance"
    assert len(data["milestones"]) == 1
    assert data["milestones"][0]["target_date"] == "2026-08-30"


def test_detect_risks_endpoint() -> None:
    payload = {
        "text": """
        Milestone 2 is delayed by 3 weeks due to failing integration tests on staging.
        Cloud spend exceeded budget by 22%.
        Blocked by SecOps compliance review.
        """
    }
    response = client.post("/api/agents/detect-risks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk_level"] in ["Critical", "High", "Medium"]
    assert data["schedule_risks_count"] >= 1
    assert data["budget_risks_count"] >= 1
    assert len(data["risks"]) >= 2


def test_detect_risks_endpoint_user_test_document() -> None:
    payload = {
        "text": """Project Title: Enterprise Cloud Analytics Platform.
Project deadline: 2026-12-15.
Current date for this sample: 2026-11-22.
Risk 1: The Cloud Telemetry Pipeline was scheduled for completion on 2026-11-20, but it is still incomplete.
Risk 2: The Unified RBAC Gateway implementation cannot begin until the Cloud Telemetry Pipeline API is ready.
Risk 3: Only one backend developer is available to work on the RBAC Gateway and dashboard integration.
Risk 4: The project budget has only 10 percent remaining, while cloud infrastructure costs are increasing.
Risk 5: Integration testing has not started, although it is required before final deployment.
The project manager is concerned that these issues may delay the 2026-12-15 delivery deadline.
Mitigation: Assign an additional backend developer, prioritize the telemetry pipeline, review cloud infrastructure spending, and begin integration test planning immediately."""
    }
    response = client.post("/api/agents/detect-risks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["overall_risk_level"] == "Critical"
    assert len(data["risks"]) == 5
    categories = {r["category"] for r in data["risks"]}
    assert {"Schedule", "Dependency", "Resource", "Budget", "Delivery"}.issubset(categories)
    assert len(data["dependency_gaps"]) >= 1
    assert len(data["resource_constraints"]) >= 1
    assert data["budget_risks_count"] >= 1
    assert len(data["delivery_challenges"]) >= 1
    assert len(data["delayed_milestones_forecast"]) >= 2
    # Verify overdue milestone identified
    assert any(f["actual_deadline"] == "2026-11-20" and f["delay_severity"] == "Critical" for f in data["delayed_milestones_forecast"])
    # Verify upcoming deadline schedule impact identified
    assert any(f["actual_deadline"] == "2026-12-15" and f["delay_severity"] == "High" for f in data["delayed_milestones_forecast"])
    # Verify reporting consistency improvements
    assert "5 risk findings: 1 schedule, 1 budget, 1 dependency, 1 resource, 1 delivery" in data["delivery_concerns_summary"]
    assert len(data["potential_bottlenecks"]) >= 1
    assert any("backend developer" in pb.lower() for pb in data["potential_bottlenecks"])



def test_identify_blockers_endpoint() -> None:
    payload = {
        "text": """
        Current Blockers:
        - Blocker 1: Ingestion pipeline blocked by SecOps approval (Owner: Bob Martinez).
        Action Items:
        - Action Item 1: Bob Martinez to submit SecOps exception ticket by 2026-09-20 (Priority: Critical)
        - Clean up old test data (Priority: Low)
        """
    }
    response = client.post("/api/agents/identify-blockers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["blockers"]) >= 1
    assert len(data["action_items"]) >= 2
    assert data["unassigned_action_items_count"] >= 1


def test_identify_blockers_endpoint_user_test_input() -> None:
    payload = {
        "text": """Project: Enterprise Cloud Analytics Platform.
Meeting Date: 2026-11-22.
The Cloud Telemetry Pipeline API is delayed because authentication testing is incomplete.
Alice Chen must complete authentication testing by 2026-11-24.
Bob Martinez cannot start RBAC integration until the telemetry API is available.
The team has not decided whether to use Redis or RabbitMQ for event processing.
Carol Vance must prepare dashboard integration tests by 2026-11-25.
David Kim reported that data warehouse credentials are still pending from the infrastructure team.
The project manager must schedule a dependency review meeting by 2026-11-23."""
    }
    response = client.post("/api/agents/identify-blockers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["blockers"]) == 3
    assert len(data["unresolved_issues"]) == 2
    assert len(data["pending_decisions"]) == 1
    assert len(data["delayed_activities"]) == 1
    assert len(data["action_items"]) == 3
    assert len(data["dependencies_requiring_attention"]) >= 1
    assert len(data["recommended_next_steps"]) == 5
    # Verify delayed activity does not contain the whole document
    assert len(data["delayed_activities"][0]["description"]) < 150



def test_analyze_project_endpoint() -> None:
    payload = {
        "text": """
        Project Title: Unified Enterprise Platform
        Objectives:
        - Consolidate legacy operations.
        Milestones:
        - Milestone 1: Beta Release - Target Date: 2026-10-15 (Owner: Alice Chen)
        Current Blockers:
        - Blocked by database migration scripts failing on staging cluster.
        Action Items:
        - Alice Chen to fix database migration by 2026-10-01 (Priority: Critical)
        """
    }
    response = client.post("/api/agents/analyze-project", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_title"] == "Unified Enterprise Platform"
    assert data["project_health"] in ["Critical", "At Risk", "Needs Attention"]
    assert len(data["executive_summary"]) > 0
    assert len(data["key_recommendations"]) >= 1
    assert len(data["scope_and_deliverables"]["milestones"]) == 1
    assert len(data["blockers_and_actions"]["action_items"]) == 1


def test_api_with_sample_proposal_file() -> None:
    proposal_path = SAMPLE_DIR / "project_proposal.txt"
    if proposal_path.exists():
        text = proposal_path.read_text(encoding="utf-8")
        response = client.post("/api/agents/analyze-scope", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        assert "Enterprise Cloud Analytics Platform" in data["project_title"]
        assert len(data["expected_deliverables"]) >= 3
        assert len(data["milestones"]) >= 3
        assert len(data["assigned_owners"]) >= 3


def test_api_with_sample_meeting_notes_file() -> None:
    notes_path = SAMPLE_DIR / "meeting_notes.txt"
    if notes_path.exists():
        text = notes_path.read_text(encoding="utf-8")
        response = client.post("/api/agents/identify-blockers", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        assert len(data["blockers"]) >= 2
        assert len(data["action_items"]) >= 4
        assert len(data["pending_decisions"]) >= 2
        assert data["unassigned_action_items_count"] >= 1


def test_analyze_scope_endpoint_with_swagger_test_input() -> None:
    payload = {
        "text": """
        Project Title: Enterprise Cloud Analytics Platform.

        Objective: Build a cloud-based analytics platform for enterprise users.

        Deliverables: Cloud Telemetry Pipeline, Unified RBAC Gateway, Real-Time Dashboard, and Data Warehouse Sync.

        Milestone 1: Complete cloud telemetry pipeline.

        Milestone 2: Implement RBAC gateway.

        Milestone 3: Deploy dashboard and data warehouse integration.

        Responsibilities: Alice Chen owns the telemetry pipeline, Bob Martinez owns the RBAC gateway, Carol Vance owns the dashboard, and David Kim owns data warehouse integration.

        Pending deliverable: Complete integration testing.
        """
    }
    response = client.post("/api/agents/analyze-scope", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["project_title"] == "Enterprise Cloud Analytics Platform"
    assert len(data["expected_deliverables"]) == 4
    deliv_names = [d["name"] for d in data["expected_deliverables"]]
    assert deliv_names == [
        "Cloud Telemetry Pipeline",
        "Unified RBAC Gateway",
        "Real-Time Dashboard",
        "Data Warehouse Sync",
    ]
    assert "Real" not in data["assigned_owners"]
    assert sorted(data["assigned_owners"]) == ["Alice Chen", "Bob Martinez", "Carol Vance", "David Kim"]
    assert len(data["team_responsibilities"]) == 4
    assert data["pending_deliverables"] == ["Complete integration testing"]
    assert len(data["milestones"]) == 3
    assert data["expected_deliverables"][3]["name"] == "Data Warehouse Sync"
    assert data["expected_deliverables"][3]["owner"] == "David Kim"


def test_analyze_scope_endpoint_with_single_line_input() -> None:
    single_line = (
        "Project Title: Enterprise Cloud Analytics Platform. "
        "Objective: Build a cloud-based analytics platform for enterprise users. "
        "Deliverables: Cloud Telemetry Pipeline, Unified RBAC Gateway, Real-Time Dashboard, and Data Warehouse Sync. "
        "Milestone 1: Complete cloud telemetry pipeline. "
        "Milestone 2: Implement RBAC gateway. "
        "Milestone 3: Deploy dashboard and data warehouse integration. "
        "Responsibilities: Alice Chen owns the telemetry pipeline, Bob Martinez owns the RBAC gateway, "
        "Carol Vance owns the dashboard, and David Kim owns data warehouse integration. "
        "Pending deliverable: Complete integration testing."
    )
    response = client.post("/api/agents/analyze-scope", json={"text": single_line})
    assert response.status_code == 200
    data = response.json()

    assert data["project_title"] == "Enterprise Cloud Analytics Platform"
    assert len(data["expected_deliverables"]) == 4
    deliv_names = [d["name"] for d in data["expected_deliverables"]]
    assert deliv_names == [
        "Cloud Telemetry Pipeline",
        "Unified RBAC Gateway",
        "Real-Time Dashboard",
        "Data Warehouse Sync",
    ]
    assert data["expected_deliverables"][3]["name"] == "Data Warehouse Sync"
    assert data["expected_deliverables"][3]["owner"] == "David Kim"
    assert "data warehouse integration" not in deliv_names
    assert data["pending_deliverables"] == ["Complete integration testing"]
    assert len(data["milestones"]) == 3
    assert sorted(data["assigned_owners"]) == ["Alice Chen", "Bob Martinez", "Carol Vance", "David Kim"]
