"""Tests for Scope and Deliverable Extraction Agent."""

import pytest

from app.agents.scope_agent import ScopeAgent
from app.models.agent_models import ScopeAnalysisResult


@pytest.fixture
def sample_scope_text() -> str:
    return """
    Project Title: Cloud Data Migration Engine

    Objectives:
    - Migrate on-premise relational databases to cloud data warehouses.
    - Provide zero-downtime replication pipelines.

    Goals:
    - Achieve 99.99% data consistency during synchronization.

    Scope:
    In-Scope:
    - PostgreSQL and MySQL cloud connectors.
    - Automated schema mapping.
    Out-of-Scope:
    - Mainframe data conversion.

    Timeline:
    - Start Date: 2026-04-01
    - End Date: 2026-11-30

    Deliverables:
    - Deliverable 1: Ingestion Gateway (Owner: Alice Chen, Deadline: 2026-06-15, Status: In progress)
    - Deliverable 2: Cloud Sync Pipeline (Owner: Bob Martinez, Deadline: 2026-09-01, Status: Pending)

    Milestones:
    - Milestone 1: Ingestion Beta - Target Date: 2026-06-30 (Owner: Alice Chen)
    - Milestone 2: Cloud Warehouse Production - Target Date: 2026-11-15 (Owner: Bob Martinez)

    Deadlines:
    - Schema Validation Deadline is 2026-05-20 (Owner: Alice Chen)

    Team Responsibilities:
    - Alice Chen is responsible for schema validation and database connectors.
    - Bob Martinez is responsible for replication pipelines and failover automation.
    """


@pytest.fixture
def unstructured_scope_text() -> str:
    return (
        "The Enterprise Cloud Analytics Platform (ECAP) initiative aims to modernize "
        "enterprise telemetry data pipeline and achieve sub-second query latency for "
        "executive operational metrics. The project start date is 2026-06-01 and target "
        "end date is 2026-12-15. Scope covers Kubernetes infrastructure, Snowflake integration, "
        "OAuth2 RBAC, and real-time dashboard, while mainframe support and mobile apps are out of scope. "
        "Deliverables to be produced are Cloud Telemetry Pipeline, Unified RBAC Gateway, "
        "Real-Time Dashboard, and Data Warehouse Sync. Milestones are Milestone 1: Architectural Foundation "
        "due 2026-08-30, Milestone 2: Security Sign-off due 2026-10-15, and Milestone 3: Production Rollout "
        "due 2026-12-10. Team responsibilities: Alice Chen – Cloud Telemetry Pipeline, Bob Martinez – "
        "Unified RBAC Gateway, Carol Vance – Real-Time Dashboard, David Kim – Data Warehouse Sync."
    )


def test_scope_agent_extracts_title_and_objectives(sample_scope_text: str) -> None:
    agent = ScopeAgent()
    result = agent.analyze(text=sample_scope_text, filename="proposal.txt")

    assert isinstance(result, ScopeAnalysisResult)
    assert "Cloud Data Migration Engine" in result.project_title
    assert len(result.objectives) >= 1
    assert any("Migrate on-premise" in obj for obj in result.objectives)
    assert any("99.99%" in g for g in result.goals)


def test_scope_agent_extracts_in_and_out_of_scope(sample_scope_text: str) -> None:
    agent = ScopeAgent()
    result = agent.analyze(text=sample_scope_text, filename="proposal.txt")

    assert len(result.in_scope) >= 1
    assert any("PostgreSQL" in s for s in result.in_scope)
    assert len(result.out_of_scope) >= 1
    assert any("Mainframe" in s for s in result.out_of_scope)


def test_scope_agent_extracts_dates_and_deadlines(sample_scope_text: str) -> None:
    agent = ScopeAgent()
    result = agent.analyze(text=sample_scope_text, filename="proposal.txt")

    assert result.start_date == "2026-04-01"
    assert result.end_date == "2026-11-30"
    assert len(result.important_deadlines) >= 1
    assert any(d.date == "2026-05-20" for d in result.important_deadlines)


def test_scope_agent_extracts_deliverables_and_milestones(sample_scope_text: str) -> None:
    agent = ScopeAgent()
    result = agent.analyze(text=sample_scope_text, filename="proposal.txt")

    assert len(result.expected_deliverables) >= 2
    deliv_names = [d.name for d in result.expected_deliverables]
    assert any("Ingestion Gateway" in n for n in deliv_names)
    assert any("Cloud Sync Pipeline" in n for n in deliv_names)

    # Check owners
    assert any(d.owner == "Alice Chen" for d in result.expected_deliverables)
    assert any(d.owner == "Bob Martinez" for d in result.expected_deliverables)

    # Check milestones
    assert len(result.milestones) >= 2
    assert any("Ingestion Beta" in m.name for m in result.milestones)
    assert any(m.target_date == "2026-06-30" for m in result.milestones)


