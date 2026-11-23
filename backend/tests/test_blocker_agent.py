"""Tests for Blocker and Action Item Identification Agent."""

import pytest

from app.agents.blocker_agent import BlockerAgent
from app.models.agent_models import BlockerAnalysisResult


@pytest.fixture
def sample_blocker_text() -> str:
    return """
    Meeting Notes - Weekly Sync

    Current Blockers:
    - Blocker 1: Ingestion pipeline blocked by SecOps approval for OAuth tokens (Owner: Bob Martinez).
    - Database migration scripts failing on staging cluster.

    Pending Decisions:
    - Pending decision on choosing ClickHouse vs Snowflake (Decision Maker: David Kim, Deadline: 2026-09-25).

    Unresolved Issues:
    - Intermittent network latency spikes exceeding 1200ms.
    - Flaky integration tests in the continuous delivery pipeline.

    Delayed Activities:
    - Staging run is delayed by 10 days due to schema incompatibilities.

    Action Items:
    - Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
    - Action Item 2: Alice Chen to profile memory usage in telemetry worker pods by 2026-09-24 (Priority: High)
    - Action Item 3: Investigate failing database migration scripts on staging (Priority: High)
    - [x] Completed task: Set up initial GitHub repository (Owner: David Kim)
    """


def test_blocker_agent_extracts_blockers(sample_blocker_text: str) -> None:
    agent = BlockerAgent()
    result = agent.analyze(text=sample_blocker_text, filename="meeting.txt")

    assert isinstance(result, BlockerAnalysisResult)
    assert len(result.blockers) >= 2
    b_descs = [b.description for b in result.blockers]
    assert any("SecOps approval" in d for d in b_descs)
    assert any("failing on staging" in d for d in b_descs)


def test_blocker_agent_extracts_decisions_and_issues(sample_blocker_text: str) -> None:
    agent = BlockerAgent()
    result = agent.analyze(text=sample_blocker_text, filename="meeting.txt")

    assert len(result.pending_decisions) >= 1
    dec = result.pending_decisions[0]
    assert "ClickHouse vs Snowflake" in dec.description
    assert dec.decision_maker == "David Kim"
    assert dec.deadline == "2026-09-25"

    assert len(result.unresolved_issues) >= 1
    assert any("latency spikes" in iss.title.lower() for iss in result.unresolved_issues)


def test_blocker_agent_extracts_action_items_and_attributes(sample_blocker_text: str) -> None:
    agent = BlockerAgent()
    result = agent.analyze(text=sample_blocker_text, filename="meeting.txt")

    assert len(result.action_items) >= 3
    # Check assigned person
    bob_action = next((a for a in result.action_items if a.assigned_person == "Bob Martinez"), None)
    assert bob_action is not None
    assert bob_action.priority == "Critical"
    assert bob_action.deadline == "2026-09-20"
    assert bob_action.current_status == "Pending"

    # Check unassigned action item
    unassigned = [a for a in result.action_items if a.assigned_person == "Unassigned"]
    assert len(unassigned) >= 1
    assert result.unassigned_action_items_count == len(unassigned)

    # Check completed task
    completed = next((a for a in result.action_items if a.current_status == "Completed"), None)
    assert completed is not None
    assert "GitHub repository" in completed.description


def test_blocker_agent_never_invents_owners_or_deadlines() -> None:
    sparse_text = """
    Action Items:
    - Update documentation formatting.
    """
    agent = BlockerAgent()
    result = agent.analyze(text=sparse_text, filename="notes.txt")

    assert len(result.action_items) == 1
    item = result.action_items[0]
    assert item.assigned_person == "Unassigned"
    assert item.deadline == "Not specified"


def test_blocker_agent_handles_empty_input() -> None:
    agent = BlockerAgent()
    result = agent.analyze(text="", filename="empty.txt")

    assert result.blockers == []
    assert result.action_items == []
    assert result.pending_decisions == []
    assert result.confidence_score == 0.0


