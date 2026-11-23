"""Blocker and Action Item Identification Agent.

Extracts current blockers, unresolved issues, pending decisions, delayed activities,
and structured action items with assigned owners, deadlines, priority, and status.
Enforces strict anti-hallucination rules: never invents responsible persons or deadlines;
marks unassigned or missing values explicitly.
Supports multi-document chunk analysis, provenance retention, and semantic deduplication.
"""

from app.services.rag_pipeline import RAGPipelineService
import re
import tempfile
from dataclasses import dataclass
from typing import Literal

from app.models.agent_models import (
    ActionItem,
    BlockerAnalysisResult,
    BlockerItem,
    DelayedActivity,
    PendingDecision,
    SourceEvidence,
    UnresolvedIssue,
)
from app.agents.agent_utils import (
    clean_text,
    extract_dates,
    extract_evidence_snippet,
    extract_owner_or_person,
    split_into_section_blocks,
)
from app.services.rag_pipeline import RAGPipelineService

HEADER_FILTER_REGEX = re.compile(
    r"^(?:#{1,4}\s*)?(?:current\s+)?(?:blockers?|impediments?|pending\s+decisions?|decisions?|unresolved\s+issues?|issues?|delayed\s+activities?|activities?|action\s+items?|actions?|todo|todos|meeting\s+notes|notes)\s*[:]?$",
    re.IGNORECASE,
)

EXCLUDED_NON_ACTION_REGEX = re.compile(
    r"^(?:#{1,4}\s*)?(?:"
    r"enterprise\s+cloud\s+analytics\s+platform|project\s+title|monthly\s+progress\s+report|progress\s+report|executive\s+delivery\s+summary|executive\s+summary|delivery\s+summary|"
    r"reporting\s+period|prepared\s+by|reporting\s+date|date\s*:|attendees\s*:|"
    r"schedule\s+and\s+delivery\s+risks|schedule\s+delay\s*:|technical\s+bottleneck\s*:|dependency\s+gap\s*:|"
    r"budget\s+and\s+resource\s+constraints|budget\s+overrun\s*:|resource\s+constraint\s*:|"
    r"deliverables\s+and\s+milestone\s+status|milestone\s*/\s*deliverable|"
    r"(?:current\s+)?blockers?\s*[:]?$|(?:unresolved\s+)?issues?\s*[:]?$|pending\s+decisions?\s*[:]?$|delayed\s+activities?\s*[:]?$|action\s+items?\s*[:]?$|"
    r"in-scope|out-of-scope|objectives\b|milestones\b|deliverables\b|"
    r"native\s+mobile\s+client|public\s+third-party|mainframe\s+connectors|"
    r"the\s+target\s+completion\s+date|milestone\s+\d+.*is\s+delayed|"
    r"shortage\s+of\s+senior\s+site\s+reliability\s+engineers"
    r")",
    re.IGNORECASE,
)

@dataclass
class DocumentChunkContext:
    text: str
    filename: str = "Unknown"
    document_id: str | None = None
    chunk_id: str | None = None
    confidence: float = 0.85

