"""Scope and Deliverable Extraction Agent.

Extracts project title, objectives, scope boundaries (in-scope / out-of-scope),
deliverables, milestones, timeline dates, and team responsibilities.
Strictly adheres to anti-hallucination rules: never fabricates dates or owners;
missing information is marked as Unknown or Not specified.
"""

import re
from typing import Any

from app.agents.agent_utils import (
    DocumentChunkContext,
    EXCLUDED_PERSON_TOKENS,
    clean_text,
    extract_dates,
    extract_evidence_snippet,
    extract_owner_or_person,
    split_into_section_blocks,
)
from app.models.agent_models import (
    DeadlineItem,
    DeliverableItem,
    MilestoneItem,
    ScopeAnalysisResult,
    SourceEvidence,
    TeamResponsibility,
)
from app.services.rag_pipeline import RAGPipelineService

STOP_HEADER_REGEX = (
    r"(?:[\r\n]+\s*|\.\s+)(?:\d+[\.\)]\s+)?(?:Objectives?|Goals?|Scope(?:\s+Boundaries)?|In-Scope|Out-of-Scope|"
    r"Expected\s+Deliverables?|Key\s+Deliverables?|Deliverables?(?:\s+to\s+be\s+produced)?|"
    r"Milestones?(?:\s*\d+)?|M\d+|Timeline|Important\s+Deadlines?|Deadlines?|"
    r"Team\s*Responsibilities?|Responsibilities?|Team|Risks?|Blockers?|"
    r"Pending\s+Deliverables?|Pending\s+Deliverable|Pending|"
    r"Budget|Financial|Governance|Approvals?)(?:\s*[:=-]|\s+(?:are|include|covers|to\s+be\s+produced\s+are)\b|(?=\s*[\r\n]))"
)