USER_BLOCKER_TEST_INPUT = """Project: Enterprise Cloud Analytics Platform.

Meeting Date: 2026-11-22.

The Cloud Telemetry Pipeline API is delayed because authentication testing is incomplete.

Alice Chen must complete authentication testing by 2026-11-24.

Bob Martinez cannot start RBAC integration until the telemetry API is available.

The team has not decided whether to use Redis or RabbitMQ for event processing.

Carol Vance must prepare dashboard integration tests by 2026-11-25.

David Kim reported that data warehouse credentials are still pending from the infrastructure team.

The project manager must schedule a dependency review meeting by 2026-11-23."""


def test_blocker_agent_user_test_input() -> None:
    agent = BlockerAgent()
    result = agent.analyze(text=USER_BLOCKER_TEST_INPUT, filename="sprint_meeting.txt")

    assert isinstance(result, BlockerAnalysisResult)

    # A. Blockers (exactly 3)
    assert len(result.blockers) == 3
    b_titles = [b.title for b in result.blockers]
    assert any("authentication testing incomplete" in t.lower() and "telemetry" in t.lower() for t in b_titles)
    assert any("rbac integration blocked" in t.lower() and "telemetry" in t.lower() for t in b_titles)
    assert any("data warehouse credentials pending" in t.lower() for t in b_titles)

    # Verify Bob Martinez is owner of the RBAC blocker
    rbac_b = next(b for b in result.blockers if "rbac" in b.title.lower())
    assert rbac_b.assigned_owner == "Bob Martinez"
    assert "RBAC integration" in rbac_b.affected_activities

    # B. Unresolved Issues (exactly 2)
    assert len(result.unresolved_issues) == 2
    iss_titles = [iss.title for iss in result.unresolved_issues]
    assert any("authentication testing remains incomplete" in t.lower() for t in iss_titles)
    assert any("data warehouse credentials" in t.lower() and "not yet been received" in t.lower() for t in iss_titles)

    # C. Pending Decisions (exactly 1)
    assert len(result.pending_decisions) == 1
    dec = result.pending_decisions[0]
    assert "Redis" in dec.description and "RabbitMQ" in dec.description
    assert "event processing" in dec.description
    assert dec.deadline == "Not specified"

    # D. Delayed Activities (exactly 1, not entire document)
    assert len(result.delayed_activities) == 1
    dly = result.delayed_activities[0]
    assert "Cloud Telemetry Pipeline API" in dly.description
    assert "authentication testing is incomplete" in dly.description.lower() or "authentication testing is incomplete" in dly.reason.lower()
    assert len(dly.description) < 150
    assert "Enterprise Cloud Analytics Platform" not in dly.description

    # E. Action Items (exactly 3; David Kim must not have an action item)
    assert len(result.action_items) == 3
    alice_act = next((a for a in result.action_items if a.assigned_person == "Alice Chen"), None)
    assert alice_act is not None
    assert "authentication testing" in alice_act.description.lower()
    assert alice_act.deadline == "2026-11-24"
    assert alice_act.priority == "Critical"

    carol_act = next((a for a in result.action_items if a.assigned_person == "Carol Vance"), None)
    assert carol_act is not None
    assert "dashboard integration tests" in carol_act.description.lower()
    assert carol_act.deadline == "2026-11-25"

    pm_act = next((a for a in result.action_items if a.assigned_person == "Project Manager"), None)
    assert pm_act is not None
    assert "dependency review meeting" in pm_act.description.lower()
    assert pm_act.deadline == "2026-11-23"

    # Confirm David Kim has no action item
    assert not any(a.assigned_person == "David Kim" for a in result.action_items)

    # F. Dependencies Requiring Attention
    assert len(result.dependencies_requiring_attention) >= 1
    dep_text = result.dependencies_requiring_attention[0]
    assert "Cloud Telemetry Pipeline API" in dep_text
    assert "RBAC integration" in dep_text
    assert "Blocked" in dep_text
    assert "telemetry API is available" in dep_text

    # G. Recommended Next Steps (5 items)
    assert len(result.recommended_next_steps) == 5
    recs = " ".join(result.recommended_next_steps).lower()
    assert "complete authentication testing" in recs
    assert "resolve the telemetry api blocker" in recs
    assert "obtain data warehouse credentials" in recs
    assert "finalize the redis/rabbitmq decision" in recs
    assert "schedule the dependency review meeting" in recs