def test_scope_agent_extracts_responsibilities_and_evidence(sample_scope_text: str) -> None:
    agent = ScopeAgent()
    result = agent.analyze(text=sample_scope_text, filename="proposal.txt")

    assert len(result.team_responsibilities) >= 1
    assert "Alice Chen" in result.assigned_owners
    assert "Bob Martinez" in result.assigned_owners
    assert len(result.evidence_snippets) >= 1
    assert result.confidence_score >= 0.8


def test_scope_agent_unstructured_project_description(unstructured_scope_text: str) -> None:
    agent = ScopeAgent()
    result = agent.analyze(text=unstructured_scope_text, filename="unstructured.txt")

    # 1. Project Title is concise and does not contain the whole paragraph
    assert result.project_title == "Enterprise Cloud Analytics Platform (ECAP)"
    assert len(result.project_title) < 50

    # 2. Objectives separated cleanly
    assert len(result.objectives) >= 1
    assert any("telemetry" in obj.lower() for obj in result.objectives)
    assert not any("deliverables to be produced" in obj.lower() for obj in result.objectives)

    # 3. In-scope and Out-of-scope boundaries extracted from conversational text
    assert len(result.in_scope) >= 3
    assert any("kubernetes" in s.lower() for s in result.in_scope)
    assert len(result.out_of_scope) >= 1
    assert any("mainframe" in s.lower() for s in result.out_of_scope)

    # 4. Dates
    assert result.start_date == "2026-06-01"
    assert result.end_date == "2026-12-15"

    # 5. Deliverables individually detected
    deliv_names = [d.name for d in result.expected_deliverables]
    assert "Cloud Telemetry Pipeline" in deliv_names
    assert "Unified RBAC Gateway" in deliv_names
    assert "Real-Time Dashboard" in deliv_names
    assert "Data Warehouse Sync" in deliv_names

    # 6. Pending deliverables (none explicitly marked pending in unstructured text)
    assert result.pending_deliverables == []

    # 7. Milestones individually extracted
    assert len(result.milestones) == 3
    assert any("Architectural Foundation" in m.name and m.target_date == "2026-08-30" for m in result.milestones)
    assert any("Security Sign-off" in m.name and m.target_date == "2026-10-15" for m in result.milestones)
    assert any("Production Rollout" in m.name and m.target_date == "2026-12-10" for m in result.milestones)

    # 8. Team responsibilities & owners
    assert len(result.team_responsibilities) == 4
    assert "Alice Chen" in result.assigned_owners
    assert "Bob Martinez" in result.assigned_owners
    assert "Carol Vance" in result.assigned_owners
    assert "David Kim" in result.assigned_owners


def test_scope_agent_multiple_deliverables_in_one_paragraph() -> None:
    text = (
        "Project: Cloud Platform\n"
        "Expected Deliverables: Cloud Telemetry Pipeline, Unified RBAC Gateway, "
        "Real-Time Dashboard, Data Warehouse Sync."
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text)

    deliv_names = [d.name for d in result.expected_deliverables]
    assert len(deliv_names) == 4
    assert "Cloud Telemetry Pipeline" in deliv_names
    assert "Unified RBAC Gateway" in deliv_names
    assert "Real-Time Dashboard" in deliv_names
    assert "Data Warehouse Sync" in deliv_names


def test_scope_agent_owner_and_responsibility_extraction() -> None:
    text = (
        "Project Title: Enterprise Platform\n"
        "Deliverables:\n"
        "- Cloud Telemetry Pipeline\n"
        "- Unified RBAC Gateway\n"
        "- Real-Time Dashboard\n"
        "- Data Warehouse Sync\n\n"
        "Team responsibilities: Alice Chen – Cloud Telemetry Pipeline, "
        "Bob Martinez – Unified RBAC Gateway, Carol Vance – Real-Time Dashboard, "
        "David Kim – Data Warehouse Sync."
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text)

    assert len(result.team_responsibilities) == 4
    resp_map = {r.role_or_person: r.responsibility for r in result.team_responsibilities}
    assert resp_map["Alice Chen"] == "Cloud Telemetry Pipeline"
    assert resp_map["Bob Martinez"] == "Unified RBAC Gateway"
    assert resp_map["Carol Vance"] == "Real-Time Dashboard"
    assert resp_map["David Kim"] == "Data Warehouse Sync"

    # Correlated deliverable owners
    deliv_owner_map = {d.name: d.owner for d in result.expected_deliverables}
    assert deliv_owner_map["Cloud Telemetry Pipeline"] == "Alice Chen"
    assert deliv_owner_map["Unified RBAC Gateway"] == "Bob Martinez"
    assert deliv_owner_map["Real-Time Dashboard"] == "Carol Vance"
    assert deliv_owner_map["Data Warehouse Sync"] == "David Kim"