class ScopeAgent:
    """Agent specializing in Project Scope, Deliverables, and Milestone Extraction."""

    def __init__(self, rag_service: RAGPipelineService | None = None) -> None:
        self.rag_service = rag_service

    def analyze(
        self,
        text: str | None = None,
        query: str | None = None,
        top_k: int = 10,
        filename: str = "Unknown",
        document_id: str | None = None,
    ) -> ScopeAnalysisResult:
        """Run scope and deliverable analysis on given text or via RAG retrieval."""
        sources: list[str] = []
        evidence_snippets: list[SourceEvidence] = []
        combined_text = ""

        chunks: list[DocumentChunkContext] = []

        # Case 1: Direct text provided
        if text and text.strip():
            combined_text = text.strip()
            sources.append(filename)
            chunks.append(
                DocumentChunkContext(
                    text=combined_text,
                    filename=filename,
                    document_id=document_id,
                )
            )
            evidence_snippets.append(
                extract_evidence_snippet(
                    combined_text,
                    window_chars=120,
                    filename=filename,
                    document_id=document_id,
                )
            )
        # Case 2: Use RAG pipeline
        elif self.rag_service:
            search_query = (
                query
                or "project title objectives scope deliverables milestones deadlines team responsibilities"
            )
            results = self.rag_service.search(search_query, top_k=top_k)
            if results:
                text_segments: list[str] = []
                for res in results:
                    src_file = str(res.metadata.get("filename", "Unknown"))
                    if src_file not in sources:
                        sources.append(src_file)
                    text_segments.append(res.text)
                    chunks.append(
                        DocumentChunkContext(
                            text=res.text,
                            filename=src_file,
                            document_id=res.document_id,
                            chunk_id=res.chunk_id,
                            confidence=max(0.5, min(0.99, res.similarity)),
                        )
                    )
                    evidence_snippets.append(
                        extract_evidence_snippet(
                            res.text,
                            window_chars=120,
                            filename=src_file,
                            document_id=res.document_id,
                            chunk_id=res.chunk_id,
                            confidence=max(0.5, min(0.99, res.similarity)),
                        )
                    )
                combined_text = "\n\n".join(text_segments)

        if not combined_text.strip():
            return ScopeAnalysisResult(
                project_title="Unknown",
                start_date="Not specified",
                end_date="Not specified",
                confidence_score=0.0,
                source_documents=sources,
                evidence_snippets=evidence_snippets,
            )

        return self._extract_scope_details(
            combined_text,
            sources,
            evidence_snippets,
            default_doc_id=document_id,
            chunk_contexts=chunks,
        )

    def _extract_scope_details(
        self,
        text: str,
        sources: list[str],
        evidence_snippets: list[SourceEvidence],
        default_doc_id: str | None = None,
        chunk_contexts: list[DocumentChunkContext] | None = None,
    ) -> ScopeAnalysisResult:
        primary_source = sources[0] if sources else "Unknown"

        # 1. Project Title (concise, never full paragraph)
        project_title = self._extract_project_title(text)

        # 2. Section Blocks
        sections = split_into_section_blocks(text)

        # 3. Objectives & Goals
        objectives, goals = self._extract_objectives_and_goals(text, sections)

        # 4. Scope: In-Scope vs Out-of-Scope
        in_scope, out_of_scope = self._extract_scope_boundaries(text, sections)

        # 5. Timeline: Start & End Dates
        start_date, end_date = self._extract_timeline_dates(text)

        # 6. Expected Deliverables
        deliverables = self._extract_deliverables(
            text, sections, primary_source, default_doc_id, chunk_contexts=chunk_contexts
        )

        # 7. Milestones
        milestones = self._extract_milestones(
            text, sections, primary_source, default_doc_id, chunk_contexts=chunk_contexts
        )

        # 8. Important Deadlines
        important_deadlines = self._extract_deadlines(
            text, primary_source, default_doc_id, chunk_contexts=chunk_contexts
        )

        # 9. Team Responsibilities & Assigned Owners
        team_responsibilities, assigned_owners = self._extract_team_responsibilities(
            text, sections, primary_source, default_doc_id, chunk_contexts=chunk_contexts
        )

        # 10. Correlate owners from team responsibilities to deliverables if missing
        self._correlate_owners_and_deliverables(
            deliverables, team_responsibilities, assigned_owners
        )

        # 11. Collect any valid owners from deliverables and milestones
        for d in deliverables:
            if d.owner != "Unknown" and d.owner not in assigned_owners and d.owner.lower() not in EXCLUDED_PERSON_TOKENS:
                assigned_owners.append(d.owner)
        for m in milestones:
            if m.owner != "Unknown" and m.owner not in assigned_owners and m.owner.lower() not in EXCLUDED_PERSON_TOKENS:
                assigned_owners.append(m.owner)

        # 12. Pending Deliverables extracted separately from explicit evidence
        pending_deliverables = self._extract_pending_deliverables(
            text, sections, deliverables
        )

        # Calculate calibrated confidence score
        has_title = project_title != "Unknown"
        has_obj = len(objectives) > 0
        has_del = len(deliverables) > 0
        has_mls = len(milestones) > 0
        signals_present = sum([has_title, has_obj, has_del, has_mls])

        if signals_present >= 3:
            confidence = 0.95 if signals_present == 4 else 0.88
        elif signals_present == 2:
            confidence = 0.75
        elif signals_present == 1:
            confidence = 0.50
        else:
            confidence = 0.30

        return ScopeAnalysisResult(
            project_title=project_title,
            objectives=list(dict.fromkeys(objectives)),
            in_scope=list(dict.fromkeys(in_scope)),
            out_of_scope=list(dict.fromkeys(out_of_scope)),
            goals=list(dict.fromkeys(goals)),
            expected_deliverables=deliverables,
            milestones=milestones,
            start_date=start_date,
            end_date=end_date,
            important_deadlines=important_deadlines,
            team_responsibilities=team_responsibilities,
            assigned_owners=list(dict.fromkeys(assigned_owners)),
            pending_deliverables=list(dict.fromkeys(pending_deliverables)),
            confidence_score=confidence,
            source_documents=sources,
            evidence_snippets=evidence_snippets,
        )

    def _extract_project_title(self, text: str) -> str:
        """Extract only the project title without capturing entire paragraphs or descriptive text."""
        # 1. Explicit label pattern: Project Title: ..., Project Name: ..., Project: ...
        m = re.search(
            r"(?:Project\s+Title|Project\s+Name|Project)\s*[:=-]\s*([^\n\r]+)",
            text,
            re.IGNORECASE,
        )
        if m:
            raw = m.group(1).strip()
            # Stop before any next inline section keyword
            raw = re.split(
                r"\b(?:Objective|Scope|Deliverable|Milestone|Timeline|Team|Goal)s?\s*[:=-]",
                raw,
                flags=re.IGNORECASE,
            )[0].strip()
            # Stop before descriptive sentence verbs
            raw = re.split(
                r"\s+(?:aims\s+to|is\s+aimed\s+at|is\s+an?\s+|focuses\s+on|will\s+deliver|is\s+to)\b",
                raw,
                flags=re.IGNORECASE,
            )[0].strip()
            raw = raw.rstrip(".,;")
            if 3 < len(raw) <= 70 and not raw.lower().startswith(("objective", "scope", "goal", "deliverable")):
                return raw

        # 2. Markdown top-level header: "# Title"
        m_md = re.search(r"^#\s+([^\n\r]+)", text, re.MULTILINE)
        if m_md:
            cand = m_md.group(1).strip()
            cand = re.sub(
                r"^(?:Project\s+Title|Project\s+Name|Project)\s*[:=-]\s*",
                "",
                cand,
                flags=re.IGNORECASE,
            ).strip()
            if 3 < len(cand) <= 70 and not any(k in cand.lower() for k in ["sprint", "meeting", "update"]):
                return cand

        # 3. Unstructured text: Look for capitalized name ending with standard project suffixes
        # e.g. "The Enterprise Cloud Analytics Platform (ECAP) initiative aims to..."
        m_ent = re.search(
            r"\b([A-Z][A-Za-z0-9/& -]+(?:Platform|Engine|System|Gateway|Dashboard|Pipeline|Service|Hub|Portal|Advisor|Tool|Application)(?:\s*\([A-Z0-9-]+\))?)",
            text,
        )
        if m_ent:
            cand = m_ent.group(1).strip()
            cand = re.sub(r"^(?:The|An|A)\s+", "", cand)
            if 3 < len(cand) <= 70 and not any(
                w in cand.lower()
                for w in ["objective", "milestone", "deadline", "responsibility", "we will", "is to", "aims to"]
            ):
                return cand

        # 4. Fallback to first line ONLY IF it's short, capitalized, and looks like a title
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            first = re.sub(r"^#+\s*", "", lines[0]).strip()
            if (
                3 < len(first) <= 60
                and not first.endswith(".")
                and not any(
                    k in first.lower()
                    for k in [
                        "sprint", "meeting", "update", "notes", "aims", "objective",
                        "deliverable", "scope", "the goal", "this project"
                    ]
                )
            ):
                return first

        return "Unknown"

    def _extract_objectives_and_goals(
        self, text: str, sections: dict[str, list[str]]
    ) -> tuple[list[str], list[str]]:
        """Extract individual objectives and goals, ensuring no concatenated text from other sections."""
        objectives: list[str] = []
        goals: list[str] = []

        # 1. Section block scan
        obj_lines: list[str] = []
        for sec_name, lines in sections.items():
            if "objective" in sec_name:
                obj_lines.extend(lines)
            elif "goal" in sec_name:
                goals.extend(lines)

        for l in obj_lines:
            l_clean = clean_text(l)
            if l_clean.lower().strip(":") in {"objectives", "objective", "project objectives"}:
                continue
            # Stop if line has crossed into another section
            if any(k in l_clean.lower() for k in ["scope:", "deliverables:", "milestones:", "team responsibilities:"]):
                l_clean = re.split(r"\b(?:Scope|Deliverables?|Milestones?|Team)\s*[:=-]", l_clean, flags=re.IGNORECASE)[0].strip()

            sentences = [s.strip() for s in re.split(r"\.\s+(?=[A-Z])", l_clean) if s.strip()]
            for s in sentences:
                s = re.sub(r"^(?:The\s+)?objective\s+(?:is\s+)?to\s+", "", s, flags=re.IGNORECASE)
                s = re.sub(r"^To\s+", "", s, flags=re.IGNORECASE)
                s = s.rstrip(".,;")
                if len(s) > 5 and not any(k in s.lower() for k in ["scope:", "deliverable:", "milestone:"]):
                    objectives.append(s)

        # 2. Targeted regex for Objectives block when not split by lines
        if not objectives:
            m_obj = re.search(
                r"\b(?:Objectives?|Purpose)\s*[:=-]\s*(.+?)(?=(?:" + STOP_HEADER_REGEX + r"|\Z))",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if m_obj:
                raw_block = m_obj.group(1).strip()
                items = re.split(r"[\r\n]+|;\s*|(?:\s|^)[-*•–—]\s+|\b\d+[\.\)]\s*", raw_block)
                for it in items:
                    it = it.strip()
                    if not it:
                        continue
                    sentences = [s.strip() for s in re.split(r"\.\s+(?=[A-Z])", it) if s.strip()]
                    for s in sentences:
                        s = re.sub(r"^(?:The\s+)?objective\s+(?:is\s+)?to\s+", "", s, flags=re.IGNORECASE)
                        s = re.sub(r"^To\s+", "", s, flags=re.IGNORECASE)
                        s = s.rstrip(".,;")
                        if len(s) > 5 and not any(k in s.lower() for k in ["scope:", "deliverable:", "milestone:"]):
                            objectives.append(s)

        # 3. Fallback for conversational / unstructured text
        if not objectives:
            unstruct_matches = re.finditer(
                r"\b(?:aims\s+to|objective\s+is\s+to|goal\s+is\s+to|purpose\s+is\s+to)\s+([^;\.\n]+)",
                text,
                re.IGNORECASE,
            )
            for um in unstruct_matches:
                cand = um.group(1).strip()
                if " and achieve " in cand:
                    parts = cand.split(" and achieve ")
                    objectives.append(parts[0].strip().capitalize())
                    objectives.append("Achieve " + parts[1].strip())
                else:
                    objectives.append(cand.capitalize())

        # Clean Goals
        cleaned_goals: list[str] = []
        for g in goals:
            g_clean = clean_text(g).rstrip(".,;")
            if g_clean and len(g_clean) > 5 and g_clean.lower().strip(":") not in {"goals", "goal", "project goals"}:
                cleaned_goals.append(g_clean)

        return list(dict.fromkeys(objectives)), list(dict.fromkeys(cleaned_goals))

    def _extract_scope_boundaries(
        self, text: str, sections: dict[str, list[str]]
    ) -> tuple[list[str], list[str]]:
        """Extract In-Scope and Out-of-Scope boundaries from section blocks or inline text."""
        in_scope: list[str] = []
        out_of_scope: list[str] = []

        stop_in = (
            r"(?:[\r\n]+\s*|\.\s+|\s+)(?:Out-of-Scope|Out\s+of\s+Scope|Excluded|"
            r"Expected\s+Deliverables?|Deliverables?|Milestones?|Timeline)\s*[:=-]"
        )
        stop_out = (
            r"(?:[\r\n]+\s*|\.\s+|\s+)(?:In-Scope|In\s+Scope|"
            r"Expected\s+Deliverables?|Deliverables?|Milestones?|Timeline|Team)\s*[:=-]"
        )

        # 1. Regex for In-Scope block in text
        m_in = re.search(
            r"\b(?:In-Scope|In\s+Scope)\s*[:=-]\s*(.+?)(?=(?:" + stop_in + r"|\Z))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if m_in:
            raw_in = m_in.group(1).strip()
            items = re.split(
                r"[\r\n]+|;\s*|(?<=[^A-Z]),\s*(?:and\s+)?|(?:\s|^)[-*•–—]\s+",
                raw_in,
            )
            for it in items:
                it = re.sub(r"^[-*•–—]\s*", "", it).strip().rstrip(".,;")
                if len(it) > 3 and not any(k in it.lower() for k in ["out of scope", "out-of-scope", "deliverable:", "milestone:"]):
                    in_scope.append(it)

        # 2. Regex for Out-of-Scope block in text
        m_out = re.search(
            r"\b(?:Out-of-Scope|Out\s+of\s+Scope|Excluded\s*(?:from\s*scope)?)\s*[:=-]\s*(.+?)(?=(?:" + stop_out + r"|\Z))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if m_out:
            raw_out = m_out.group(1).strip()
            items = re.split(
                r"[\r\n]+|;\s*|(?<=[^A-Z]),\s*(?:and\s+)?|(?:\s|^)[-*•–—]\s+",
                raw_out,
            )
            for it in items:
                it = re.sub(r"^[-*•–—]\s*", "", it).strip().rstrip(".,;")
                if len(it) > 3 and not any(k in it.lower() for k in ["in scope", "in-scope", "deliverable:", "milestone:"]):
                    out_of_scope.append(it)

        # 3. Section block scan if not already found
        if not in_scope:
            for sec_name, lines in sections.items():
                if "in-scope" in sec_name or "in scope" in sec_name:
                    for l in lines:
                        it = clean_text(l).strip(".,;")
                        if it and len(it) > 3 and it.lower() not in {"in-scope", "in scope"}:
                            in_scope.append(it)

        if not out_of_scope:
            for sec_name, lines in sections.items():
                if "out-of-scope" in sec_name or "out of scope" in sec_name:
                    for l in lines:
                        it = clean_text(l).strip(".,;")
                        if it and len(it) > 3 and it.lower() not in {"out-of-scope", "out of scope"}:
                            out_of_scope.append(it)

        # 4. Unstructured / conversational text fallback
        if not in_scope:
            m_scope = re.search(
                r"\b(?:Scope\s+(?:covers|includes|is)|The\s+scope\s+includes)\s+([^;\.\n]+?)(?:,\s*while|\.\s*|\Z)",
                text,
                re.IGNORECASE,
            )
            if m_scope:
                raw_items = m_scope.group(1).strip()
                items = re.split(r",\s*(?:and\s+)?|\s+and\s+", raw_items)
                for it in items:
                    it = it.strip().rstrip(".,;")
                    if len(it) > 3:
                        in_scope.append(it)

        if not out_of_scope:
            m_out_unstruct = re.search(
                r"(?:while|whereas|also|\.)\s+([^;\.\n]+?)\s+(?:are|is)\s+out\s+of\s+scope",
                text,
                re.IGNORECASE,
            )
            if m_out_unstruct:
                raw_items = m_out_unstruct.group(1).strip()
                if "while" in raw_items.lower():
                    raw_items = re.split(r"\bwhile\s+", raw_items, flags=re.IGNORECASE)[-1]
                items = re.split(r",\s*(?:and\s+)?|\s+and\s+", raw_items)
                for it in items:
                    it = it.strip().rstrip(".,;")
                    if len(it) > 3:
                        out_of_scope.append(it)

        return list(dict.fromkeys(in_scope)), list(dict.fromkeys(out_of_scope))

    def _extract_timeline_dates(self, text: str) -> tuple[str, str]:
        """Extract confirmed start date and target end date."""
        start_date = "Not specified"
        end_date = "Not specified"

        start_match = re.search(
            r"(?:start\s*date|commencement|kick-?off)\s*(?:is|on|[:=-])\s*([A-Za-z0-9\s,\.-]+?)(?=[;\n\.]|\s+and\s+target|$)",
            text,
            re.IGNORECASE,
        )
        if start_match:
            candidate = start_match.group(1).strip()
            dates = extract_dates(candidate)
            start_date = dates[0] if dates else candidate

        end_match = re.search(
            r"(?:end\s*date|completion\s*date|target\s*completion|target\s*end\s*date|launch\s*date)\s*(?:is|on|[:=-])\s*([A-Za-z0-9\s,\.-]+?)(?=[;\n\.]|$)",
            text,
            re.IGNORECASE,
        )
        if end_match:
            candidate = end_match.group(1).strip()
            dates = extract_dates(candidate)
            end_date = dates[0] if dates else candidate

        return start_date, end_date

    def _extract_deliverables(
        self,
        text: str,
        sections: dict[str, list[str]],
        filename: str,
        document_id: str | None,
        chunk_contexts: list[DocumentChunkContext] | None = None,
    ) -> list[DeliverableItem]:
        """Extract individual deliverables including multi-item comma lists and section bullet points.
        Never splits hyphenated compound names (e.g. Real-Time Dashboard) or treat them as owners.
        """
        deliverables: list[DeliverableItem] = []
        candidates: list[str] = []
        counter = 1

        # 1. Section block lines (excluding pending deliverable sections)
        deliv_lines: list[str] = []
        for sec_name, lines in sections.items():
            if "deliverable" in sec_name and "pending" not in sec_name:
                for l in lines:
                    clean_l = clean_text(l)
                    if re.match(r"^[-*•–—\s]*(?:Milestone\s*\d*|M\d+)\b", clean_l, re.IGNORECASE):
                        continue
                    if clean_l.lower().strip(":") not in {
                        "expected deliverables", "deliverables", "deliverable", "key deliverables",
                        "key expected deliverables", "key expected deliverables and milestones"
                    } and not clean_l.lower().startswith("pending deliverable"):
                        deliv_lines.append(clean_l)

        # 2. Check CSV rows
        csv_row_matches = re.findall(
            r"Row\s+\d+:\s*(.*?)(?=(?:Row\s+\d+:|$))", text, re.DOTALL
        )
        for row in csv_row_matches:
            if "deliverable" in row.lower() or "task" in row.lower():
                deliv_lines.append(row.strip())

        # If section lines exist, split list items
        if deliv_lines:
            for line in deliv_lines:
                if ("," in line or " and " in line) and not line.lower().startswith("row "):
                    sub_items = re.split(
                        r",\s*(?![^()]*\))(?:\s*and\s+)?|(?<=[^,])\s+and\s+(?![^()]*\))|;\s*",
                        line,
                    )
                    for sit in sub_items:
                        sit = sit.strip()
                        if sit:
                            candidates.append(sit)
                else:
                    candidates.append(line)
        else:
            # 3. Targeted regex for Deliverables block in text
            m_del = re.search(
                r"\b(?:\d+[\.\)]\s+)?(?:Expected\s+Deliverables?|Key\s+Deliverables?|Deliverables?\s*(?:to\s+be\s+produced)?)\s*(?:are|include|[:=-]|\band\s+milestones\b|\bto\b)?\s*(.+?)(?=(?:" + STOP_HEADER_REGEX + r"|\Z))",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if m_del:
                raw_block = m_del.group(1).strip()
                raw_clean = re.sub(
                    r"^(?:to\s+be\s+produced\s+are|include|are)\s+",
                    "",
                    raw_block,
                    flags=re.IGNORECASE,
                )
                items = re.split(
                    r",\s*(?![^()]*\))(?:\s*and\s+)?|(?<=[^,])\s+and\s+(?![^()]*\))|[\r\n]+|;\s*|\b\d+[\.\)]\s*",
                    raw_clean,
                )
                for it in items:
                    it = it.strip()
                    if it and len(it) > 3 and not it.lower().strip(":") in {
                        "expected deliverables", "deliverables", "deliverable"
                    }:
                        candidates.append(it)

        # Process each deliverable candidate
        seen_names: set[str] = set()
        for cand in candidates:
            cand_clean = re.sub(r"^[-*•–—\s]*", "", cand).strip()
            if re.match(r"^(?:Milestone\s*\d*|M\d+)\b", cand_clean, re.IGNORECASE):
                continue
            cand_clean = re.sub(
                r"^(?:Deliverable\s*\d*|Task\s*\d*)\s*[:=-]\s*",
                "",
                cand_clean,
                flags=re.IGNORECASE,
            ).strip()
            cand_clean = re.sub(r"^(?:and\s+)", "", cand_clean, flags=re.IGNORECASE).strip()

            raw_owner = extract_owner_or_person(cand_clean)
            owner = raw_owner if raw_owner.lower() not in EXCLUDED_PERSON_TOKENS else "Unknown"
            dates = extract_dates(cand_clean)
            deadline = dates[0] if dates else "Not specified"

            # Distinguish statuses: only mark pending if explicitly stated in evidence
            low = cand_clean.lower()
            if any(w in low for w in ["completed", "done", "delivered"]):
                status = "completed"
            elif any(w in low for w in ["in progress", "active", "in-progress"]):
                status = "in_progress"
            elif "status: pending" in low or "is pending" in low or "(pending)" in low or low.endswith(" pending"):
                status = "pending"
            else:
                status = "unknown"

            name = re.sub(r"\s*\([^)]*\)", "", cand_clean).strip()
            name = re.sub(
                r"\s+(?:due\s*(?:on|by)?|deadline|status)\s+[^\n,;]+",
                "",
                name,
                flags=re.IGNORECASE,
            ).strip()
            name = re.sub(r"^(?:and\s+)", "", name, flags=re.IGNORECASE).strip()
            name = name.rstrip(".,;")

            if "Task: " in name or "Deliverable: " in name:
                m_csv = re.search(r"(?:Deliverable|Task)\s*[:=-]\s*([^;\|\n]+)", name, re.IGNORECASE)
                if m_csv:
                    name = m_csv.group(1).strip()

            norm_key = name.lower()
            if (
                len(name) > 3
                and norm_key not in seen_names
                and not any(k in norm_key for k in ["milestone", "target date", "timeline", "team responsibilities", "pending deliverable"])
            ):
                seen_names.add(norm_key)
                src_f, d_id, c_id, conf = filename, document_id, None, 0.85
                if chunk_contexts:
                    c_low = cand.lower()
                    for ctx in chunk_contexts:
                        if c_low in ctx.text.lower() or any(w in ctx.text.lower() for w in c_low.split()[:4]):
                            src_f = ctx.filename
                            d_id = ctx.document_id or document_id
                            c_id = ctx.chunk_id
                            conf = ctx.confidence
                            break
                evidence = [
                    extract_evidence_snippet(cand, filename=src_f, document_id=d_id, chunk_id=c_id, confidence=conf)
                ]
                item = DeliverableItem(
                    deliverable_id=f"DEL-{counter:03d}",
                    name=name,
                    description=cand if len(cand) > len(name) else None,
                    owner=owner,
                    deadline=deadline,
                    status=status,
                    evidence=evidence,
                )
                deliverables.append(item)
                counter += 1

        return deliverables

    def _extract_pending_deliverables(
        self,
        text: str,
        sections: dict[str, list[str]],
        deliverables: list[DeliverableItem],
    ) -> list[str]:
        """Extract pending deliverables explicitly mentioned in pending sections or explicitly marked pending."""
        pending_items: list[str] = []

        # 1. Section blocks matching 'pending'
        for sec_name, lines in sections.items():
            if "pending" in sec_name:
                for l in lines:
                    clean_l = clean_text(l)
                    if clean_l.lower().strip(":") in {
                        "pending deliverable", "pending deliverables", "pending", "pending items"
                    }:
                        continue
                    parts = re.split(
                        r",\s*(?![^()]*\))(?:\s*and\s+)?|(?<=[^,])\s+and\s+(?![^()]*\))|;\s*",
                        clean_l,
                    )
                    for p in parts:
                        p = re.sub(r"^[-*•–—\s]*", "", p).strip().rstrip(".,;")
                        p = re.sub(r"^(?:and\s+)", "", p, flags=re.IGNORECASE).strip().rstrip(".,;")
                        if p and len(p) > 2 and p not in pending_items:
                            pending_items.append(p)

        # 2. Targeted regex for Pending Deliverables line or block in text
        m_pend = re.search(
            r"\b(?:Pending\s+Deliverables?|Pending\s+Items?)\s*[:=-]\s*(.+?)(?=(?:"
            + STOP_HEADER_REGEX
            + r"|\Z))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if m_pend:
            raw_block = m_pend.group(1).strip()
            for l in raw_block.splitlines():
                parts = re.split(
                    r",\s*(?![^()]*\))(?:\s*and\s+)?|(?<=[^,])\s+and\s+(?![^()]*\))|;\s*",
                    l,
                )
                for p in parts:
                    p = re.sub(r"^[-*•–—\s]*", "", p).strip().rstrip(".,;")
                    p = re.sub(r"^(?:and\s+)", "", p, flags=re.IGNORECASE).strip().rstrip(".,;")
                    if p and len(p) > 2 and p not in pending_items:
                        pending_items.append(p)

        # 3. Add deliverables whose status is explicitly marked as 'pending'
        for d in deliverables:
            if d.status == "pending" and d.name not in pending_items:
                pending_items.append(d.name)

        return list(dict.fromkeys(pending_items))

    def _extract_milestones(
        self,
        text: str,
        sections: dict[str, list[str]],
        filename: str,
        document_id: str | None,
        chunk_contexts: list[DocumentChunkContext] | None = None,
    ) -> list[MilestoneItem]:
        """Extract individual milestones, ensuring multiple milestones are never concatenated together."""
        milestones: list[MilestoneItem] = []
        counter = 1

        pattern = r"\b(?:Milestone\s*\d+|M\d+)\b"
        matches = list(re.finditer(pattern, text, re.IGNORECASE))

        if matches:
            for i, match in enumerate(matches):
                start = match.start()
                if i + 1 < len(matches):
                    end = matches[i + 1].start()
                else:
                    remaining = text[start:]
                    stop_m = re.search(STOP_HEADER_REGEX, remaining, re.IGNORECASE)
                    end = start + stop_m.start() if stop_m else len(text)

                raw_m = text[start:end].strip()
                if "\n" in raw_m:
                    raw_m = raw_m.splitlines()[0].strip()
                raw_m = re.sub(r"[,;\s]+and\s*$", "", raw_m, flags=re.IGNORECASE).rstrip(".,;")

                owner = extract_owner_or_person(raw_m)
                dates = extract_dates(raw_m)
                target_date = dates[0] if dates else "Not specified"

                status = "pending"
                low = raw_m.lower()
                if any(w in low for w in ["completed", "done", "passed"]):
                    status = "completed"
                elif any(w in low for w in ["in progress", "active"]):
                    status = "in_progress"
                elif any(w in low for w in ["delayed", "at risk"]):
                    status = "delayed"

                name = re.sub(r"\s*\([^)]*\)", "", raw_m).strip()
                name = re.sub(
                    r"\s+(?:due\s*(?:on|by)?|target\s*date\s*[:=-]?|target)\s+[^\n,;]+",
                    "",
                    name,
                    flags=re.IGNORECASE,
                ).strip()
                name = re.sub(r"\s*[-–—:]\s*$", "", name).strip()
                name = name.rstrip(".,;")

                src_f, d_id, c_id, conf = filename, document_id, None, 0.85
                if chunk_contexts:
                    m_low = raw_m.lower()
                    for ctx in chunk_contexts:
                        if m_low in ctx.text.lower() or any(w in ctx.text.lower() for w in m_low.split()[:4]):
                            src_f = ctx.filename
                            d_id = ctx.document_id or document_id
                            c_id = ctx.chunk_id
                            conf = ctx.confidence
                            break
                evidence = [
                    extract_evidence_snippet(raw_m, filename=src_f, document_id=d_id, chunk_id=c_id, confidence=conf)
                ]
                milestones.append(
                    MilestoneItem(
                        milestone_id=f"MLS-{counter:03d}",
                        name=name,
                        target_date=target_date,
                        owner=owner,
                        status=status,
                        deliverables=[],
                        evidence=evidence,
                    )
                )
                counter += 1
        else:
            sec_lines: list[str] = []
            for sec_name, lines in sections.items():
                if "milestone" in sec_name:
                    for l in lines:
                        clean_l = clean_text(l)
                        if re.match(r"^[-*•–—\s]*(?:Deliverable\s*\d*|Task\s*\d*)\b", clean_l, re.IGNORECASE):
                            continue
                        if clean_l.lower().strip(":") not in {
                            "milestone", "milestones", "project milestones",
                            "key expected deliverables and milestones"
                        }:
                            sec_lines.append(clean_l)

            for cand in sec_lines:
                cand_clean = re.sub(r"^[-*•–—\s]*", "", cand).strip()
                if re.match(r"^(?:Deliverable\s*\d*|Task\s*\d*)\b", cand_clean, re.IGNORECASE):
                    continue
                owner = extract_owner_or_person(cand_clean)
                dates = extract_dates(cand_clean)
                target_date = dates[0] if dates else "Not specified"
                name = re.sub(r"^(?:Milestone\s*\d*|M\d+)\s*[:=-]\s*", "", cand_clean, flags=re.IGNORECASE).strip()
                name = re.sub(r"\s*\([^)]*\)", "", name).strip()
                name = re.sub(r"\s+(?:target\s*date|due|owner|status)\s+[^\n,;]+", "", name, flags=re.IGNORECASE).strip()
                name = name.rstrip(".,;")
                if not name:
                    name = cand_clean
                src_f, d_id, c_id, conf = filename, document_id, None, 0.85
                if chunk_contexts:
                    c_low = cand.lower()
                    for ctx in chunk_contexts:
                        if c_low in ctx.text.lower() or any(w in ctx.text.lower() for w in c_low.split()[:4]):
                            src_f = ctx.filename
                            d_id = ctx.document_id or document_id
                            c_id = ctx.chunk_id
                            conf = ctx.confidence
                            break
                evidence = [
                    extract_evidence_snippet(cand, filename=src_f, document_id=d_id, chunk_id=c_id, confidence=conf)
                ]
                milestones.append(
                    MilestoneItem(
                        milestone_id=f"MLS-{counter:03d}",
                        name=name,
                        target_date=target_date,
                        owner=owner,
                        status="pending",
                        deliverables=[],
                        evidence=evidence,
                    )
                )
                counter += 1

        return milestones

    def _extract_deadlines(
        self,
        text: str,
        filename: str,
        document_id: str | None,
        chunk_contexts: list[DocumentChunkContext] | None = None,
    ) -> list[DeadlineItem]:
        """Extract important deadlines with clean titles, dates, and owners."""
        deadlines: list[DeadlineItem] = []
        lines = text.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if re.search(r"\b(?:deadline|due\s*date|target\s*date|is\s+due)\b", line_str, re.IGNORECASE):
                dates = extract_dates(line_str)
                if dates:
                    title_match = re.search(
                        r"^(?:[-*•–—]\s*)?([A-Za-z0-9\s/_-]{3,50}?)(?:\s+(?:deadline|due\s*date|target\s*date|is\s+due)|[:=-])",
                        line_str,
                        re.IGNORECASE,
                    )
                    title = title_match.group(1).strip() if title_match else clean_text(line_str[:40])
                    owner = extract_owner_or_person(line_str)
                    clean_title = f"{title} Deadline" if "deadline" not in title.lower() else title

                    src_f, d_id, c_id, conf = filename, document_id, None, 0.85
                    if chunk_contexts:
                        l_low = line_str.lower()
                        for ctx in chunk_contexts:
                            if l_low in ctx.text.lower() or any(w in ctx.text.lower() for w in l_low.split()[:4]):
                                src_f = ctx.filename
                                d_id = ctx.document_id or document_id
                                c_id = ctx.chunk_id
                                conf = ctx.confidence
                                break

                    deadlines.append(
                        DeadlineItem(
                            title=clean_title,
                            date=dates[0],
                            owner=owner,
                            evidence=[
                                extract_evidence_snippet(line_str, filename=src_f, document_id=d_id, chunk_id=c_id, confidence=conf)
                            ],
                        )
                    )
        return deadlines

    def _extract_team_responsibilities(
        self,
        text: str,
        sections: dict[str, list[str]],
        filename: str,
        document_id: str | None,
        chunk_contexts: list[DocumentChunkContext] | None = None,
    ) -> tuple[list[TeamResponsibility], list[str]]:
        """Extract team responsibilities supporting verbs ('owns', 'leads', 'is responsible for')
        and delimiters ('–', '—', ':', ' - '). Never splits hyphenated names or treats words like Real as owners.
        """
        responsibilities: list[TeamResponsibility] = []
        assigned_owners: list[str] = []
        candidate_items: list[str] = []

        def _split_resp_line(l: str) -> list[str]:
            if "\n" in l:
                return [x.strip() for x in l.splitlines() if x.strip()]
            if ";" in l:
                return [x.strip() for x in l.split(";") if x.strip()]
            split_pattern = (
                r",\s*(?:and\s+)?(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:owns|leads|is\s+responsible|[-–—:=]))"
                r"|(?<=[^,])\s+and\s+(?=[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:owns|leads|is\s+responsible|[-–—:=]))"
                r"|\.\s+(?=[A-Z][a-zA-Z\s]+:)"
            )
            parts = re.split(split_pattern, l)
            if len(parts) > 1:
                return [p.strip() for p in parts if p.strip()]
            return [l.strip()]

        # 1. Section block scan
        sec_lines: list[str] = []
        for sec_name, lines in sections.items():
            if any(k in sec_name for k in ["responsibility", "team", "roles", "governance"]):
                for l in lines:
                    clean_l = clean_text(l)
                    if clean_l.lower().strip(":") not in {
                        "team responsibilities", "responsibilities", "team", "project governance and approvals"
                    }:
                        sec_lines.append(clean_l)

        if sec_lines:
            for line in sec_lines:
                candidate_items.extend(_split_resp_line(line))
        else:
            # 2. Targeted regex for Team Responsibilities block
            m_sec = re.search(
                r"\b(?:Team\s+Responsibilities?|Responsibilities?|Team\s+Roles?)\s*[:=-]\s*(.+?)(?=(?:" + STOP_HEADER_REGEX + r"|\Z))",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if m_sec:
                raw_block = m_sec.group(1).strip()
                candidate_items.extend(_split_resp_line(raw_block))

        # Parse candidates
        seen_pairs: set[tuple[str, str]] = set()
        for item in candidate_items:
            clean_item = re.sub(r"^[-*•–—\s]*", "", item).strip()
            clean_item = re.sub(r"^(?:and\s+)", "", clean_item, flags=re.IGNORECASE).strip()

            person: str | None = None
            task: str | None = None

            # Pattern A: Verb pattern (Person owns ..., Person leads ..., Person is responsible for ...)
            m_verb = re.match(
                r"^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+(?:owns|leads|is\s+responsible\s+for|handles|manages)\s+(.+)$",
                clean_item,
                re.IGNORECASE,
            )
            if m_verb:
                person = m_verb.group(1).strip()
                task = m_verb.group(2).strip().rstrip(".,;")
                task = re.sub(r"^(?:the|a|an)\s+", "", task, flags=re.IGNORECASE).strip()

            # Pattern B: Delimiter pattern (Person – Task, Person: Task, Person - Task with spaces)
            if not person:
                m_delim = re.match(
                    r"^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s+[-–—]\s+|\s*[–—:]\s*)(.+)$",
                    clean_item,
                )
                if m_delim:
                    g1 = m_delim.group(1).strip()
                    g2 = m_delim.group(2).strip().rstrip(".,;")
                    g2_clean = re.sub(r"^(?:the|a|an)\s+", "", g2, flags=re.IGNORECASE).strip()
                    role_indicators = {"lead", "manager", "head", "architect", "engineer", "director", "owner", "sponsor"}
                    if any(w in g1.lower().split() for w in role_indicators) and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$", g2_clean):
                        person = g2_clean
                        task = g1
                    else:
                        person = g1
                        task = g2_clean

            # Pattern C: Generic Role: Person or Responsibility
            if not person:
                m_role = re.match(
                    r"^([A-Za-z\s\(\)]+)(?:\s+[-–—]\s+|\s*[–—:]\s*)(.+)$",
                    clean_item,
                )
                if m_role:
                    role = m_role.group(1).strip()
                    resp = m_role.group(2).strip().rstrip(".,;")
                    if role.lower() not in EXCLUDED_PERSON_TOKENS:
                        person = role
                        task = resp

            if person and task:
                if person.lower() in EXCLUDED_PERSON_TOKENS or len(person.split()) > 3:
                    continue
                pair_key = (person.lower(), task.lower())
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    src_f, d_id, c_id, conf = filename, document_id, None, 0.85
                    if chunk_contexts:
                        i_low = item.lower()
                        for ctx in chunk_contexts:
                            if i_low in ctx.text.lower() or any(w in ctx.text.lower() for w in i_low.split()[:4]):
                                src_f = ctx.filename
                                d_id = ctx.document_id or document_id
                                c_id = ctx.chunk_id
                                conf = ctx.confidence
                                break
                    evidence = [
                        extract_evidence_snippet(item, filename=src_f, document_id=d_id, chunk_id=c_id, confidence=conf)
                    ]
                    responsibilities.append(
                        TeamResponsibility(
                            role_or_person=person,
                            responsibility=task,
                            evidence=evidence,
                        )
                    )
                    if person not in assigned_owners:
                        assigned_owners.append(person)

        # 3. Text-wide fallback if responsibilities list is still empty
        if not responsibilities:
            for m in re.finditer(
                r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:owns|leads|is\s+responsible\s+for)\s+([^;\.\n]+)",
                text,
                re.IGNORECASE,
            ):
                cand_person = m.group(1).strip()
                cand_task = m.group(2).strip().rstrip(".,;")
                cand_task = re.sub(r"^(?:the|a|an)\s+", "", cand_task, flags=re.IGNORECASE).strip()
                if cand_person.lower() not in EXCLUDED_PERSON_TOKENS and len(cand_person.split()) <= 3:
                    pair_key = (cand_person.lower(), cand_task.lower())
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        evidence = [
                            extract_evidence_snippet(text, m.span(), filename=filename, document_id=document_id)
                        ]
                        responsibilities.append(
                            TeamResponsibility(
                                role_or_person=cand_person,
                                responsibility=cand_task,
                                evidence=evidence,
                            )
                        )
                        if cand_person not in assigned_owners:
                            assigned_owners.append(cand_person)

            for m in re.finditer(
                r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+[-–—]\s+|\s*[–—]\s*)([A-Z][A-Za-z0-9\s/&]+)",
                text,
            ):
                cand_person = m.group(1).strip()
                cand_task = m.group(2).strip().rstrip(".,;")
                if cand_person.lower() not in EXCLUDED_PERSON_TOKENS and len(cand_person.split()) <= 3:
                    pair_key = (cand_person.lower(), cand_task.lower())
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        evidence = [
                            extract_evidence_snippet(text, m.span(), filename=filename, document_id=document_id)
                        ]
                        responsibilities.append(
                            TeamResponsibility(
                                role_or_person=cand_person,
                                responsibility=cand_task,
                                evidence=evidence,
                            )
                        )
                        if cand_person not in assigned_owners:
                            assigned_owners.append(cand_person)

        return responsibilities, assigned_owners

    def _correlate_owners_and_deliverables(
        self,
        deliverables: list[DeliverableItem],
        responsibilities: list[TeamResponsibility],
        assigned_owners: list[str],
    ) -> None:
        """Map assigned owners from team responsibilities to deliverables when owner is unknown."""
        stopwords = {"the", "a", "an", "and", "or", "for", "to", "in", "of", "with"}
        for d in deliverables:
            if d.owner == "Unknown":
                d_name = d.name.lower()
                tokens_d = {
                    w for w in re.findall(r"[a-z0-9]+", d_name)
                    if w not in stopwords and len(w) > 2
                }
                for r in responsibilities:
                    r_person = r.role_or_person
                    r_task = r.responsibility.lower()
                    tokens_r = {
                        w for w in re.findall(r"[a-z0-9]+", r_task)
                        if w not in stopwords and len(w) > 2
                    }
                    is_match = d_name in r_task or r_task in d_name
                    if not is_match:
                        common = tokens_d & tokens_r
                        if (
                            len(common) >= 2
                            or (
                                common
                                and len(tokens_d) <= 2
                                and len(common) / max(1, min(len(tokens_d), len(tokens_r))) >= 0.5
                            )
                            or (
                                common
                                and any(k in common for k in ["telemetry", "rbac", "dashboard", "warehouse"])
                            )
                        ):
                            is_match = True

                    if is_match:
                        d.owner = r_person
                        if r_person not in assigned_owners and r_person.lower() not in EXCLUDED_PERSON_TOKENS:
                            assigned_owners.append(r_person)
                        break
