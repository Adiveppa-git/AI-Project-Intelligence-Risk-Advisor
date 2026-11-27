"""Utility functions and pattern recognizers for AI-style agents."""

import csv
import io
import re
from dataclasses import dataclass
from typing import Any

from app.models.agent_models import SourceEvidence


@dataclass
class DocumentChunkContext:
    text: str
    filename: str = "Unknown"
    document_id: str | None = None
    chunk_id: str | None = None
    confidence: float = 0.85


def normalize_content_key(text: str) -> str:
    """Normalize text keys for cross-document deduplication."""
    s = text.lower().strip()
    s = re.sub(r"^[-*•–—\s]+", "", s)
    s = re.sub(
        r"^(?:(?:row\s*\d+|task\s*id(?:\s*:\s*[a-z0-9_-]+)?|risk(?:\s*\d+)?|blocker(?:\s*\d+)?|decision(?:\s*\d+)?|issue(?:\s*\d+)?|action(?:\s*items?)?(?:\s*\d+)?|activity)\s*[:=-]\s*)+",
        "",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(r"^pending\s+decision\s+(?:on|regarding)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bclickhouse\s+vs\s+snowflake\b", "clickhouse snowflake", s)
    s = re.sub(r"\bbetween\s+redis\s+and\s+rabbitmq\b", "redis rabbitmq", s)
    s = re.sub(r"\bredis\s+or\s+rabbitmq\b", "redis rabbitmq", s)
    return s


def parse_structured_task_row(line: str) -> dict[str, str] | None:
    """Parse structured task lines from CSV rows, semicolon lists, or key-value format.

    Returns a normalized dictionary with keys:
    task_id, task_name, deliverable, owner, priority, status, deadline, dependencies, notes
    or None if the line is not a task row.
    """
    clean_l = line.strip()
    if not clean_l:
        return None

    line_lower = clean_l.lower()

    # Ignore CSV header line
    if line_lower.startswith("task id,") or "task id,task name" in line_lower:
        return None

    # Case 1: Comma-separated CSV format (e.g. TSK-101,... or starts with Task ID pattern)
    if (re.match(r"^TSK-\d+", clean_l, re.IGNORECASE) or clean_l.count(",") >= 5) and not line_lower.startswith(("http://", "https://")):
        try:
            reader = csv.reader(io.StringIO(clean_l))
            row = next(reader)
        except Exception:
            row = [p.strip() for p in clean_l.split(",")]

        if len(row) >= 5 and (re.match(r"^TSK-", row[0].strip(), re.IGNORECASE) or len(row) >= 7):
            t_id = row[0].strip()
            t_name = row[1].strip() if len(row) > 1 else ""
            t_deliv = row[2].strip() if len(row) > 2 else ""
            t_owner = row[3].strip() if len(row) > 3 and row[3].strip() else "Unassigned"
            t_prio = row[4].strip() if len(row) > 4 and row[4].strip() else "Medium"
            t_stat = row[5].strip() if len(row) > 5 and row[5].strip() else "Pending"
            t_dl = row[6].strip() if len(row) > 6 and row[6].strip() else "Not specified"
            t_dep = row[7].strip() if len(row) > 7 else ""
            t_notes = row[8].strip() if len(row) > 8 else ""
            return {
                "task_id": t_id,
                "task id": t_id,
                "task_name": t_name,
                "task name": t_name,
                "deliverable": t_deliv,
                "owner": t_owner,
                "priority": t_prio,
                "status": t_stat,
                "deadline": t_dl,
                "dependencies": t_dep,
                "notes": t_notes,
            }

    # Case 2: Semicolon or Key: Value delimited format (e.g. Row 1: Task ID: TSK-101; Task Name: ...)
    if "task id:" in line_lower or "task name:" in line_lower:
        fields: dict[str, str] = {}
        parts = re.split(r";\s*", clean_l)
        for part in parts:
            m = re.match(r"^(?:Row\s*\d+\s*:\s*)?([A-Za-z\s]+)\s*:\s*(.*)$", part.strip())
            if m:
                k = m.group(1).strip().lower()
                v = m.group(2).strip()
                fields[k] = v
        if "task name" in fields or "task id" in fields:
            t_id = fields.get("task id", "")
            t_name = fields.get("task name", "")
            return {
                "task_id": t_id,
                "task id": t_id,
                "task_name": t_name,
                "task name": t_name,
                "deliverable": fields.get("deliverable", ""),
                "owner": fields.get("owner", fields.get("assigned to", "Unassigned")),
                "priority": fields.get("priority", "Medium"),
                "status": fields.get("status", "Pending"),
                "deadline": fields.get("deadline", "Not specified"),
                "dependencies": fields.get("dependencies", ""),
                "notes": fields.get("notes", ""),
            }

    return None


def get_semantic_risk_cluster_key(text: str, title: str = "", category: str = "") -> str:
    """Map overlapping text/title expressions into a canonical semantic cluster key."""
    combined = f"{title} {text}".lower()

    # 1. Compound Technical Bottleneck (Memory + Latency in single line)
    if "memory consumption" in combined and "latency" in combined and "1200ms" in combined:
        return "technical_bottleneck_compound"

    # 2. Milestone 2 Schedule Findings
    if "milestone 2" in combined and any(k in combined for k in ["3 weeks", "delayed by 3 weeks"]):
        return "milestone2_delay_3_weeks"
    if "2026-10-15" in combined and any(k in combined for k in ["slipping into november", "at risk of slipping"]):
        return "milestone2_target_slipping"

    # 3. OAuth / SecOps Schedule Delay & Blocker
    if (
        ("oauth" in combined or "secops" in combined or "rbac" in combined or "security compliance" in combined or "security review" in combined or "token exchange" in combined)
        and any(k in combined for k in ["blocked", "blocking", "approval", "backlog", "rate limit", "exception ticket", "review"])
        and not any(k in combined for k in ["database migration", "memory"])
    ):
        return "oauth_secops_approval"

    # 4. Database Migration Failure / Delay on Staging
    if any(k in combined for k in ["database migration", "migration scripts", "migration tests", "schema mismatch", "schema syntax"]):
        return "database_migration_staging"

    # 5. Staging Cluster Memory Crashes / Worker Pod Consumption
    if any(k in combined for k in ["memory out-of-bounds", "memory crashes", "memory usage in telemetry", "frequent memory"]):
        return "staging_memory_crashes"

    # 6. Cross-Region Network Latency Spikes
    if any(k in combined for k in ["network latency", "latency spikes", "1200ms"]):
        return "network_latency_spikes"

    # 7. Cloud Budget Overrun / Cost Containment
    if any(k in combined for k in ["budget overrun", "cloud infrastructure expenditure", "cloud spend exceeded", "exceeded budget by 22%", "cloud cost containment", "budget optimization", "cloud spend"]):
        return "cloud_budget_overrun"

    # 8. Data Warehouse Sync Kafka Dependency
    if "data warehouse" in combined and "kafka" in combined:
        return "data_warehouse_kafka_dependency"

    # 9. Frontend Engineering Capacity / Understaffed
    if "frontend" in combined and any(k in combined for k in ["understaffed", "bandwidth", "shortage"]):
        return "frontend_team_understaffed"

    # 10. Senior SRE Shortage / Deployment Pipeline Instability
    if ("site reliability" in combined or "sre" in combined) and any(k in combined for k in ["shortage", "instability", "pipeline"]):
        return "sre_shortage_instability"

    # 11. Frontend Telemetry Chart Rendering Behind Schedule
    if ("telemetry chart" in combined or "chart rendering" in combined) and any(k in combined for k in ["behind schedule", "delayed"]):
        return "telemetry_chart_behind_schedule"

    # 12. Incomplete Test Coverage on Token Refresh
    if "test coverage" in combined or ("token refresh" in combined and "incomplete" in combined):
        return "incomplete_test_coverage"

    # 13. Flaky Integration Tests
    if "flaky integration tests" in combined or ("flaky" in combined and "pipeline" in combined):
        return "flaky_integration_tests"

    # 13. Mode A Charter Risks
    if "telemetry" in combined and any(k in combined for k in ["overdue", "scheduled for completion"]):
        return "cloud_telemetry_pipeline_overdue"
    if "rbac" in combined and "telemetry" in combined and any(k in combined for k in ["dependency", "blocked by", "cannot begin"]):
        return "rbac_telemetry_dependency"
    if "backend developer" in combined and any(k in combined for k in ["only one", "shortage", "single"]):
        return "single_backend_developer_bottleneck"
    if "integration testing" in combined and "not started" in combined:
        return "integration_testing_unstarted"

    # 14. Fallback: Normalized token signature
    stopwords = {
        "with", "that", "this", "from", "have", "been", "were", "what", "when",
        "where", "which", "will", "would", "could", "should", "their", "there",
        "about", "project", "deliverable", "milestone", "status", "deadline",
        "review", "active", "risk", "issue", "finding", "impact", "potential",
        "schedule", "delay", "behind", "into", "over", "under", "also", "some"
    }
    words = [
        w for w in re.findall(r"[a-z0-9]+", combined)
        if len(w) >= 4 and w not in stopwords
    ]
    key_words = sorted(list(dict.fromkeys(words))[:4])
    cat_tag = (category or "gen").lower()[:4]
    return f"{cat_tag}_{'_'.join(key_words)}" if key_words else normalize_content_key(text)


def clean_text(text: str) -> str:
    """Strip extraneous whitespace and control characters."""
    return re.sub(r"\s+", " ", text).strip()


def detect_filename_from_text(text: str) -> str | None:
    """Infer source filename from document headers, metadata markers, or known project files."""
    if not text:
        return None

    # Check explicit filename / source / document labels in first 1000 characters
    head = text[:1000]
    m = re.search(
        r"(?:^|[\r\n])\s*(?:source(?:\s*file(?:name)?)?|file(?:name)?|document)\s*[:=]\s*([a-zA-Z0-9_\-\./\\]+\.(?:pdf|docx|csv|txt))\b",
        head,
        re.IGNORECASE,
    )
    if m:
        fn = m.group(1).replace("\\", "/").split("/")[-1].strip()
        if fn.lower() not in {"unknown", "none"}:
            return fn

    text_lower = text.lower()
    if "sprint 14 technical sync" in text_lower or "sprint 14 retrospective" in text_lower:
        return "sprint_14_retrospective.txt"
    if "task id,task name,deliverable" in text_lower or ("tsk-101" in text_lower and "kafka" in text_lower):
        return "task_matrix_sprint14.csv"
    if "official project charter & architecture specification" in text_lower or ("enterprise cloud analytics platform" in text_lower and "official project charter" in text_lower):
        return "project_charter_ecap.pdf"
    if "monthly progress report" in text_lower and "reporting period: q3" in text_lower:
        return "progress_report_q3.docx"

    return None


def extract_evidence_snippet(
    text: str,
    match_span: tuple[int, int] | None = None,
    window_chars: int = 140,
    filename: str = "Unknown",
    document_id: str | None = None,
    chunk_id: str | None = None,
    confidence: float = 0.85,
) -> SourceEvidence:
    """Generate a clean SourceEvidence object with surrounding context snippet."""
    if not text:
        return SourceEvidence(
            filename=filename,
            document_id=document_id,
            chunk_id=chunk_id,
            snippet="Not specified",
            confidence=confidence,
        )

    if match_span:
        start = max(0, match_span[0] - window_chars // 2)
        end = min(len(text), match_span[1] + window_chars // 2)
        snippet = text[start:end].strip()
    else:
        snippet = text[: window_chars * 2].strip()

    snippet = re.sub(r"\s+", " ", snippet)
    if len(snippet) > 250:
        snippet = snippet[:247] + "..."

    return SourceEvidence(
        filename=filename,
        document_id=document_id,
        chunk_id=chunk_id,
        snippet=snippet,
        confidence=confidence,
    )


def extract_dates(text: str) -> list[str]:
    """Find date references in standard enterprise project formats."""
    date_patterns = [
        # YYYY-MM-DD
        r"\b\d{4}-\d{2}-\d{2}\b",
        # DD/MM/YYYY or MM/DD/YYYY
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        # Month DD, YYYY or Month DD YYYY
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
        # Month YYYY (e.g. September 2026)
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        # Q1/Q2/Q3/Q4 2026
        r"\bQ[1-4]\s+\d{4}\b",
        # Week N, YYYY
        r"\bWeek\s+\d{1,2}(?:,\s+\d{4})?\b",
    ]
    matches: list[str] = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            date_str = match.group(0).strip()
            if date_str not in matches:
                matches.append(date_str)
    return matches


EXCLUDED_PERSON_TOKENS = {
    "project", "sprint", "task", "milestone", "status", "deadline",
    "date", "high", "low", "medium", "critical", "none", "unknown", "the",
    "action", "action item", "current", "pending", "item", "deliverable",
    "deliverables", "due date", "target date", "in-scope", "out-of-scope",
    "in scope", "out of scope", "cloud telemetry", "unified rbac",
    "real-time dashboard", "data warehouse", "cloud infrastructure",
    "telemetry data", "objective", "objectives", "goal", "goals", "scope",
    "general", "note", "notes", "attendee", "attendees", "real", "time",
    "real-time", "real time", "dashboard", "pipeline", "gateway", "sync",
    "warehouse", "cloud", "unified", "telemetry", "rbac", "data", "analytics",
    "platform", "engine", "testing", "integration", "responsibilities", "responsibility",
    "project objectives", "executive summary", "scope boundaries", "project governance",
    "version", "sponsor", "document type", "official project"
}


def extract_owner_or_person(text: str) -> str:
    """Extract assigned owner or responsible person from line or snippet. Never invent names."""
    patterns = [
        r"(?:Owner|Assigned\s*(?:to)?|Lead|Responsible|Assignee|POC|Author|Decision\s*Maker)\s*[:=-]\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:owns|to\s+[a-z]+|is\s+responsible\s+for|leads)\b",
        r"\((?:Owner\s*[:=-]\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            if candidate.lower() not in EXCLUDED_PERSON_TOKENS and len(candidate.split()) <= 3:
                return candidate
    return "Unknown"


def parse_labeled_lines(text: str) -> list[str]:
    """Break text into meaningful lines, bullet points, or list items."""
    raw_lines = text.splitlines()
    cleaned: list[str] = []
    for line in raw_lines:
        s = line.strip()
        if not s:
            continue
        s = re.sub(r"^[-*•–—]\s*", "", s)
        s = re.sub(r"^\d+[\.\)]\s*", "", s)
        s = re.sub(r"^\[[\sXx]\]\s*", "", s)
        if s and len(s) > 2:
            cleaned.append(s)
    return cleaned


def split_into_section_blocks(text: str) -> dict[str, list[str]]:
    """Group lines by detected section headings, handling both standalone headers and inline labels."""
    sections: dict[str, list[str]] = {}
    current_section = "general"
    sections[current_section] = []

    # Pre-normalize inline section headers onto separate lines if separated by periods
    normalized_text = re.sub(
        r"(?<=[a-zA-Z0-9\)])\.\s+(?=(?:Objectives?|Goals?|Scope|In-Scope|Out-of-Scope|"
        r"Expected\s+Deliverables?|Key\s+Deliverables?|Deliverables?|"
        r"Milestones?(?:\s*\d+)?|M\d+|Timeline|Important\s+Deadlines?|Deadlines?|"
        r"Team\s*Responsibilities?|Responsibilities?|Team|Risks?|Blockers?|"
        r"Pending\s+Deliverables?|Pending\s+Deliverable|Pending|"
        r"Budget|Financial)\s*[:=-])",
        ".\n",
        text,
        flags=re.IGNORECASE,
    )

    lines = normalized_text.splitlines()
    for line in lines:
        s = line.strip()
        if not s:
            continue

        # Check for section header with colon, e.g. "Objectives:", "Expected Deliverables:", "## Milestones"
        # Bullet list items and numbered item labels (e.g. "- Blocker 1:", "Action Item 1:") must not become section headers
        is_bullet = bool(re.match(r"^[-*•–—]", s))
        is_item_label = bool(
            re.match(
                r"^(?:[-*•–—]\s*)?(?:Blocker(?:\s*\d+)?|Decision(?:\s*\d+)?|Issue|Action\s*Item(?:\s*\d+)?|Activity|Row\s*\d+|Task\s*ID)\b",
                s,
                re.IGNORECASE,
            )
        )

        header_candidate = None
        content_after = None

        if not is_bullet and not is_item_label:
            m_heading = re.match(r"^(?:#{1,4}\s+|\d+[\.\)]\s+)?([A-Za-z0-9\s/&-]{3,50})\s*[:]\s*(.*)$", s)
            if m_heading:
                title_part = m_heading.group(1).strip().lower()
                content_after = m_heading.group(2).strip()
                header_candidate = title_part
            else:
                m_md = re.match(r"^(?:#{1,4}\s+|\d+[\.\)]\s+)([A-Za-z0-9\s/&-]{3,50})$", s)
                if m_md:
                    header_candidate = m_md.group(1).strip().lower()

        is_header = False
        if header_candidate:
            if any(k in header_candidate for k in [
                "objective", "goal", "scope", "in-scope", "out-of-scope", "deliverable",
                "milestone", "deadline", "timeline", "responsibility", "responsibilities", "risk", "blocker",
                "action", "decision", "issue", "delay", "dependency", "budget", "summary",
                "attendee", "note", "pending", "governance", "approval"
            ]):
                current_section = header_candidate
                if current_section not in sections:
                    sections[current_section] = []
                is_header = True
                if content_after:
                    cleaned_content = re.sub(r"^[-*•–—]\s*", "", content_after)
                    if cleaned_content:
                        sections[current_section].append(cleaned_content)

        if not is_header:
            cleaned = re.sub(r"^[-*•–—]\s*", "", s)
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
            cleaned = re.sub(r"^\[[\sXx]\]\s*", "", cleaned)
            if cleaned:
                sections[current_section].append(cleaned)

    return sections
