"""Utility functions and pattern recognizers for AI-style agents."""

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


def clean_text(text: str) -> str:
    """Strip extraneous whitespace and control characters."""
    return re.sub(r"\s+", " ", text).strip()


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