def test_scope_agent_missing_project_title_does_not_use_paragraph() -> None:
    paragraph = (
        "The primary goal of this initiative is to build a reliable telemetry and "
        "logging pipeline to support sub-second querying across distributed multi-region databases."
    )
    agent = ScopeAgent()
    result = agent.analyze(text=paragraph)

    assert result.project_title == "Unknown"
    assert result.project_title != paragraph


def test_scope_agent_missing_dates_and_scope_boundaries() -> None:
    text = (
        "Project Title: Minimalist Project\n"
        "Objectives:\n"
        "- Build a lightweight search engine.\n"
        "Deliverables:\n"
        "- Search Indexer"
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text)

    assert result.project_title == "Minimalist Project"
    assert result.start_date == "Not specified"
    assert result.end_date == "Not specified"
    assert result.in_scope == []
    assert result.out_of_scope == []
    assert len(result.expected_deliverables) == 1
    assert result.expected_deliverables[0].name == "Search Indexer"
    assert result.expected_deliverables[0].owner == "Unknown"
    assert result.expected_deliverables[0].deadline == "Not specified"


def test_scope_agent_never_invents_missing_data() -> None:
    sparse_text = "General project overview with no owners or dates mentioned."
    agent = ScopeAgent()
    result = agent.analyze(text=sparse_text, filename="sparse.txt")

    assert result.start_date == "Not specified"
    assert result.end_date == "Not specified"
    assert result.assigned_owners == []
    assert result.expected_deliverables == []
    assert result.milestones == []
    assert result.confidence_score <= 0.5


def test_scope_agent_handles_empty_input() -> None:
    agent = ScopeAgent()
    result = agent.analyze(text="", filename="empty.txt")

    assert result.project_title == "Unknown"
    assert result.start_date == "Not specified"
    assert result.end_date == "Not specified"
    assert result.confidence_score == 0.0


def test_scope_agent_user_reported_swagger_scenario() -> None:
    text = (
        "Project Title: Enterprise Cloud Analytics Platform.\n\n"
        "Objective: Build a cloud-based analytics platform for enterprise users.\n\n"
        "Deliverables: Cloud Telemetry Pipeline, Unified RBAC Gateway, Real-Time Dashboard, and Data Warehouse Sync.\n\n"
        "Milestone 1: Complete cloud telemetry pipeline.\n\n"
        "Milestone 2: Implement RBAC gateway.\n\n"
        "Milestone 3: Deploy dashboard and data warehouse integration.\n\n"
        "Responsibilities: Alice Chen owns the telemetry pipeline, Bob Martinez owns the RBAC gateway, "
        "Carol Vance owns the dashboard, and David Kim owns data warehouse integration.\n\n"
        "Pending deliverable: Complete integration testing."
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text, filename="proposal.txt")

    # 1. Project Title
    assert result.project_title == "Enterprise Cloud Analytics Platform"

    # 2. Objectives
    assert len(result.objectives) == 1
    assert "Build a cloud-based analytics platform" in result.objectives[0]

    # 3. Deliverables: exactly 4 distinct deliverables
    deliv_names = [d.name for d in result.expected_deliverables]
    assert len(deliv_names) == 4
    assert deliv_names == [
        "Cloud Telemetry Pipeline",
        "Unified RBAC Gateway",
        "Real-Time Dashboard",
        "Data Warehouse Sync",
    ]

    # Never split hyphenated names such as Real-Time Dashboard
    assert "Real-Time Dashboard" in deliv_names
    assert "Time Dashboard" not in deliv_names

    # Word 'Real' must NOT be treated as an owner
    assert "Real" not in result.assigned_owners
    assert not any(d.owner == "Real" for d in result.expected_deliverables)

    # 4. Responsibilities: 4 people and 4 mappings
    assert len(result.team_responsibilities) == 4
    resp_map = {r.role_or_person: r.responsibility for r in result.team_responsibilities}
    assert resp_map["Alice Chen"] == "telemetry pipeline"
    assert resp_map["Bob Martinez"] == "RBAC gateway"
    assert resp_map["Carol Vance"] == "dashboard"
    assert resp_map["David Kim"] == "data warehouse integration"

    # 5. Correlated owners to deliverables
    deliv_owner_map = {d.name: d.owner for d in result.expected_deliverables}
    assert deliv_owner_map["Cloud Telemetry Pipeline"] == "Alice Chen"
    assert deliv_owner_map["Unified RBAC Gateway"] == "Bob Martinez"
    assert deliv_owner_map["Real-Time Dashboard"] == "Carol Vance"
    assert deliv_owner_map["Data Warehouse Sync"] == "David Kim"

    # 6. Assigned owners: exactly 4 people
    assert sorted(result.assigned_owners) == ["Alice Chen", "Bob Martinez", "Carol Vance", "David Kim"]

    # 7. Pending deliverable: separated from expected deliverables
    assert result.pending_deliverables == ["Complete integration testing"]
    assert "Complete integration testing" not in deliv_names

    # 8. Milestones: exactly 3 distinct milestones
    assert len(result.milestones) == 3
    m_names = [m.name for m in result.milestones]
    assert any("Milestone 1" in m for m in m_names)
    assert any("Milestone 2" in m for m in m_names)
    assert any("Milestone 3" in m for m in m_names)