def test_blocker_agent_single_line_swagger_input() -> None:
    agent = BlockerAgent()
    single_line = " ".join(USER_BLOCKER_TEST_INPUT.split())
    result = agent.analyze(text=single_line, filename="swagger_payload.txt")

    assert len(result.blockers) == 3
    assert len(result.unresolved_issues) == 2
    assert len(result.pending_decisions) == 1
    assert len(result.delayed_activities) == 1
    assert len(result.action_items) == 3
    assert len(result.delayed_activities[0].description) < 150
    assert "Enterprise Cloud Analytics Platform" not in result.delayed_activities[0].description


def test_blocker_agent_missing_owner_and_deadline() -> None:
    agent = BlockerAgent()
    sparse_text = """
    Action Items:
    - Update deployment documentation by 2026-12-01.
    - Bob Martinez must refactor telemetry consumer.
    """
    result = agent.analyze(text=sparse_text, filename="notes.txt")

    assert len(result.action_items) == 2
    item1 = next((a for a in result.action_items if "deployment documentation" in a.description.lower()), None)
    assert item1 is not None
    assert item1.assigned_person == "Unassigned"
    assert item1.deadline == "2026-12-01"

    item2 = next((a for a in result.action_items if "telemetry consumer" in a.description.lower()), None)
    assert item2 is not None
    assert item2.assigned_person == "Bob Martinez"
    assert item2.deadline == "Not specified"


def test_blocker_agent_text_with_no_identifiable_action_items() -> None:
    agent = BlockerAgent()
    safe_text = "All team members attended the sprint retro. The meeting was productive and concluded on time."
    result = agent.analyze(text=safe_text, filename="safe.txt")

    assert result.action_items == []
    assert result.unassigned_action_items_count == 0
    assert result.blockers == []
    assert result.delayed_activities == []


def test_duplicate_blocker_detection() -> None:
    agent = BlockerAgent()
    text = """
    ## Current Blockers
    - Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
    - Blocker 6: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange.
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.blockers) == 1
    assert res.blockers[0].assigned_owner == "Bob Martinez"
    assert len(res.blockers[0].supporting_evidence) >= 1


def test_duplicate_issue_detection() -> None:
    agent = BlockerAgent()
    text = """
    ## Unresolved Issues
    - Issue 1: Intermittent network latency spikes exceeding 1200ms when querying cross-region replicas.
    - Issue: Intermittent network latency spikes exceeding 1200ms when querying cross-region replicas.
    - Incomplete test coverage on token refresh failure modes.
    - Incomplete test coverage on token refresh failure modes.
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.unresolved_issues) == 2
    titles = [i.title.lower() for i in res.unresolved_issues]
    assert any("latency spikes" in t for t in titles)
    assert any("test coverage" in t for t in titles)


def test_duplicate_pending_decision_detection() -> None:
    agent = BlockerAgent()
    text = """
    ## Pending Decisions
    - Decision 1: Pending decision on selecting ClickHouse vs Snowflake for warm telemetry storage tier (Decision Maker: David Kim, Deadline: 2026-09-25).
    - Decision 3: Pending decision on selecting ClickHouse vs Snowflake for warm telemetry storage tier.
    - Decision 2: Pending decision regarding Kafka partition sizing and retention policy sign-off (Decision Maker: Alice Chen, Deadline: 2026-09-28).
    - Decision 4: Pending decision regarding Kafka partition sizing and retention policy sign-off.
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.pending_decisions) == 2
    dec1 = next((d for d in res.pending_decisions if "clickhouse" in d.description.lower()), None)
    assert dec1 is not None
    assert dec1.decision_maker == "David Kim"
    assert dec1.deadline == "2026-09-25"


def test_duplicate_delayed_activity_detection() -> None:
    agent = BlockerAgent()
    text = """
    ## Delayed Activities
    - Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.
    - Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.delayed_activities) == 1
    assert "Database migration" in res.delayed_activities[0].description