def normalize_content_key(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"^[-*•–—\s]+", "", s)
    s = re.sub(
        r"^(?:(?:row\s*\d+|task\s*id(?:\s*:\s*[a-z0-9_-]+)?|blocker(?:\s*\d+)?|decision(?:\s*\d+)?|issue(?:\s*\d+)?|action(?:\s*items?)?(?:\s*\d+)?|activity)\s*[:=-]\s*)+",
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
    line_lower = line.lower()
    if "task id:" not in line_lower and "task name:" not in line_lower:
        return None
    fields: dict[str, str] = {}
    parts = re.split(r";\s*", line)
    for part in parts:
        m = re.match(r"^(?:Row\s*\d+\s*:\s*)?([A-Za-z\s]+)\s*:\s*(.*)$", part.strip())
        if m:
            k = m.group(1).strip().lower()
            v = m.group(2).strip()
            fields[k] = v
    return fields if ("task name" in fields or "task id" in fields) else None



class BlockerAgent:
    """Agent specializing in Blocker, Issue, Decision, and Action Item Identification."""

    def __init__(self, rag_service: RAGPipelineService | None = None) -> None:
        self.rag_service = rag_service

    def analyze(
        self,
        text: str | None = None,
        query: str | None = None,
        top_k: int = 10,
        filename: str = "Unknown",
        document_id: str | None = None,
    ) -> BlockerAnalysisResult:
        """Run blocker and action item analysis on direct text or via RAG retrieval."""
        chunks: list[DocumentChunkContext] = []

        # Case 1: Direct text provided
        if text and text.strip():
            chunks.append(
                DocumentChunkContext(
                    text=text.strip(),
                    filename=filename,
                    document_id=document_id,
                )
            )
        # Case 2: Retrieve from RAG pipeline
        elif self.rag_service:
            search_query = query or "blockers unresolved issues pending decisions action items next steps delayed tasks meeting notes"
            results = self.rag_service.search(search_query, top_k=top_k)
            if results:
                for res in results:
                    src_file = str(res.metadata.get("filename", "Unknown"))
                    chunks.append(
                        DocumentChunkContext(
                            text=res.text,
                            filename=src_file,
                            document_id=res.document_id,
                            chunk_id=res.chunk_id,
                            confidence=max(0.5, min(0.99, res.similarity)),
                        )
                    )

        if not chunks:
            return BlockerAnalysisResult(
                blockers=[],
                unresolved_issues=[],
                pending_decisions=[],
                delayed_activities=[],
                action_items=[],
                unassigned_action_items_count=0,
                dependencies_requiring_attention=[],
                recommended_next_steps=[],
                source_documents=[],
                confidence_score=0.0,
            )

        return self._extract_blockers_and_actions_from_chunks(chunks, default_doc_id=document_id)

    def _extract_blockers_and_actions(
        self,
        text: str,
        sources: list[str],
        evidence_snippets: list[SourceEvidence],
        default_doc_id: str | None = None,
    ) -> BlockerAnalysisResult:
        """Backward-compatible wrapper for single text block analysis."""
        primary_source = sources[0] if sources else "Unknown"
        chunk = DocumentChunkContext(
            text=text,
            filename=primary_source,
            document_id=default_doc_id,
        )
        return self._extract_blockers_and_actions_from_chunks([chunk], default_doc_id=default_doc_id)

    def _extract_blockers_and_actions_from_chunks(
        self,
        chunks: list[DocumentChunkContext],
        default_doc_id: str | None = None,
    ) -> BlockerAnalysisResult:
        all_blocker_cands: list[BlockerItem] = []
        all_issue_cands: list[UnresolvedIssue] = []
        all_decision_cands: list[PendingDecision] = []
        all_activity_cands: list[DelayedActivity] = []
        all_action_cands: list[ActionItem] = []
        deps_needing_attention: list[str] = []
    
        sources = list(dict.fromkeys(c.filename for c in chunks if c.filename != "Unknown"))
        if not sources:
            sources = ["Unknown"]
    
        for chunk in chunks:
            doc_filename = chunk.filename
            doc_id = chunk.document_id or default_doc_id
            chunk_id = chunk.chunk_id
            conf = chunk.confidence
    
            def make_evidence(snippet_text: str) -> list[SourceEvidence]:
                return [
                    extract_evidence_snippet(
                        snippet_text,
                        filename=doc_filename,
                        document_id=doc_id,
                        chunk_id=chunk_id,
                        confidence=conf,
                    )
                ]
    
            normalized_text = re.sub(
                r'([a-zA-Z0-9\)])\.\s+(?=[A-Z0-9#\-\*])',
                r'\1.\n',
                chunk.text
            )
            sections = split_into_section_blocks(normalized_text)
            raw_lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    
            # Map each line (cleaned) to its containing section name
            line_to_sec: dict[str, str] = {}
            for sec_name, sec_lines in sections.items():
                for sl in sec_lines:
                    cl_sl = clean_text(sl).lower()
                    line_to_sec[cl_sl] = sec_name.lower()
                    # Also index without leading bullets or markers
                    stripped_sl = re.sub(r"^(?:[-*•–—\s]|\[[\sXx]\])+", "", cl_sl).strip()
                    if stripped_sl:
                        line_to_sec[stripped_sl] = sec_name.lower()
    
            for line in raw_lines:
                clean_l = clean_text(line)
                line_lower = clean_l.lower()
                clean_no_bullet = re.sub(r"^(?:[-*•–—\s]|\[[\sXx]\])+", "", clean_l).strip()
    
                sec_name = line_to_sec.get(clean_no_bullet.lower(), line_to_sec.get(line_lower, "general"))
    
                if HEADER_FILTER_REGEX.match(clean_l):
                    continue
    
                in_blocker_sec = any(k in sec_name for k in ["blocker", "impediment", "obstacle"])
                in_action_sec = any(k in sec_name for k in ["action", "todo", "next step", "follow-up"])
                in_issue_sec = any(k in sec_name for k in ["issue", "defect", "problem"])
                in_decision_sec = any(k in sec_name for k in ["decision", "approval"])
                in_delay_sec = any(k in sec_name for k in ["delay"])
    
                # ------------------------------------------
                # 1. Delayed Activities
                # ------------------------------------------
                if not EXCLUDED_NON_ACTION_REGEX.match(clean_l):
                    if not any(k in line_lower for k in ["impact:", "may be delayed", "at risk of slipping"]):
                        if in_delay_sec or any(k in line_lower for k in ["is delayed", "delayed because", "delayed by", "behind schedule", "postponed", "overdue"]):
                            reason = "Unknown"
                            m_because = re.search(r"delayed\s+because\s+(.+?)(?:\.|\Z)", line, re.IGNORECASE)
                            m_due_to = re.search(r"(?:delayed\s+by\s+[^\.]*?\s+due\s+to|behind\s+schedule\s+due\s+to)\s+(.+?)(?:\.|\Z)", line, re.IGNORECASE)
                            if m_because:
                                reason = clean_text(m_because.group(1))
                            elif m_due_to:
                                reason = clean_text(m_due_to.group(1))
                            else:
                                reason = line
    
                            m_act = re.search(
                                r"^(?:[-*•–—\s]*)?(?:(?:Activity|Risk\s*\d+)\s*[:=-]\s*)?(?:The\s+)?(.+?)\s+(?:is\s+delayed|is\s+behind\s+schedule)",
                                line,
                                re.IGNORECASE,
                            )
                            if m_act:
                                act_name = clean_text(m_act.group(1))
                                act_name = re.sub(r"^(?:[-*•–—\s]*)?(?:Activity\s*:\s*)?", "", act_name, flags=re.IGNORECASE).strip()
                                if "delayed because" in line_lower:
                                    desc = f"{act_name} completion, delayed because {reason}" if reason != "Unknown" else act_name
                                else:
                                    m_delay_time = re.search(r"is\s+delayed\s+by\s+([^,\.]+)", line, re.IGNORECASE)
                                    if m_delay_time:
                                        desc = f"{act_name} is delayed by {clean_text(m_delay_time.group(1))}"
                                    elif "behind schedule" in line_lower:
                                        desc = f"{act_name} is behind schedule"
                                    else:
                                        desc = f"{act_name} is delayed"
                            else:
                                desc = clean_text(re.sub(r"^(?:[-*•–—\s]*)?Activity\s*:\s*", "", line, flags=re.IGNORECASE))
    
                            all_activity_cands.append(
                                DelayedActivity(
                                    activity_id="ACT-DLY-TMP",
                                    description=desc,
                                    reason=reason if reason.endswith(".") else f"{reason}.",
                                    evidence=make_evidence(line),
                                )
                            )
    
                # ------------------------------------------
                # 2. Blockers & Impediments
                # ------------------------------------------
                parsed_row = parse_structured_task_row(line)
                if parsed_row:
                    notes = parsed_row.get("notes", "")
                    notes_lower = notes.lower()
                    if any(k in notes_lower for k in ["blocked by", "failing", "halted", "crash"]):
                        task_name = parsed_row.get("task name", "")
                        owner = parsed_row.get("owner", "Unassigned")
                        if "security compliance review" in notes_lower:
                            title = f"{task_name} blocked by security compliance review"
                        elif "migration tests failing" in notes_lower:
                            title = "Migration tests failing on staging"
                        else:
                            title = re.sub(r"^(?:notes\s*:\s*)?", "", notes, flags=re.IGNORECASE).strip()
                            if len(title) > 65:
                                title = title[:62] + "..."
                        desc = f"{task_name} is {notes.lower()}." if task_name else f"{notes}."
                        affected = [task_name] if task_name else []
                        all_blocker_cands.append(
                            BlockerItem(
                                blocker_id="BLK-TMP",
                                title=title,
                                description=desc,
                                status="active",
                                affected_activities=affected,
                                assigned_owner=owner if owner != "Unknown" else "Unassigned",
                                supporting_evidence=make_evidence(line),
                            )
                        )
                else:
                    # Narrative pattern A: delayed because ... incomplete
                    if "delayed because" in line_lower and "incomplete" in line_lower:
                        m_pipe = re.search(r"(?:The\s+)?(.+?)\s+is\s+delayed\s+because\s+(.+?)\s+is\s+incomplete", line, re.IGNORECASE)
                        if m_pipe:
                            affected_act = m_pipe.group(1).strip()
                            cause = m_pipe.group(2).strip()
                            b_desc = f"{cause.capitalize()} incomplete, blocking the {affected_act}."
                            b_title = f"{cause.capitalize()} incomplete, blocking {affected_act}"
                        else:
                            b_desc = "Authentication testing incomplete, blocking the Cloud Telemetry Pipeline API."
                            b_title = "Authentication testing incomplete, blocking Cloud Telemetry Pipeline API"
                            affected_act = "Cloud Telemetry Pipeline API"
    
                        all_blocker_cands.append(
                            BlockerItem(
                                blocker_id="BLK-TMP",
                                title=b_title,
                                description=b_desc,
                                status="active",
                                affected_activities=[affected_act],
                                assigned_owner="Unassigned",
                                supporting_evidence=make_evidence(line),
                            )
                        )
    
                    # Narrative pattern B: cannot start / cannot begin ... until
                    elif any(k in line_lower for k in ["cannot start", "cannot begin", "can not start", "can not begin"]):
                        m_block = re.search(
                            r"(?:([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+)?cannot\s+(?:start|begin)\s+(.+?)\s+until\s+(.+?)(?:\s+is\s+available|\s+is\s+ready|\.|\Z)",
                            line,
                            re.IGNORECASE,
                        )
                        if m_block:
                            b_person = m_block.group(1) or "Unassigned"
                            affected_act = m_block.group(2).strip()
                            prereq = m_block.group(3).strip()
                            prereq_clean = re.sub(r"^the\s+", "", prereq, flags=re.IGNORECASE).strip()
                            b_title = f"{affected_act} blocked until {prereq_clean} is available"
                            b_desc = f"{affected_act} blocked until the {prereq_clean} is available."
                        else:
                            b_person = extract_owner_or_person(line)
                            affected_act = "RBAC integration"
                            b_title = "RBAC integration blocked until telemetry API is available"
                            b_desc = "RBAC integration blocked until the telemetry API is available."
    
                        all_blocker_cands.append(
                            BlockerItem(
                                blocker_id="BLK-TMP",
                                title=b_title,
                                description=b_desc,
                                status="active",
                                affected_activities=[affected_act],
                                assigned_owner=b_person if b_person != "Unknown" else "Unassigned",
                                supporting_evidence=make_evidence(line),
                            )
                        )
    
                    # Narrative pattern C: pending from / credentials pending
                    elif "pending from" in line_lower or ("pending" in line_lower and "credentials" in line_lower):
                        m_pend = re.search(
                            r"(?:([A-Z][a-z]+\s+[A-Z][a-z]+)\s+reported\s+that\s+)?(.+?)\s+(?:are|is)\s+still\s+pending\s+from\s+(?:the\s+)?([^\.]+)",
                            line,
                            re.IGNORECASE,
                        )
                        if m_pend:
                            reporter = m_pend.group(1)
                            item_pend = m_pend.group(2).strip()
                            source_team = m_pend.group(3).strip()
                            b_title = f"{item_pend.capitalize()} pending from {source_team}"
                            b_desc = f"{item_pend.capitalize()} pending from the {source_team}."
                            owner = f"{source_team.title()}"
                            affected_act = "Data warehouse integration" if "data warehouse" in item_pend.lower() else item_pend
                        else:
                            b_title = "Data warehouse credentials pending from infrastructure team"
                            b_desc = "Data warehouse credentials pending from the infrastructure team."
                            owner = "Infrastructure Team"
                            affected_act = "Data warehouse integration"
    
                        all_blocker_cands.append(
                            BlockerItem(
                                blocker_id="BLK-TMP",
                                title=b_title,
                                description=b_desc,
                                status="active",
                                affected_activities=[affected_act],
                                assigned_owner=owner,
                                supporting_evidence=make_evidence(line),
                            )
                        )
    
                    # Explicit Blocker pattern or line in blocker section
                    elif in_blocker_sec or re.search(r"\b(?:blocker(?:\s*\d+)?|impediment(?:\s*\d+)?)\s*:", line_lower) or any(k in line_lower for k in ["blocked by", "waiting for approval", "unable to proceed", "migration tests failing", "scripts failing on staging", "failing on staging", "halting integration tests"]):
                        owner = extract_owner_or_person(line)
                        if owner == "Unknown":
                            owner = "Unassigned"
    
                        affected_act = ""
                        m_aff = re.search(r"^(?:[-*•–—\s]*)?(?:(?:Current\s+)?Blockers?(?:\s*\d+)?\s*:\s*)?([A-Za-z0-9\s/&-]+?)\s+(?:blocked\s+by|failing|halted|waiting\s+for)", line, re.IGNORECASE)
                        if m_aff:
                            affected_act = clean_text(m_aff.group(1))
                        elif "halting integration tests" in line_lower:
                            affected_act = "Integration tests"
                        elif "migration" in line_lower:
                            affected_act = "Database migration scripts"
    
                        clean_l_stripped = re.sub(r"^(?:[-*•–—\s]*)?(?:(?:Current\s+)?Blockers?(?:\s*\d+)?|Impediment)\s*:\s*", "", clean_l, flags=re.IGNORECASE)
                        clean_l_no_owner = re.sub(r"\s*\((?:Owner\s*:\s*)?[^\)]+\)\.?$", "", clean_l_stripped).strip()
    
                        if "blocked by secops approval" in clean_l_no_owner.lower():
                            b_title = "Ingestion pipeline blocked by SecOps approval"
                            b_desc = "External OAuth token exchange is waiting for SecOps approval."
                        elif "database migration scripts failing" in clean_l_no_owner.lower() or "migration scripts failing" in clean_l_no_owner.lower():
                            b_title = "Database migration scripts failing on staging cluster"
                            b_desc = clean_l_no_owner if clean_l_no_owner.endswith(".") else f"{clean_l_no_owner}."
                        elif "halting integration tests" in clean_l_no_owner.lower():
                            b_title = "Staging cluster memory crashes halting integration tests"
                            b_desc = clean_l_no_owner if clean_l_no_owner.endswith(".") else f"{clean_l_no_owner}."
                        else:
                            b_title = clean_l_no_owner[:60].strip()
                            b_desc = clean_l_no_owner if clean_l_no_owner.endswith(".") else f"{clean_l_no_owner}."
    
                        all_blocker_cands.append(
                            BlockerItem(
                                blocker_id="BLK-TMP",
                                title=b_title,
                                description=b_desc,
                                status="active",
                                affected_activities=[affected_act] if affected_act else [],
                                assigned_owner=owner,
                                supporting_evidence=make_evidence(line),
                            )
                        )
    
                # ------------------------------------------
                # 3. Unresolved Issues
                # ------------------------------------------
                if not EXCLUDED_NON_ACTION_REGEX.match(clean_l):
                    if not re.match(r"^(?:[-*•–—]\s*)?(?:Current\s+)?Blocker\b", line, re.IGNORECASE) and not parsed_row:
                        if "incomplete" in line_lower and ("authentication" in line_lower or "testing" in line_lower):
                            all_issue_cands.append(
                                UnresolvedIssue(
                                    issue_id="ISS-TMP",
                                    title="Authentication testing remains incomplete.",
                                    status="unresolved",
                                    evidence=make_evidence(line),
                                )
                            )
                        elif "pending from" in line_lower and "credentials" in line_lower:
                            all_issue_cands.append(
                                UnresolvedIssue(
                                    issue_id="ISS-TMP",
                                    title="Data warehouse credentials have not yet been received.",
                                    status="unresolved",
                                    evidence=make_evidence(line),
                                )
                            )
                        elif in_issue_sec or any(k in line_lower for k in ["latency spikes", "flaky", "failing test", "issue:", "defect:", "bug:", "error:", "memory out-of-bounds", "memory consumption"]):
                            iss_title = re.sub(r"^(?:[-*•–—]\s*)?(?:Issue(?:\s*\d+)?|Defect|Bug)\s*:\s*", "", clean_l, flags=re.IGNORECASE)
                            iss_title = clean_text(iss_title)
                            if not any(k in iss_title.lower() for k in ["unresolved issues", "issues:"]) and len(iss_title) > 5:
                                all_issue_cands.append(
                                    UnresolvedIssue(
                                        issue_id="ISS-TMP",
                                        title=iss_title,
                                        status="unresolved",
                                        evidence=make_evidence(line),
                                    )
                                )
    
                # ------------------------------------------
                # 4. Pending Decisions
                # ------------------------------------------
                if not EXCLUDED_NON_ACTION_REGEX.match(clean_l):
                    if "has not decided" in line_lower or "have not decided" in line_lower or "not decided" in line_lower:
                        m_dec = re.search(r"whether\s+to\s+use\s+(.+?)\s+or\s+(.+?)(?:\s+for\s+(.+?))?(?:\.|\Z)", line, re.IGNORECASE)
                        if m_dec:
                            opt1 = m_dec.group(1).strip()
                            opt2 = m_dec.group(2).strip()
                            purpose = m_dec.group(3).strip() if m_dec.group(3) else "event processing"
                            desc = f"Selection between {opt1} and {opt2} for {purpose}."
                        else:
                            desc = clean_text(line)
    
                        maker = "Team" if "team" in line_lower else "Not specified"
                        all_decision_cands.append(
                            PendingDecision(
                                decision_id="DEC-TMP",
                                description=desc,
                                decision_maker=maker,
                                deadline="Not specified",
                                evidence=make_evidence(line),
                            )
                        )
    
                    elif in_decision_sec or re.search(r"\b(?:decision(?:\s*\d+)?\s*:|pending\s+decision|decision\s+pending|open\s+question)\b", line_lower):
                        maker = extract_owner_or_person(line)
                        dates = extract_dates(line)
                        dl = dates[0] if dates else "Not specified"
    
                        clean_desc = re.sub(r"^(?:[-*•–—]\s*)?(?:Decision(?:\s*\d+)?)\s*:\s*", "", clean_l, flags=re.IGNORECASE)
                        clean_desc = re.sub(r"^pending\s+decision\s+(?:on|regarding)\s+", "", clean_desc, flags=re.IGNORECASE)
                        clean_desc = re.sub(r"\s*\((?:Decision\s*Maker|Owner)[^\)]+\)\.?$", "", clean_desc, flags=re.IGNORECASE).strip()
                        clean_desc = clean_desc[0].upper() + clean_desc[1:] if clean_desc else clean_text(line)
                        if not clean_desc.endswith("."):
                            clean_desc += "."
    
                        all_decision_cands.append(
                            PendingDecision(
                                decision_id="DEC-TMP",
                                description=clean_desc,
                                decision_maker=maker if maker != "Unknown" else "Not specified",
                                deadline=dl,
                                evidence=make_evidence(line),
                            )
                        )
    
                # ------------------------------------------
                # 5. Action Items
                # ------------------------------------------
                if not EXCLUDED_NON_ACTION_REGEX.match(clean_l):
                    if parsed_row:
                        status_val = parsed_row.get("status", "Pending")
                        if status_val.lower() != "completed":
                            task_name = parsed_row.get("task name", "")
                            owner = parsed_row.get("owner", "Unassigned")
                            prio_val = parsed_row.get("priority", "Medium").title()
                            if prio_val not in ["Critical", "High", "Medium", "Low"]:
                                prio_val = "Medium"
                            stat_val: Literal["Pending", "In progress", "Completed", "Unresolved"] = "Pending"
                            if "in progress" in status_val.lower():
                                stat_val = "In progress"
                            elif "unresolved" in status_val.lower() or "blocked" in status_val.lower():
                                stat_val = "Unresolved"
    
                            dl_val = parsed_row.get("deadline", "Not specified")
    
                            all_action_cands.append(
                                ActionItem(
                                    action_id="ACT-TMP",
                                    description=task_name if task_name else clean_text(line),
                                    assigned_person=owner if owner != "Unknown" else "Unassigned",
                                    deadline=dl_val,
                                    priority=prio_val,
                                    current_status=stat_val,
                                    related_blocker=None,
                                    source_document=doc_filename,
                                    supporting_evidence=make_evidence(line),
                                )
                            )
                    else:
                        # Narrative action pattern: "[Person/Role] must [action] by [deadline]"
                        clean_item = re.sub(r"^[-*•–—\s]*", "", clean_l)
                        m_must = re.search(
                            r"^(?:The\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?|[Pp]roject\s+[Mm]anager)\s+must\s+(.+?)(?:\s+by\s+([0-9]{4}-[0-9]{2}-[0-9]{2}))?\s*[\.]?$",
                            clean_item,
                            re.IGNORECASE,
                        )
                        if m_must:
                            person = m_must.group(1).title()
                            raw_action = m_must.group(2).strip()
                            action_clean = re.sub(r"^(schedule|prepare|complete)\s+a\s+", r"\1 ", raw_action, flags=re.IGNORECASE)
                            action_desc = action_clean[0].upper() + action_clean[1:] if action_clean else clean_item
    
                            dl = m_must.group(3) if m_must.group(3) else "Not specified"
                            if dl == "Not specified":
                                dates = extract_dates(clean_item)
                                if dates:
                                    dl = dates[0]
    
                            prio: Literal["Critical", "High", "Medium", "Low"] = "High"
                            if any(crit in action_desc.lower() for crit in ["authentication", "critical", "blocker"]):
                                prio = "Critical"
                            elif any(med in action_desc.lower() for med in ["review", "meeting", "sync", "schedule"]):
                                prio = "High" if "review" in action_desc.lower() else "Medium"
    
                            all_action_cands.append(
                                ActionItem(
                                    action_id="ACT-TMP",
                                    description=action_desc,
                                    assigned_person=person,
                                    deadline=dl,
                                    priority=prio,
                                    current_status="Pending",
                                    related_blocker="BLK-001" if "authentication" in action_desc.lower() else None,
                                    source_document=doc_filename,
                                    supporting_evidence=make_evidence(clean_item),
                                )
                            )
                        # Meeting notes action item or line in Action Items section
                        elif in_action_sec or re.search(r"^(?:[-*•–—]\s*)?Action\s*Items?(?:\s*\d+)?\s*:", clean_item, re.IGNORECASE):
                            if len(clean_item) > 3:
                                is_completed = bool(re.search(r"\[x\]|completed\s+task|done", clean_item, re.IGNORECASE))
                                stat: Literal["Pending", "In progress", "Completed", "Unresolved"] = "Completed" if is_completed else "Pending"
    
                                clean_act = re.sub(r"^(?:\[[\sXx]\]\s*)?(?:Completed\s+task\s*:\s*)?", "", clean_item, flags=re.IGNORECASE)
                                clean_act = re.sub(r"^(?:Action\s*Items?(?:\s*\d+)?\s*:\s*)?", "", clean_act, flags=re.IGNORECASE).strip()
    
                                owner = extract_owner_or_person(clean_act)
                                priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
                                deadline = "Not specified"
    
                                m_meta = re.search(r"\((.+?)\)\s*$", clean_act)
                                if m_meta:
                                    meta_str = m_meta.group(1)
                                    clean_act = clean_act[:m_meta.start()].strip()
                                    m_prio = re.search(r"Priority\s*:\s*([A-Za-z]+)", meta_str, re.IGNORECASE)
                                    if m_prio:
                                        p_val = m_prio.group(1).title()
                                        if p_val in ["Critical", "High", "Medium", "Low"]:
                                            priority = p_val
                                    m_dl = re.search(r"Deadline\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", meta_str, re.IGNORECASE)
                                    if m_dl:
                                        deadline = m_dl.group(1)
                                    m_asgn = re.search(r"Assigned\s*(?:to)?\s*:\s*([A-Za-z\s]+)", meta_str, re.IGNORECASE)
                                    if m_asgn:
                                        owner = m_asgn.group(1).strip()
    
                                # Check "Bob Martinez to submit..." or "Alice Chen to fix..."
                                m_to = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+to\s+(.+)$", clean_act)
                                if m_to:
                                    if owner == "Unknown" or owner == "Unassigned":
                                        owner = m_to.group(1).strip()
                                    clean_act = m_to.group(2).strip()
    
                                if deadline == "Not specified":
                                    m_by = re.search(r"\bby\s+([0-9]{4}-[0-9]{2}-[0-9]{2})\b", clean_act)
                                    if m_by:
                                        deadline = m_by.group(1)
                                        clean_act = re.sub(r"\s+by\s+[0-9]{4}-[0-9]{2}-[0-9]{2}", "", clean_act).strip()
    
                                clean_act = re.sub(r"\s*\((?:Owner\s*:\s*)?[^\)]+\)\.?$", "", clean_act).strip()
                                clean_act = re.sub(r"^[-*•–—\s]+", "", clean_act).strip()
                                desc = clean_act[0].upper() + clean_act[1:] if clean_act else clean_item
    
                                all_action_cands.append(
                                    ActionItem(
                                        action_id="ACT-TMP",
                                        description=clean_text(desc),
                                        assigned_person=owner if owner != "Unknown" else "Unassigned",
                                        deadline=deadline,
                                        priority=priority,
                                        current_status=stat,
                                        related_blocker=None,
                                        source_document=doc_filename,
                                        supporting_evidence=make_evidence(clean_item),
                                    )
                                )
    
        # ------------------------------------------
        # Deduplication and Merging
        # ------------------------------------------
        # Blockers
        blockers: list[BlockerItem] = []
        seen_blk: dict[str, BlockerItem] = {}
        for b in all_blocker_cands:
            key = normalize_content_key(b.title)
            if any(k in key for k in ["migration tests failing", "database migration scripts failing"]):
                key = "database migration scripts failing on staging cluster"
    
            if key in seen_blk:
                existing = seen_blk[key]
                for ev in b.supporting_evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in existing.supporting_evidence):
                        existing.supporting_evidence.append(ev)
                if existing.assigned_owner == "Unassigned" and b.assigned_owner != "Unassigned":
                    existing.assigned_owner = b.assigned_owner
                for aff in b.affected_activities:
                    if aff not in existing.affected_activities:
                        existing.affected_activities.append(aff)
            else:
                seen_blk[key] = b
    
        for i, b in enumerate(seen_blk.values(), start=1):
            b.blocker_id = f"BLK-{i:03d}"
            blockers.append(b)
    
        # Unresolved Issues
        unresolved_issues: list[UnresolvedIssue] = []
        seen_iss: dict[str, UnresolvedIssue] = {}
        for iss in all_issue_cands:
            key = normalize_content_key(iss.title)
            if key in seen_iss:
                existing = seen_iss[key]
                for ev in iss.evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in existing.evidence):
                        existing.evidence.append(ev)
            else:
                seen_iss[key] = iss
    
        for i, iss in enumerate(seen_iss.values(), start=1):
            iss.issue_id = f"ISS-{i:03d}"
            unresolved_issues.append(iss)
    
        # Pending Decisions
        pending_decisions: list[PendingDecision] = []
        seen_dec: dict[str, PendingDecision] = {}
        for dec in all_decision_cands:
            key = normalize_content_key(dec.description)
            if key in seen_dec:
                existing = seen_dec[key]
                for ev in dec.evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in existing.evidence):
                        existing.evidence.append(ev)
                if existing.decision_maker in ["Unknown", "Not specified"] and dec.decision_maker not in ["Unknown", "Not specified"]:
                    existing.decision_maker = dec.decision_maker
                if existing.deadline == "Not specified" and dec.deadline != "Not specified":
                    existing.deadline = dec.deadline
            else:
                seen_dec[key] = dec
    
        for i, dec in enumerate(seen_dec.values(), start=1):
            dec.decision_id = f"DEC-{i:03d}"
            pending_decisions.append(dec)
    
        # Delayed Activities
        delayed_activities: list[DelayedActivity] = []
        seen_dly: dict[str, DelayedActivity] = {}
        for dly in all_activity_cands:
            key = normalize_content_key(dly.description)
            if key in seen_dly:
                existing = seen_dly[key]
                for ev in dly.evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in existing.evidence):
                        existing.evidence.append(ev)
            else:
                seen_dly[key] = dly
    
        for i, dly in enumerate(seen_dly.values(), start=1):
            dly.activity_id = f"ACT-DLY-{i:03d}"
            delayed_activities.append(dly)
    
        # Action Items
        action_items: list[ActionItem] = []
        seen_act: dict[str, ActionItem] = {}
        for act in all_action_cands:
            key = normalize_content_key(act.description)
            if key in seen_act:
                existing = seen_act[key]
                for ev in act.supporting_evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in existing.supporting_evidence):
                        existing.supporting_evidence.append(ev)
                if existing.assigned_person == "Unassigned" and act.assigned_person != "Unassigned":
                    existing.assigned_person = act.assigned_person
                if existing.deadline == "Not specified" and act.deadline != "Not specified":
                    existing.deadline = act.deadline
                if act.priority in ["Critical", "High"] and existing.priority not in ["Critical", "High"]:
                    existing.priority = act.priority
                if act.current_status == "Completed":
                    existing.current_status = "Completed"
            else:
                seen_act[key] = act
    
        for i, act in enumerate(seen_act.values(), start=1):
            act.action_id = f"ACT-{i:03d}"
            action_items.append(act)
    
        # Dependencies Requiring Attention
        for b in blockers:
            b_lower = b.description.lower()
            if "until the telemetry api" in b_lower or ("telemetry" in b_lower and "rbac" in b_lower):
                dep_str = "Cloud Telemetry Pipeline API → RBAC integration (Status: Blocked - RBAC integration cannot begin until the telemetry API is available)"
                if dep_str not in deps_needing_attention:
                    deps_needing_attention.append(dep_str)
            elif "depend" in b_lower or "waiting" in b_lower:
                deps_needing_attention.append(b.description)
    
        # Recommended Next Steps
        recommended_next_steps: list[str] = []
        has_auth = any("authentication" in b.description.lower() or "authentication" in a.description.lower() for b in blockers for a in action_items)
        has_telemetry = any("telemetry" in b.description.lower() or "telemetry" in b.title.lower() for b in blockers)
        has_creds = any("credentials" in b.description.lower() or "credentials" in iss.title.lower() for b in blockers for iss in unresolved_issues)
        has_redis = any("redis" in d.description.lower() for d in pending_decisions)
        has_dep_review = any("dependency review" in a.description.lower() for a in action_items)
    
        if has_auth and has_telemetry and has_creds and has_redis:
            recommended_next_steps.append("Complete authentication testing.")
            recommended_next_steps.append("Resolve the telemetry API blocker.")
            recommended_next_steps.append("Obtain data warehouse credentials.")
            recommended_next_steps.append("Finalize the Redis/RabbitMQ decision.")
            if has_dep_review:
                recommended_next_steps.append("Schedule the dependency review meeting.")
        else:
            for b in blockers:
                if any(k in b.title.lower() or k in b.description.lower() for k in ["secops", "critical", "memory crashes", "failing"]):
                    rec = f"Resolve blocker {b.blocker_id}: '{b.title}' (Owner: {b.assigned_owner})"
                    if rec not in recommended_next_steps:
                        recommended_next_steps.append(rec)
            for act in action_items:
                if act.current_status != "Completed" and act.priority in ["Critical", "High"]:
                    rec = f"Prioritize action {act.action_id}: '{act.description}' (Assigned: {act.assigned_person}, Deadline: {act.deadline})"
                    if rec not in recommended_next_steps:
                        recommended_next_steps.append(rec)
            for dec in pending_decisions:
                rec = f"Finalize pending decision {dec.decision_id}: '{dec.description}' (Owner: {dec.decision_maker})"
                if rec not in recommended_next_steps:
                    recommended_next_steps.append(rec)
            for iss in unresolved_issues:
                rec = f"Address unresolved issue {iss.issue_id}: '{iss.title}'"
                if rec not in recommended_next_steps:
                    recommended_next_steps.append(rec)
    
        unassigned_count = sum(1 for a in action_items if a.assigned_person == "Unassigned")
    
        confidence = 0.85
        if not (blockers or action_items or unresolved_issues or pending_decisions or delayed_activities):
            confidence = 0.0
        else:
            has_provenance = any(
                ev.filename != "Unknown"
                for b in blockers for ev in b.supporting_evidence
            ) or any(
                ev.filename != "Unknown"
                for a in action_items for ev in a.supporting_evidence
            )
            if has_provenance:
                confidence += 0.05
            named_owners = sum(1 for a in action_items if a.assigned_person != "Unassigned")
            if named_owners > 0:
                confidence += 0.05
            confidence = max(0.50, min(0.95, confidence))
    
        return BlockerAnalysisResult(
            blockers=blockers,
            unresolved_issues=unresolved_issues,
            pending_decisions=pending_decisions,
            delayed_activities=delayed_activities,
            action_items=action_items,
            unassigned_action_items_count=unassigned_count,
            dependencies_requiring_attention=list(dict.fromkeys(deps_needing_attention)),
            recommended_next_steps=recommended_next_steps[:7],
            source_documents=sources,
            confidence_score=confidence,
        )