def test_scope_agent_hyphenated_deliverables_and_comma_and_lists() -> None:
    text = (
        "Deliverables: Zero-Trust Ingress, Real-Time Dashboard, and End-to-End Test Suite.\n"
        "Pending deliverable: Performance Benchmarking."
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text)

    names = [d.name for d in result.expected_deliverables]
    assert len(names) == 3
    assert "Zero-Trust Ingress" in names
    assert "Real-Time Dashboard" in names
    assert "End-to-End Test Suite" in names
    assert result.pending_deliverables == ["Performance Benchmarking"]


def test_scope_agent_multiple_responsibilities_in_one_paragraph() -> None:
    text = (
        "Team Responsibilities: Alice Chen owns the telemetry pipeline, "
        "Bob Martinez owns the RBAC gateway, and Carol Vance owns the dashboard."
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text)

    assert len(result.team_responsibilities) == 3
    assert "Alice Chen" in result.assigned_owners
    assert "Bob Martinez" in result.assigned_owners
    assert "Carol Vance" in result.assigned_owners


def test_scope_agent_deliverables_with_explicit_status_vs_unknown() -> None:
    text = (
        "Deliverables:\n"
        "- Ingestion Engine (Status: Completed)\n"
        "- Stream Processor (Status: In-Progress)\n"
        "- Query Gateway (Status: Pending)\n"
        "- Monitoring Service"
    )
    agent = ScopeAgent()
    result = agent.analyze(text=text)

    status_map = {d.name: d.status for d in result.expected_deliverables}
    assert status_map["Ingestion Engine"] == "completed"
    assert status_map["Stream Processor"] == "in_progress"
    assert status_map["Query Gateway"] == "pending"
    assert status_map["Monitoring Service"] == "unknown"

    # Only Query Gateway was explicitly marked as pending
    assert result.pending_deliverables == ["Query Gateway"]