def test_duplicate_action_item_detection() -> None:
    agent = BlockerAgent()
    text = """
    ## Action Items
    - Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
    - Action Item 7: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.action_items) == 1
    assert res.action_items[0].assigned_person == "Bob Martinez"
    assert res.action_items[0].priority == "Critical"


def test_completed_task_exclusion() -> None:
    agent = BlockerAgent()
    text = """
    Task ID: TSK-101; Task Name: Deploy Kafka Ingestion Brokers; Owner: Alice Chen; Priority: High; Status: Completed; Deadline: 2026-08-10; Notes: Deployed successfully
    Task ID: TSK-102; Task Name: Configure RBAC OAuth Gateway; Owner: Bob Martinez; Priority: Critical; Status: In progress; Deadline: 2026-09-28; Notes: Ongoing
    """
    res = agent.analyze(text=text, filename="tasks.csv")
    assert len(res.action_items) == 1
    assert res.action_items[0].description == "Configure RBAC OAuth Gateway"
    assert not any("Deploy Kafka Ingestion Brokers" in a.description for a in res.action_items)
    assert not any("Deploy Kafka Ingestion Brokers" in iss.title for iss in res.unresolved_issues)


def test_project_title_and_heading_exclusion() -> None:
    agent = BlockerAgent()
    text = """
    Enterprise Cloud Analytics Platform - Monthly Progress Report
    Reporting Period: Q3 2026
    Prepared by: Project Delivery Management Office
    1. Executive Delivery Summary
    2. Schedule and Delivery Risks
    3. Budget and Resource Constraints
    Deliverables and Milestone Status
    Out-of-Scope: Native mobile client applications (iOS and Android).
    Action Items:
    - Alice Chen to profile memory usage by 2026-09-24.
    """
    res = agent.analyze(text=text, filename="report.docx")
    assert len(res.action_items) == 1
    assert res.action_items[0].assigned_person == "Alice Chen"
    act_descs = [a.description.lower() for a in res.action_items]
    assert not any("progress report" in d for d in act_descs)
    assert not any("reporting period" in d for d in act_descs)
    assert not any("executive summary" in d for d in act_descs)
    assert not any("out-of-scope" in d for d in act_descs)
    assert not any("native mobile" in d for d in act_descs)


def test_structured_csv_task_extraction() -> None:
    agent = BlockerAgent()
    row = "Row 2: Task ID: TSK-102; Task Name: Configure RBAC OAuth Gateway; Deliverable: Unified RBAC Security Gateway; Owner: Bob Martinez; Priority: Critical; Status: In progress; Deadline: 2026-09-28; Dependencies: SecOps Approval; Notes: Blocked by security compliance review"
    res = agent.analyze(text=row, filename="task_list.csv")
    assert len(res.action_items) == 1
    act = res.action_items[0]
    assert act.description == "Configure RBAC OAuth Gateway"
    assert act.assigned_person == "Bob Martinez"
    assert act.deadline == "2026-09-28"
    assert act.priority == "Critical"
    assert act.current_status == "In progress"
    assert act.source_document == "task_list.csv"


def test_concise_action_descriptions() -> None:
    agent = BlockerAgent()
    text = """
    ## Action Items
    - Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
    - Action Item 4: Carol Vance to mock dashboard response models by 2026-09-28 (Priority: Medium)
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.action_items) == 2
    assert res.action_items[0].description == "Submit SecOps compliance exception ticket"
    assert res.action_items[1].description == "Mock dashboard response models"