def test_scope_agent_preserves_original_deliverable_names_single_line_swagger() -> None:
    text = (
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
    agent = ScopeAgent()
    result = agent.analyze(text=text, filename="swagger_payload.txt")

    # Assert exactly four expected deliverables
    assert len(result.expected_deliverables) == 4
    deliv_names = [d.name for d in result.expected_deliverables]
    assert deliv_names == [
        "Cloud Telemetry Pipeline",
        "Unified RBAC Gateway",
        "Real-Time Dashboard",
        "Data Warehouse Sync",
    ]

    # Fourth deliverable must be Data Warehouse Sync, owned by David Kim
    assert result.expected_deliverables[3].name == "Data Warehouse Sync"
    assert result.expected_deliverables[3].owner == "David Kim"
    assert "data warehouse integration" not in deliv_names

    # David Kim's responsibility remains "data warehouse integration"
    resp_map = {r.role_or_person: r.responsibility for r in result.team_responsibilities}
    assert resp_map["David Kim"] == "data warehouse integration"
    assert len(result.team_responsibilities) == 4

    # Exactly four assigned owners
    assert sorted(result.assigned_owners) == ["Alice Chen", "Bob Martinez", "Carol Vance", "David Kim"]

    # Exactly one pending deliverable
    assert result.pending_deliverables == ["Complete integration testing"]

    # Exactly three milestones
    assert len(result.milestones) == 3


def test_scope_agent_ecap_project_charter_extraction() -> None:
    charter_text = """Project Title: Enterprise Cloud Analytics Platform (ECAP)
Document Type: Official Project Charter & Architecture Specification
Version: 1.0 | Date: 2026-06-01
Sponsor: Enterprise Architecture Review Board
1. Executive Summary & Project Purpose
The Enterprise Cloud Analytics Platform (ECAP) modernizes telemetry data collection and distributed data warehouse operations.
2. Project Objectives
- Build a real-time event-driven telemetry pipeline processing 50,000 events/second.
- Implement zero-trust role-based access control (RBAC) gateway for API clients.
- Provide real-time operational risk intelligence dashboards for executive leadership.
- Enable automated streaming synchronization into Snowflake warehouse.
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
5. Project Governance and Approvals
Project Lead: Alice Chen. Security Lead: Bob Martinez. Frontend Lead: Carol Vance. DevOps Lead: David Kim.
Approved Initial Budget Allocation: $250,000.
"""
    agent = ScopeAgent()
    result = agent.analyze(text=charter_text, filename="project_charter.pdf")

    # 1. Out-of-Scope verification
    assert result.out_of_scope == [
        "Legacy mainframe hardware",
        "Native mobile applications",
        "Public third-party endpoints",
    ]
    for non_exclusion in ["Governance", "Approvals", "Project Lead", "Security Lead", "Budget", "$250,000"]:
        assert not any(non_exclusion.lower() in o.lower() for o in result.out_of_scope)

    # 2. In-Scope verification
    assert any("Kubernetes" in item for item in result.in_scope)
    assert any("Kafka" in item for item in result.in_scope)

    # 3. Deliverable deadlines & owners
    assert len(result.expected_deliverables) == 4
    deliv_map = {d.name: d for d in result.expected_deliverables}

    assert "Cloud Telemetry Pipeline" in deliv_map
    assert deliv_map["Cloud Telemetry Pipeline"].owner == "Alice Chen"
    assert deliv_map["Cloud Telemetry Pipeline"].deadline == "2026-08-15"
    assert deliv_map["Cloud Telemetry Pipeline"].target_date == "2026-08-15"
    assert deliv_map["Cloud Telemetry Pipeline"].status == "unknown"

    assert "Unified RBAC Gateway" in deliv_map
    assert deliv_map["Unified RBAC Gateway"].owner == "Bob Martinez"
    assert deliv_map["Unified RBAC Gateway"].deadline == "2026-09-30"
    assert deliv_map["Unified RBAC Gateway"].target_date == "2026-09-30"
    assert deliv_map["Unified RBAC Gateway"].status == "unknown"

    assert "Real-Time Dashboard" in deliv_map
    assert deliv_map["Real-Time Dashboard"].owner == "Carol Vance"
    assert deliv_map["Real-Time Dashboard"].deadline == "2026-11-20"
    assert deliv_map["Real-Time Dashboard"].target_date == "2026-11-20"
    assert deliv_map["Real-Time Dashboard"].status == "unknown"

    assert "Data Warehouse Sync" in deliv_map
    assert deliv_map["Data Warehouse Sync"].owner == "David Kim"
    assert deliv_map["Data Warehouse Sync"].deadline == "2026-12-01"
    assert deliv_map["Data Warehouse Sync"].target_date == "2026-12-01"
    assert deliv_map["Data Warehouse Sync"].status == "unknown"

    # 4. Team Responsibilities & Ownership
    assert len(result.team_responsibilities) == 4
    resp_map = {r.role_or_person: r for r in result.team_responsibilities}
    assert resp_map["Alice Chen"].role == "Project Lead"
    assert resp_map["Alice Chen"].responsibility == "Project Lead"
    assert resp_map["Alice Chen"].member == "Alice Chen"

    assert resp_map["Bob Martinez"].role == "Security Lead"
    assert resp_map["Bob Martinez"].responsibility == "Security Lead"
    assert resp_map["Bob Martinez"].member == "Bob Martinez"

    assert resp_map["Carol Vance"].role == "Frontend Lead"
    assert resp_map["Carol Vance"].responsibility == "Frontend Lead"
    assert resp_map["Carol Vance"].member == "Carol Vance"

    assert resp_map["David Kim"].role == "DevOps Lead"
    assert resp_map["David Kim"].responsibility == "DevOps Lead"
    assert resp_map["David Kim"].member == "David Kim"