def test_correct_affected_activity_extraction() -> None:
    agent = BlockerAgent()
    text = """
    ## Current Blockers
    - Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
    - Blocker 3: Staging cluster environment is experiencing frequent memory out-of-bounds crashes, halting integration tests.
    """
    res = agent.analyze(text=text, filename="meeting.txt")
    assert len(res.blockers) == 2
    b1 = next((b for b in res.blockers if "Ingestion pipeline" in b.title), None)
    assert b1 is not None
    assert "Ingestion pipeline" in b1.affected_activities
    assert b1.assigned_owner == "Bob Martinez"

    b2 = next((b for b in res.blockers if "memory crashes" in b.title.lower()), None)
    assert b2 is not None
    assert "Integration tests" in b2.affected_activities


def test_multiple_document_evidence_provenance() -> None:
    from app.agents.blocker_agent import DocumentChunkContext
    agent = BlockerAgent()
    chunk1 = DocumentChunkContext(
        text="## Current Blockers\n- Blocker 2: Database migration scripts failing on staging cluster.",
        filename="meeting_notes.txt",
        document_id="doc-notes-01",
        chunk_id="chk-01",
    )
    chunk2 = DocumentChunkContext(
        text="Row 4: Task ID: TSK-104; Task Name: Execute Staging Database Migration; Owner: Unassigned; Priority: High; Status: Pending; Deadline: 2026-09-30; Notes: Migration tests failing on staging",
        filename="task_list.csv",
        document_id="doc-csv-02",
        chunk_id="chk-02",
    )
    res = agent._extract_blockers_and_actions_from_chunks([chunk1, chunk2])
    assert len(res.blockers) >= 1
    migration_blk = next((b for b in res.blockers if "migration" in b.title.lower()), None)
    assert migration_blk is not None
    ev_files = {e.filename for e in migration_blk.supporting_evidence}
    assert "meeting_notes.txt" in ev_files
    assert "task_list.csv" in ev_files

    act = next((a for a in res.action_items if "Staging Database Migration" in a.description), None)
    assert act is not None
    assert act.source_document == "task_list.csv"


def test_recommended_next_steps_without_duplicates() -> None:
    agent = BlockerAgent()
    text = """
    ## Current Blockers
    - Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
    ## Action Items
    - Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
    - Action Item 2: Alice Chen to profile memory usage in telemetry worker pods by 2026-09-24 (Priority: High)
    """
    res = agent.analyze(text=text, filename="notes.txt")
    assert len(res.recommended_next_steps) >= 2
    assert len(res.recommended_next_steps) == len(set(res.recommended_next_steps))


def test_existing_multi_agent_orchestrator_compatibility() -> None:
    from app.services.agent_orchestrator import AgentOrchestratorService
    from app.models.agent_models import MultiAgentAnalysisRequest
    orchestrator = AgentOrchestratorService()
    req = MultiAgentAnalysisRequest(
        text="""
        Project Title: Enterprise Cloud Analytics Platform
        Objectives: Modernize enterprise data platform.
        Milestones: Milestone 1: Beta release by 2026-10-15 (Owner: Alice Chen)
        Current Blockers: Ingestion pipeline blocked by SecOps approval (Owner: Bob Martinez).
        Action Items: Bob Martinez to submit SecOps ticket by 2026-09-20 (Priority: Critical)
        """,
        top_k=5,
    )
    report = orchestrator.analyze_project(req)
    assert report.project_title == "Enterprise Cloud Analytics Platform"
    assert len(report.blockers_and_actions.blockers) >= 1
    assert len(report.blockers_and_actions.action_items) >= 1
    assert report.blockers_and_actions.action_items[0].assigned_person == "Bob Martinez"
    assert report.project_health in ["Critical", "At Risk", "Needs Attention"]


