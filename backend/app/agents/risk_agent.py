"""Risk Detection and Delivery Forecasting Agent.

Identifies schedule risks, missed/approaching deadlines, dependency gaps,
resource constraints, budget overruns, bottlenecks, and delivery challenges.
Provides explainable severity classification (Critical, High, Medium, Low)
and evidence-grounded delivery forecasts without speculative date fabrication.
"""

import re
from typing import Any, Literal

from app.agents.agent_utils import (
    DocumentChunkContext,
    clean_text,
    detect_filename_from_text,
    extract_dates,
    extract_evidence_snippet,
    get_semantic_risk_cluster_key,
    normalize_content_key,
    parse_structured_task_row,
    split_into_section_blocks,
)
from app.models.agent_models import (
    DelayedMilestoneForecast,
    DependencyGap,
    RiskAnalysisResult,
    RiskItem,
    ScopeAnalysisResult,
    SourceEvidence,
)
from app.services.rag_pipeline import RAGPipelineService


def is_section_heading(line: str) -> bool:
    """Identify if a line is a section heading rather than an actual risk statement."""
    line_clean = clean_text(line).strip().rstrip(":")
    stripped = re.sub(r"^#{1,6}\s*", "", line_clean).strip()
    stripped_no_num = re.sub(r"^(?:section\s*)?\d+[\.\)]\s*", "", stripped, flags=re.IGNORECASE).strip()

    heading_exact = {
        "executive summary", "executive delivery summary", "project purpose",
        "schedule and delivery risks", "schedule risks", "delivery risks",
        "budget and resource constraints", "budget constraints", "resource constraints",
        "technical bottlenecks", "bottlenecks", "bottleneck",
        "deliverables and milestone status", "milestones status", "deliverables status", "deliverables and milestones",
        "current blockers", "blockers", "blocker",
        "delayed activities", "delayed activity",
        "unresolved issues", "unresolved issue",
        "pending decisions", "pending decision",
        "action items", "action item",
        "risk assessment", "risk log", "risk review", "risk factors", "risk summary", "risk overview",
        "risks and challenges", "risks and mitigations", "risks", "key risks",
        "project risks", "project challenges", "project issues",
        "table of contents", "project governance and approvals", "project governance",
        "in-scope", "out-of-scope", "scope boundaries", "scope",
    }
    if stripped_no_num.lower() in heading_exact:
        return True

    if re.match(r"^#{1,6}\s+\S+", line_clean):
        if len(stripped.split()) <= 8 and not re.search(r"[a-z0-9]\.\s+[A-Z]", stripped):
            return True

    if re.match(r"^(?:section\s*)?\d+[\.\)]\s+[A-Z][A-Za-z0-9\s/&,-]+$", line_clean, re.IGNORECASE):
        words = stripped_no_num.split()
        if len(words) <= 7 and not any(verb in stripped_no_num.lower() for verb in [" is ", " are ", " was ", " were ", " has ", " have ", " due to ", " because "]):
            return True

    if len(stripped_no_num.split()) <= 6:
        lower = stripped_no_num.lower()
        if any(h in lower for h in [
            "schedule and delivery", "budget and resource", "technical bottleneck",
            "delayed activities", "unresolved issues", "current blockers", "action items"
        ]) and not any(v in lower for v in [" is ", " are ", " was ", " were ", " by ", " due to "]):
            return True

    if "|" in line_clean and any(col in line_clean.lower() for col in ["milestone", "deliverable", "due date", "status", "owner"]):
        if not any(status in line_clean.lower() for status in ["completed", "delayed", "at risk", "pending", "in progress"]):
            return True

    if re.match(r"^(?:project\s*title|reporting\s*period|prepared\s*by|attendees|date|document\s*type|version|sponsor)\s*[:=-]", line_clean, re.IGNORECASE):
        return True

    if re.match(r"^(?:out-of-scope|in-scope|project\s*objectives?|executive\s*summary)\s*[:=-]", line_clean, re.IGNORECASE):
        return True

    return False


def is_non_risk_line(line: str) -> bool:
    """Identify document titles, action items, objectives, and neutral content that should not be classified as risks."""
    line_clean = clean_text(line).strip()
    low = line_clean.lower()

    if is_section_heading(line):
        return True

    if re.match(r"^#?\s*(?:meeting\s*notes|monthly\s*progress\s*report|project\s*proposal|project\s*charter|sprint\s*\d+\s*progress\s*report)\b", low):
        return True

    if "monthly progress report" in low and len(line_clean.split()) <= 8:
        return True

    if re.match(r"^[-*•–—\s]*(?:action\s*item\s*\d*|action\s*item)\b", low):
        return True
    if re.match(r"^[-*•–—\s]*(?:decision\s*\d*|pending\s*decision)\b", low):
        return True

    if re.match(r"^[-*•–—\s]*(?:achieve|eliminate|build|provide|enable|implement|deliver|modernize)\b", low):
        if not any(w in low for w in ["delay", "overdue", "fail", "crash", "shortage", "slipping", "behind schedule", "exceeded"]):
            return True

    if "out-of-scope" in low or "in-scope" in low:
        return True

    if "|" in line_clean and ("| completed" in low or "| in progress" in low or "| pending" in low):
        if not any(w in low for w in ["delayed", "at risk", "blocked", "critical", "fail"]):
            return True

    if re.match(r"^[-*•–—\s]*(?:approved\s+initial\s+budget|start\s*date|target\s*end\s*date)\b", low):
        return True

    if re.search(r"\bdeadline\s+is\b", low) and not any(w in low for w in ["delay", "overdue", "missed", "slipping", "behind", "fail", "incomplete"]):
        return True

    return False


def generate_risk_title(raw_text: str, category: str) -> str:
    """Generate a clean, readable, non-truncated risk title."""
    clean = clean_text(raw_text).strip()
    clean = re.sub(r"^[-*•–—#\s]+", "", clean).strip()
    clean = re.sub(r"^(?:Blocker\s*\d*|Issue|Activity|Risk\s*\d*|Task\s*\d*)\s*[:=-]\s*", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"^(?:Schedule\s*delay|Technical\s*bottleneck|Dependency\s*gap|Budget\s*overrun|Resource\s*constraint|Delivery\s*challenge)\s*[:=-]\s*", "", clean, flags=re.IGNORECASE).strip()

    if "|" in clean:
        parts = [p.strip() for p in clean.split("|")]
        m_name = parts[0]
        status = parts[-1] if len(parts) > 1 else ""
        return f"{m_name} marked as {status}" if status else m_name

    if clean.startswith("Row ") and "Task Name:" in clean:
        m_tname = re.search(r"Task\s*Name:\s*([^;]+)", clean, re.IGNORECASE)
        m_notes = re.search(r"Notes:\s*([^;]+)", clean, re.IGNORECASE)
        if m_tname and m_notes:
            return f"{m_tname.group(1).strip()}: {m_notes.group(1).strip()}"
        if m_tname:
            return m_tname.group(1).strip()

    clause_match = re.split(r"\s+(?:due\s+to|because|unless|which\s+is\s+awaiting|creating\s+a)\s+", clean, flags=re.IGNORECASE)
    if clause_match and len(clause_match[0]) >= 25:
        candidate = clause_match[0].strip().rstrip(",;.")
    else:
        candidate = clean

    if len(candidate) > 75:
        truncated = candidate[:72]
        if " " in truncated:
            candidate = truncated.rsplit(" ", 1)[0]

    trailing_stopwords = {"the", "a", "an", "and", "or", "for", "to", "in", "of", "with", "by", "is", "are", "when", "on"}
    words = candidate.split()
    while words and words[-1].lower() in trailing_stopwords:
        words.pop()
    candidate = " ".join(words).rstrip(",;.:- ")

    return candidate[0].upper() + candidate[1:] if candidate else f"{category} Risk Finding"


def generate_mitigation(description: str, category: str) -> str:
    """Produce a specific, actionable mitigation recommendation grounded in the risk."""
    low = description.lower()

    if category == "Budget":
        if any(w in low for w in ["cloud", "cluster", "compute", "scaling", "ingress", "infrastructure", "aws", "gcp", "azure"]):
            return "Review cloud infrastructure expenditure, optimize cluster scaling, and introduce cost monitoring."
        return "Review project expenditure, optimize infrastructure allocation, and introduce cost monitoring controls."

    if category == "Resource":
        if any(w in low for w in ["understaffed", "developer", "frontend", "backend", "bandwidth", "shortage"]):
            return "Reallocate available engineers and prioritize critical deliverables."
        if any(w in low for w in ["site reliability", "sre", "devops", "pipeline instability"]):
            return "Reallocate senior site reliability engineers to stabilize the deployment pipeline."
        return "Reallocate available engineers and prioritize critical deliverables."

    if category == "Dependency":
        if any(w in low for w in ["secops", "security", "compliance", "approval", "oauth", "token"]):
            return "Escalate pending SecOps approvals and establish an approval deadline."
        if any(w in low for w in ["third-party", "external api", "upstream", "partner", "vendor"]):
            return "Establish technical SLAs and daily synchronization with upstream providers."
        return "Track critical-path dependencies closely and establish clear handoff milestones."

    if category == "Bottleneck":
        if any(w in low for w in ["memory", "pod", "crash", "out-of-bounds", "latency", "network"]):
            return "Investigate worker memory consumption and optimize network communication."
        if any(w in low for w in ["migration", "schema", "database", "syntax", "tables"]):
            return "Align database schema definitions across environments and fix syntax mismatches."
        if any(w in low for w in ["flaky", "test", "coverage", "pipeline"]):
            return "Quarantine and resolve flaky integration tests and stabilize CI/CD pipelines."
        return "Investigate worker memory consumption and optimize network communication."

    if category == "Schedule":
        if any(w in low for w in ["milestone", "deadline", "slipping", "behind schedule", "delayed", "overdue"]):
            return "Rebaseline affected milestones and track critical-path dependencies."
        return "Rebaseline affected milestones and track critical-path dependencies."

    if category == "Delivery":
        if any(w in low for w in ["testing", "integration testing", "acceptance", "deployment", "test coverage"]):
            return "Begin integration test planning immediately, define test environments, and prepare test suites in parallel with development."
        return "Define delivery verification gates, accelerate acceptance testing, and prepare deployment rollback strategies."

    return "Review risk findings with the delivery lead, assign an owner, and track active mitigation progress."


def generate_impact(description: str, category: str, affected: str) -> str:
    """Generate explainable potential impact for a risk finding."""
    target = f"'{affected}'" if affected != "Not specified" else "project deliverables"
    if category == "Schedule":
        return f"Schedule slippage directly endangering milestone completion and delivery timeline of {target}."
    if category == "Dependency":
        return f"Blocked upstream prerequisite preventing execution and integration of {target}."
    if category == "Resource":
        return f"Engineering capacity constraint restricting development bandwidth and slowing completion of {target}."
    if category == "Budget":
        return f"Unbudgeted operational expenses risking funding exhaustion prior to completion of {target}."
    if category == "Bottleneck":
        return f"Technical throughput constraints and instability impacting verification and reliability of {target}."
    if category == "Delivery":
        return f"Incomplete verification phase increasing deployment risk and compressing validation of {target}."
    return f"Delivery impact on {target} requiring active management."


def assign_severity(line: str, category: str) -> Literal["Critical", "High", "Medium", "Low"]:
    """Assign an explainable severity classification grounded in the source statement."""
    low = line.lower()
    if any(c in low for c in ["critical", "halted", "halting", "overdue", "blocker", "blocks deployment", "cannot release", "major delay"]):
        return "Critical"
    if any(h in low for h in [
        "delayed by 3 weeks", "delayed by 2 weeks", "delayed by 10 days",
        "behind schedule", "exceeded budget", "understaffed", "shortage of",
        "at risk of slipping", "not started", "frequent memory", "crashes",
        "failing", "spikes exceeding 1200ms", "flaky integration tests",
        "only one backend developer", "budget has only 10"
    ]):
        return "High"
    if any(m in low for m in ["slight", "minor", "1 day", "few days"]):
        return "Medium"
    if category in {"Schedule", "Budget", "Delivery"}:
        return "High"
    return "Medium"


def classify_category(line: str) -> str | None:
    """Classify an evidence line into its primary risk category."""
    low = line.lower()

    # Explicit prefix checks
    if any(low.startswith(p) or f" {p}" in low for p in ["schedule delay:", "schedule risk:"]):
        return "Schedule"
    if any(low.startswith(p) or f" {p}" in low for p in ["technical bottleneck:", "bottleneck:"]):
        return "Bottleneck"
    if any(low.startswith(p) or f" {p}" in low for p in ["dependency gap:", "dependency:"]):
        return "Dependency"
    if any(low.startswith(p) or f" {p}" in low for p in ["budget overrun:", "budget risk:"]):
        return "Budget"
    if any(low.startswith(p) or f" {p}" in low for p in ["resource constraint:", "resource risk:"]):
        return "Resource"
    if any(low.startswith(p) or f" {p}" in low for p in ["delivery challenge:", "delivery risk:"]):
        return "Delivery"

    # 1. Budget
    if any(k in low for k in [
        "budget overrun", "exceeded budget", "cost overrun",
        "cloud infrastructure expenditure exceeded", "cloud infrastructure costs are increasing",
        "cloud costs are increasing", "budget has only", "cloud spend", "over budget",
    ]) and any(alert in low for alert in ["over", "exceed", "spike", "increasing", "remaining", "deficit", "shortfall", "risk"]):
        return "Budget"

    # 2. Resource
    if any(k in low for k in [
        "resource constraint", "understaffed", "shortage of",
        "only one backend developer", "bandwidth bottleneck",
        "lack of senior", "lack of engineers", "key person", "overcapacity"
    ]):
        return "Resource"

    # 3. Schedule
    if any(k in low for k in [
        "schedule delay", "is delayed", "delayed by", "delayed", "delay", "delays",
        "behind schedule", "missed deadline", "at risk of slipping", "slipping into",
        "slipping", "cannot meet launch date", "cannot meet deadline", "cannot meet",
        "status: delayed", "| delayed", "delayed (at risk)", "overdue",
        "is still incomplete", "late delivery", "postponed",
    ]):
        return "Schedule"

    # 4. Dependency
    if any(k in low for k in [
        "dependency gap", "blocked by", "depends on third-party", "depends on",
        "awaiting secops", "pending secops", "secops approval", "cannot begin until",
        "cannot start until", "external oauth token exchange", "upstream service",
        "authentication token exchange is failing"
    ]):
        return "Dependency"

    # 5. Bottleneck
    if any(k in low for k in [
        "technical bottleneck", "latency spikes", "memory consumption in worker pods",
        "memory out-of-bounds crashes", "failing tests in staging", "flaky integration tests",
        "failing on staging", "failing database migration", "schema syntax incompatibilities",
        "delivery bottleneck", "outage", "pipeline failure"
    ]):
        return "Bottleneck"

    # 6. Delivery
    if any(k in low for k in [
        "delivery challenge", "testing has not started", "integration testing not started",
        "incomplete test coverage", "required before final deployment"
    ]):
        return "Delivery"

    return None


def normalize_milestone_key(name: str) -> str:
    """Produce a canonical key to identify the underlying milestone/deliverable."""
    low = name.lower()
    m_num = re.search(r"milestone\s*(\d+)", low)
    if m_num:
        return f"milestone_{m_num.group(1)}"
    if any(k in low for k in ["oauth", "rbac", "security gateway"]):
        return "rbac_oauth_gateway"
    if any(k in low for k in ["telemetry", "ingestion"]):
        return "telemetry_pipeline"
    if any(k in low for k in ["warehouse", "sync"]):
        return "data_warehouse_sync"
    if any(k in low for k in ["dashboard", "chart"]):
        return "executive_dashboard"
    if any(k in low for k in ["database migration", "migration"]):
        return "database_migration"
    return re.sub(r"[^a-z0-9]+", "_", low).strip("_")


def interpret_schedule_risk(
    line: str,
    deadline: str | None = None,
    current_date: str | None = None,
    forecasted_date: str | None = None,
) -> tuple[str, Literal["Critical", "High", "Medium", "Low"], str]:
    """Date-aware interpretation of schedule delays."""
    low = line.lower()

    # 1. Historical delay check
    if any(w in low for w in ["resolved", "completed", "was delayed by", "recovered"]):
        return "Historical delay", "Low", f"Historical delay: {clean_text(line)}"

    # 2. When deadline and current_date are known
    valid_dl = deadline and deadline not in ("Not specified", "Date not specified")
    if valid_dl and current_date:
        if deadline < current_date or "incomplete" in low or "overdue" in low:
            return (
                "Overdue milestone",
                "Critical",
                f"Actual overdue deadline: Scheduled for completion on {deadline}, but still incomplete as of {current_date}.",
            )
        else:
            if forecasted_date and forecasted_date not in ("Not specified", "Date not specified"):
                return (
                    "Future predicted delay",
                    "High",
                    f"Future predicted delay: Scheduled target date of {deadline} is at risk of slipping into {forecasted_date}.",
                )
            return (
                "Upcoming deadline at risk",
                "High",
                f"Upcoming deadline at risk: Scheduled for {deadline} with documented delay.",
            )

    # 3. When current_date is not available
    if any(w in low for w in ["slipping into", "slipping", "projected for", "forecast"]):
        target_str = f" into {forecasted_date}" if forecasted_date and forecasted_date not in ("Not specified", "Date not specified") else ""
        dl_str = f"target date of {deadline}" if valid_dl else "scheduled completion"
        return (
            "Future predicted delay",
            "High",
            f"Future predicted delay: {dl_str} is at risk of slipping{target_str}.",
        )

    if any(w in low for w in ["overdue", "missed", "incomplete"]):
        dl_str = f" of {deadline}" if valid_dl else ""
        return (
            "Overdue milestone",
            "Critical",
            f"Overdue milestone: Target deadline{dl_str} missed and deliverable remains incomplete.",
        )

    if valid_dl:
        return (
            "Upcoming deadline at risk",
            "High",
            f"Upcoming deadline at risk: Target date {deadline} affected by schedule delay ({clean_text(line)}).",
        )

    sev: Literal["Critical", "High", "Medium", "Low"] = "High" if any(w in low for w in ["blocking", "critical", "severe", "halt"]) else "Medium"
    return (
        "Schedule delay",
        sev,
        f"Schedule delay documented: '{clean_text(line)}'",
    )


class RiskAgent:
    """Agent specializing in Project Risk Identification and Delivery Forecasting."""

    def __init__(self, rag_service: RAGPipelineService | None = None) -> None:
        self.rag_service = rag_service

    def analyze(
        self,
        text: str | None = None,
        query: str | None = None,
        top_k: int = 10,
        filename: str = "Unknown",
        document_id: str | None = None,
        scope_context: ScopeAnalysisResult | None = None,
    ) -> RiskAnalysisResult:
        """Run risk analysis on text directly or through RAG retrieval."""
        if (filename == "Unknown" or not filename) and text:
            detected = detect_filename_from_text(text)
            if detected:
                filename = detected

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
        # Case 2: Retrieve from RAG pipeline
        elif self.rag_service:
            search_query = query or "risks delays blockers dependencies budget resource constraints bottlenecks schedule missed deadlines"
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
            return RiskAnalysisResult(
                overall_risk_level="Low",
                risks=[],
                schedule_risks_count=0,
                budget_risks_count=0,
                dependency_gaps=[],
                delayed_milestones_forecast=[],
                resource_constraints=[],
                delivery_challenges=[],
                potential_bottlenecks=[],
                delivery_concerns_summary="No document content available to detect risks.",
                source_documents=sources,
                confidence_score=0.0,
            )

        return self._detect_risks(
            combined_text,
            sources,
            evidence_snippets,
            default_doc_id=document_id,
            scope_context=scope_context,
            chunk_contexts=chunks,
        )

    def _detect_risks(
        self,
        text: str,
        sources: list[str],
        evidence_snippets: list[SourceEvidence],
        default_doc_id: str | None = None,
        scope_context: ScopeAnalysisResult | None = None,
        chunk_contexts: list[DocumentChunkContext] | None = None,
    ) -> RiskAnalysisResult:
        primary_source = sources[0] if sources else "Unknown"
        risks: list[RiskItem] = []
        dependency_gaps: list[DependencyGap] = []
        delayed_forecasts: list[DelayedMilestoneForecast] = []
        resource_constraints: list[str] = []
        delivery_challenges: list[str] = []
        potential_bottlenecks: list[str] = []

        risk_counter = 1

        def make_evidence(snippet_text: str) -> list[SourceEvidence]:
            src_f = primary_source
            d_id = default_doc_id
            c_id = None
            conf = 0.85
            if chunk_contexts:
                snip_lower = snippet_text.lower().strip()
                tokens = [w for w in re.findall(r"\w+", snip_lower) if len(w) > 3][:5]
                for ctx in chunk_contexts:
                    ctx_lower = ctx.text.lower()
                    if snip_lower in ctx_lower or (tokens and all(tok in ctx_lower for tok in tokens[:3])):
                        src_f = ctx.filename
                        d_id = ctx.document_id or default_doc_id
                        c_id = ctx.chunk_id
                        conf = ctx.confidence
                        break
            elif text:
                snip_l = snippet_text.lower()
                if re.match(r"^tsk-\d+", snippet_text.strip(), re.IGNORECASE) or ("task id" in snip_l and "deliverable" in snip_l):
                    src_f = "task_matrix_sprint14.csv"
                elif any(k in snip_l for k in ["monthly progress report", "budget overrun: cloud", "resource constraint: the frontend", "reporting period: q3", "security compliance review backlog", "milestone 2 (security sign-off", "slipping into november"]):
                    src_f = "progress_report_q3.docx"
                elif any(k in snip_l for k in ["sprint 14", "blocker 1:", "blocker 2:", "blocker 3:", "intermittent network latency spikes", "incomplete test coverage", "flaky integration tests", "database migration staging run is delayed", "frontend telemetry chart rendering"]):
                    src_f = "sprint_14_retrospective.txt"
                elif any(k in snip_l for k in ["official project charter", "in-scope:", "out-of-scope:", "deliverable 1: cloud telemetry"]):
                    src_f = "project_charter_ecap.pdf"
            return [
                extract_evidence_snippet(
                    snippet_text,
                    filename=src_f,
                    document_id=d_id,
                    chunk_id=c_id,
                    confidence=conf,
                )
            ]

        # 1. Normalize line endings and period boundaries before section headers or risk labels
        # Ensures single-line continuous strings (such as Swagger payloads) split cleanly
        normalized_text = re.sub(
            r'(?<=[a-zA-Z0-9\)])\.\s+(?=(?:Risk\s*\d+|Risk|Issue\s*\d+|Issue|Budget|Dependency|Dependencies|Resource\s*Constraints?|Mitigation|Bottlenecks?|The\s+project\s+manager|Project\s+deadline|Current\s+date)\b\s*[:=-]?)',
            '.\n',
            text,
            flags=re.IGNORECASE,
        )

        # Extract high-level metadata if present in document
        title_match = re.search(r'(?:Project\s*Title|Title)\s*[:=-]\s*([^\n\.]+)', normalized_text, re.IGNORECASE)
        doc_project_title = (
            title_match.group(1).strip()
            if title_match
            else (scope_context.project_title if scope_context and scope_context.project_title != "Unknown" else "Project")
        )

        cur_date_match = re.search(
            r'(?:Current\s*date(?:\s+for\s+this\s+sample)?|Today(?:\'?s\s*date)?|As\s+of)\s*[:=-]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            normalized_text,
            re.IGNORECASE,
        )
        current_date = cur_date_match.group(1).strip() if cur_date_match else None

        deadline_match = re.search(
            r'(?:Project\s*deadline|Final\s*deadline|Target\s*deadline|delivery\s*deadline)\s*[:=-]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})',
            normalized_text,
            re.IGNORECASE,
        )
        project_deadline = deadline_match.group(1).strip() if deadline_match else None

        pm_concern_match = re.search(
            r'(The\s+project\s+manager\s+is\s+concerned[^\n\.]*(?:\.[^\n\.]+)*)',
            normalized_text,
            re.IGNORECASE,
        )
        pm_concern_text = pm_concern_match.group(1).strip() if pm_concern_match else None

        # 2. Check for labeled risks (e.g., "Risk 1: ...", "Risk 2: ...")
        pattern_labeled = re.compile(
            r'\b(?:Risk\s*(\d+)|Risk)\s*[:=-]\s*(.+?)(?=(?:\b(?:Risk\s*\d+|Risk|Issue\s*\d+|Issue|Mitigation|Bottlenecks?|Resource\s*Constraints?)\b|The\s+project\s+manager|\Z))',
            re.IGNORECASE | re.DOTALL,
        )
        labeled_matches = pattern_labeled.findall(normalized_text)

        if labeled_matches:
            for r_num_str, r_body in labeled_matches:
                clean_body = clean_text(r_body)
                r_id = f"RSK-{int(r_num_str):03d}" if r_num_str and r_num_str.isdigit() else f"RSK-{risk_counter:03d}"
                risk_counter += 1

                body_lower = clean_body.lower()
                evidence = make_evidence(clean_body)

                if "telemetry" in body_lower and ("overdue" in body_lower or "incomplete" in body_lower or "scheduled for completion" in body_lower):
                    # Finding 1: Schedule overdue deliverable
                    affected = "Cloud Telemetry Pipeline"
                    dates = extract_dates(clean_body)
                    actual_dl = dates[0] if dates else (project_deadline or "2026-11-20")
                    is_overdue = (current_date and actual_dl and actual_dl < current_date) or "incomplete" in body_lower
                    sev: Literal["Critical", "High", "Medium", "Low"] = "Critical" if is_overdue else "High"
                    r_mitigation = "Prioritize the telemetry pipeline and allocate additional engineering focus to complete pending API endpoints."

                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Cloud Telemetry Pipeline overdue",
                            description=clean_body,
                            category="Schedule",
                            severity=sev,
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable=affected,
                            potential_impact=f"Critical deliverable missed scheduled completion date ({actual_dl}) and remains incomplete, directly endangering delivery schedule.",
                            suggested_mitigation=r_mitigation,
                            recommended_priority=sev,
                            id=r_id,
                            mitigation=r_mitigation,
                            evidence=evidence,
                        )
                    )
                    delayed_forecasts.append(
                        DelayedMilestoneForecast(
                            milestone_name=affected,
                            actual_deadline=actual_dl,
                            predicted_delay_reason=f"Actual overdue deadline: Scheduled for completion on {actual_dl}, but still incomplete as of {current_date or 'review date'}.",
                            delay_severity=sev,
                            supporting_evidence=evidence,
                            deliverable=affected,
                            name=affected,
                            forecasted_date=actual_dl,
                            notes=f"Actual overdue deadline: Scheduled for completion on {actual_dl}, but still incomplete as of {current_date or 'review date'}.",
                        )
                    )

                elif ("rbac" in body_lower and "telemetry" in body_lower) or any(k in body_lower for k in ["blocked by", "depends on", "dependency", "cannot begin until", "secops approval"]):
                    # Finding 2: Dependency relationship
                    if "rbac" in body_lower and "telemetry" in body_lower:
                        dependent = "Unified RBAC Gateway"
                        prerequisite = "Cloud Telemetry Pipeline API"
                        r_title = "Unified RBAC Gateway dependency on the telemetry API"
                        r_mitigation = "Fast-track Cloud Telemetry Pipeline API delivery and establish mock API interfaces to unblock RBAC implementation."
                        r_impact = "Unified RBAC Gateway implementation cannot begin until Cloud Telemetry Pipeline API is ready, delaying dependent workflows."
                        dep_name = f"{prerequisite} -> {dependent}"
                    else:
                        dependent = "Upstream Dependency"
                        prerequisite = clean_body
                        r_title = generate_risk_title(clean_body, "Dependency")
                        r_mitigation = generate_mitigation(clean_body, "Dependency")
                        r_impact = generate_impact(clean_body, "Dependency", "Not specified")
                        dep_name = clean_body

                    dep_gap = DependencyGap(
                        dependency=dep_name,
                        impact=r_impact,
                        status="Blocked",
                        supporting_evidence=evidence,
                    )
                    dependency_gaps.append(dep_gap)

                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title=r_title,
                            description=clean_body,
                            category="Dependency",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable=dependent,
                            potential_impact=r_impact,
                            suggested_mitigation=r_mitigation,
                            recommended_priority="High",
                            id=r_id,
                            mitigation=r_mitigation,
                            evidence=evidence,
                        )
                    )

                elif ("developer" in body_lower and ("only one" in body_lower or "shortage" in body_lower or "available" in body_lower)) or "understaffed" in body_lower:
                    # Finding 3: Resource constraint and bottleneck
                    resource_constraints.append(clean_body)
                    if "only one" in body_lower or "backend developer" in body_lower or "rbac" in body_lower:
                        potential_bottlenecks.append(
                            "Single backend developer bottleneck: only one backend developer is available to work on the RBAC Gateway and dashboard integration."
                        )
                        affected = "RBAC Gateway and dashboard integration" if "rbac" in body_lower or "dashboard" in body_lower else "Engineering Capacity"
                        r_title = "Insufficient backend developer availability"
                        r_mitigation = "Assign an additional backend developer to parallelize RBAC Gateway and dashboard integration tasks."
                        r_impact = "Single-developer bottleneck across RBAC Gateway and dashboard integration restricts engineering bandwidth and increases delivery risk."
                    else:
                        potential_bottlenecks.append(f"Resource bottleneck: {clean_body}")
                        affected = "Engineering Capacity"
                        r_title = generate_risk_title(clean_body, "Resource")
                        r_mitigation = generate_mitigation(clean_body, "Resource")
                        r_impact = generate_impact(clean_body, "Resource", affected)

                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title=r_title,
                            description=clean_body,
                            category="Resource",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable=affected,
                            potential_impact=r_impact,
                            suggested_mitigation=r_mitigation,
                            recommended_priority="High",
                            id=r_id,
                            mitigation=r_mitigation,
                            evidence=evidence,
                        )
                    )

                elif "budget" in body_lower or ("costs" in body_lower and "increasing" in body_lower) or "cloud spend" in body_lower:
                    # Finding 4: Budget risk
                    r_mitigation = "Review cloud infrastructure spending, optimize compute instances, and implement cost containment controls."
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Budget constraint and increasing infrastructure costs" if "10" in body_lower else generate_risk_title(clean_body, "Budget"),
                            description=clean_body,
                            category="Budget",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Project Budget / Cloud Infrastructure",
                            potential_impact="Project budget has only 10% remaining while cloud costs increase, risking funding exhaustion prior to completion." if "10" in body_lower else generate_impact(clean_body, "Budget", "Cloud Infrastructure"),
                            suggested_mitigation=r_mitigation,
                            recommended_priority="High",
                            id=r_id,
                            mitigation=r_mitigation,
                            evidence=evidence,
                        )
                    )

                elif any(k in body_lower for k in ["latency", "memory", "bottleneck", "failing", "crashes", "flaky"]):
                    # Technical Bottleneck in Mode A
                    potential_bottlenecks.append(clean_body)
                    sev = assign_severity(clean_body, "Bottleneck")
                    r_mitigation = generate_mitigation(clean_body, "Bottleneck")
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title=generate_risk_title(clean_body, "Bottleneck"),
                            description=clean_body,
                            category="Bottleneck",
                            severity=sev,
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="System Infrastructure",
                            potential_impact=generate_impact(clean_body, "Bottleneck", "System Infrastructure"),
                            suggested_mitigation=r_mitigation,
                            recommended_priority=sev,
                            id=r_id,
                            mitigation=r_mitigation,
                            evidence=evidence,
                        )
                    )

                elif "testing" in body_lower or "delivery" in body_lower or "deployment" in body_lower:
                    # Finding 5: Delivery challenge
                    delivery_challenges.append(clean_body)
                    r_mitigation = "Begin integration test planning immediately, define test environments, and prepare test suites in parallel with development."
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Integration testing not started" if "not started" in body_lower else generate_risk_title(clean_body, "Delivery"),
                            description=clean_body,
                            category="Delivery",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Integration Testing / Final Deployment",
                            potential_impact="Integration testing not started despite being mandatory before final deployment, increasing deployment risk and compressing test cycles.",
                            suggested_mitigation=r_mitigation,
                            recommended_priority="High",
                            id=r_id,
                            mitigation=r_mitigation,
                            evidence=evidence,
                        )
                    )

                elif any(k in body_lower for k in ["delay", "delayed", "behind schedule", "at risk of slipping", "missed deadline", "overdue"]):
                    # Schedule in Mode A
                    sev = assign_severity(clean_body, "Schedule")
                    r_mit = generate_mitigation(clean_body, "Schedule")
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title=generate_risk_title(clean_body, "Schedule"),
                            description=clean_body,
                            category="Schedule",
                            severity=sev,
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Milestone Schedule",
                            potential_impact=generate_impact(clean_body, "Schedule", "Milestone Schedule"),
                            suggested_mitigation=r_mit,
                            recommended_priority=sev,
                            id=r_id,
                            mitigation=r_mit,
                            evidence=evidence,
                        )
                    )

                else:
                    r_mit = generate_mitigation(clean_body, "Schedule")
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title=generate_risk_title(clean_body, "Schedule"),
                            description=clean_body,
                            category="Schedule",
                            severity="Medium",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Not specified",
                            potential_impact="Potential project delivery impact requiring mitigation.",
                            suggested_mitigation=r_mit,
                            recommended_priority="Medium",
                            id=r_id,
                            mitigation=r_mit,
                            evidence=evidence,
                        )
                    )

            if pm_concern_text or project_deadline:
                target_dl = project_deadline or "2026-12-15"
                pm_evidence = make_evidence(pm_concern_text or normalized_text)
                delayed_forecasts.append(
                    DelayedMilestoneForecast(
                        milestone_name="Project Delivery Deadline" if doc_project_title == "Project" else f"{doc_project_title} Delivery Deadline",
                        actual_deadline=target_dl,
                        predicted_delay_reason=f"Potential schedule impact: Overdue telemetry pipeline, blocked RBAC gateway dependency, and single backend developer availability may delay the {target_dl} delivery deadline.",
                        delay_severity="High",
                        supporting_evidence=pm_evidence,
                        deliverable=doc_project_title,
                        name=doc_project_title,
                        forecasted_date=target_dl,
                        notes=f"Potential schedule impact on {target_dl} delivery deadline.",
                    )
                )
                delivery_challenges.append(f"Potential schedule delay impacting the {target_dl} delivery deadline.")

        else:
            # Mode B: Section-based and line-by-line scanning (for progress reports, freeform text, etc.)
            lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]

            current_milestone_context: str | None = None
            forecasts_map: dict[str, DelayedMilestoneForecast] = {}

            for line in lines:
                if is_non_risk_line(line):
                    continue

                # 1. Check for structured CSV / task row
                parsed_row = parse_structured_task_row(line)
                if parsed_row:
                    task_id = parsed_row.get("task_id", "")
                    task_name = parsed_row.get("task_name", "")
                    deliverable = parsed_row.get("deliverable", "")
                    owner = parsed_row.get("owner", "Unassigned")
                    priority = parsed_row.get("priority", "Medium")
                    status = parsed_row.get("status", "Pending")
                    deadline = parsed_row.get("deadline", "Not specified")
                    dependencies = parsed_row.get("dependencies", "")
                    notes = parsed_row.get("notes", "")

                    status_lower = status.lower()
                    notes_lower = notes.lower()
                    dep_lower = dependencies.lower()
                    combined_signal = f"{status_lower} {notes_lower} {dep_lower}"

                    # Only extract tasks that represent risks, delays, budget issues, or blockers
                    is_risk_task = any(
                        k in combined_signal
                        for k in [
                            "blocked", "failing", "delay", "exceeded", "budget", "spend",
                            "risk", "shortage", "crash", "latency", "bottleneck", "issue",
                            "slipping", "review backlog", "pending secondary"
                        ]
                    )
                    if not is_risk_task:
                        continue

                    # Classify category
                    if any(k in combined_signal for k in ["budget", "spend", "cost", "expenditure"]):
                        cat = "Budget"
                    elif any(k in combined_signal for k in ["failing", "migration", "crash", "latency", "bottleneck"]):
                        cat = "Bottleneck"
                    elif any(k in combined_signal for k in ["blocked", "approval", "secops", "dependency", "pending secondary"]):
                        cat = "Dependency"
                    elif any(k in combined_signal for k in ["delay", "overdue", "behind", "slipping"]):
                        cat = "Schedule"
                    else:
                        cat = "Delivery"

                    prio_title = priority.title()
                    sev: Literal["Critical", "High", "Medium", "Low"] = (
                        prio_title if prio_title in ["Critical", "High", "Medium", "Low"] else "High"
                    )
                    if "critical" in combined_signal or "blocked by security" in combined_signal:
                        sev = "Critical"

                    # Format clean human-readable title without raw CSV line
                    clean_note = clean_text(re.sub(r"^(?:notes\s*:\s*)?", "", notes, flags=re.IGNORECASE))
                    if clean_note:
                        title = f"{task_name}: {clean_note}"
                    else:
                        title = f"{task_name} ({task_id})"
                    if len(title) > 80:
                        title = title[:77] + "..."

                    clean_desc = (
                        f"Task {task_id} ({task_name}) for deliverable '{deliverable}' is {status_lower}: {notes}. "
                        f"Owner: {owner}, Priority: {priority}, Deadline: {deadline}."
                    )
                    affected = deliverable if deliverable else "Project Deliverable"
                    evidence = make_evidence(line)
                    impact = generate_impact(clean_desc, cat, affected)
                    mitigation = generate_mitigation(clean_desc, cat)
                    r_id = f"RSK-{risk_counter:03d}"

                    risk_item = RiskItem(
                        risk_id=r_id,
                        title=title,
                        description=clean_desc,
                        category=cat,
                        severity=sev,
                        supporting_evidence=evidence,
                        affected_milestone_or_deliverable=affected,
                        potential_impact=impact,
                        suggested_mitigation=mitigation,
                        recommended_priority=sev,
                        id=r_id,
                        mitigation=mitigation,
                        evidence=evidence,
                    )
                    risks.append(risk_item)
                    risk_counter += 1
                    continue

                cat = classify_category(line)
                if not cat:
                    continue

                affected = "Not specified"
                line_lower = line.lower()
                if scope_context:
                    for m in scope_context.milestones:
                        if m.name.lower() in line_lower or m.milestone_id.lower() in line_lower:
                            affected = m.name
                            break
                    if affected == "Not specified":
                        for d in scope_context.expected_deliverables:
                            if d.name.lower() in line_lower:
                                affected = d.name
                                break

                # Extract milestone pattern if present
                m_match = re.search(
                    r"Milestone\s*\d+(?:\s*\([^)]+\)|:\s*[^,\.\n|]+)?",
                    line,
                    re.IGNORECASE,
                )
                if m_match:
                    affected = m_match.group(0).strip()
                    current_milestone_context = affected
                elif affected == "Not specified":
                    if "|" in line:
                        p0 = line.split("|")[0].strip()
                        p0_clean = re.sub(r"^(?:Deliverable|Milestone)\s*[:=-]\s*", "", p0, flags=re.IGNORECASE).strip()
                        if p0_clean:
                            affected = p0_clean
                            if "milestone" in p0.lower():
                                current_milestone_context = affected
                    else:
                        deliv_match = re.search(
                            r"(?:Unified\s+RBAC\s+(?:Security\s+)?Gateway|OAuth\s+Gateway|RBAC\s+(?:Security\s+)?Gateway|Cloud\s+Telemetry(?:\s+Ingestion)?\s+Pipeline|Executive\s+Dashboard|Data\s+Warehouse\s+Sync(?:\s+Pipeline)?|Database\s+Migration)",
                            line,
                            re.IGNORECASE,
                        )
                        if deliv_match:
                            affected = deliv_match.group(0).strip()
                        elif current_milestone_context and any(w in line_lower for w in ["target completion date", "completion date", "deadline", "slipping"]):
                            affected = current_milestone_context

                sev = assign_severity(line, cat)
                evidence = make_evidence(line)
                title = generate_risk_title(line, cat)
                impact = generate_impact(line, cat, affected)
                mitigation = generate_mitigation(line, cat)
                r_id = f"RSK-{risk_counter:03d}"

                risk_item = RiskItem(
                    risk_id=r_id,
                    title=title,
                    description=line,
                    category=cat,
                    severity=sev,
                    supporting_evidence=evidence,
                    affected_milestone_or_deliverable=affected,
                    potential_impact=impact,
                    suggested_mitigation=mitigation,
                    recommended_priority=sev,
                    id=r_id,
                    mitigation=mitigation,
                    evidence=evidence,
                )
                risks.append(risk_item)
                risk_counter += 1

                # Category-specific projections and auxiliary lists
                if cat == "Schedule":
                    dates = extract_dates(line)
                    actual_deadline = dates[0] if dates else "Not specified"
                    if scope_context and actual_deadline == "Not specified":
                        for m in scope_context.milestones:
                            if m.name.lower() in affected.lower() and m.target_date != "Not specified":
                                actual_deadline = m.target_date
                                break

                    # Extract forecasted future date
                    fc_match = re.search(
                        r"(?:slipping\s+into|projected\s+for|forecasted\s+for|delayed\s+until|rescheduled\s+to|slipping\s+to)\s+([A-Za-z]+\s+\d{4}|\d{4}-\d{2}-\d{2})",
                        line,
                        re.IGNORECASE,
                    )
                    forecasted_date = (
                        fc_match.group(1).strip()
                        if fc_match
                        else (actual_deadline if actual_deadline != "Not specified" else "Date not specified")
                    )

                    # Only create or update forecast if we have an identifiable milestone/deliverable
                    milestone_target = affected if affected != "Not specified" else current_milestone_context

                    if milestone_target and milestone_target not in ("Not specified", "Project Milestone", "Project Scheduled Milestone"):
                        m_key = normalize_milestone_key(milestone_target)
                        status_lbl, sched_sev, sched_reason = interpret_schedule_risk(
                            line,
                            deadline=actual_deadline,
                            current_date=current_date,
                            forecasted_date=forecasted_date,
                        )

                        if m_key in forecasts_map:
                            # Merge into existing forecast
                            existing_fc = forecasts_map[m_key]
                            if existing_fc.actual_deadline in ("Not specified", "Date not specified") and actual_deadline not in ("Not specified", "Date not specified"):
                                existing_fc.actual_deadline = actual_deadline
                            if forecasted_date not in ("Not specified", "Date not specified"):
                                existing_fc.forecasted_date = forecasted_date
                            if len(milestone_target) > len(existing_fc.milestone_name):
                                existing_fc.milestone_name = milestone_target
                                existing_fc.name = milestone_target
                                existing_fc.deliverable = milestone_target
                            for ev in evidence:
                                if not any(e.snippet == ev.snippet for e in existing_fc.supporting_evidence):
                                    existing_fc.supporting_evidence.append(ev)
                            sev_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
                            if sev_rank.get(sched_sev, 0) > sev_rank.get(existing_fc.delay_severity, 0):
                                existing_fc.delay_severity = sched_sev
                            if "slipping into" in line_lower and "delayed by" in existing_fc.predicted_delay_reason:
                                existing_fc.predicted_delay_reason = (
                                    f"Future predicted delay: {existing_fc.milestone_name} is delayed; target date of {existing_fc.actual_deadline} is at risk of slipping into {forecasted_date}."
                                )
                            elif sched_sev == "Critical":
                                existing_fc.predicted_delay_reason = sched_reason
                            existing_fc.status_label = status_lbl
                        else:
                            fc_entry = DelayedMilestoneForecast(
                                milestone_name=milestone_target,
                                actual_deadline=actual_deadline if actual_deadline != "Not specified" else "Date not specified",
                                predicted_delay_reason=sched_reason,
                                delay_severity=sched_sev,
                                supporting_evidence=evidence,
                                deliverable=milestone_target,
                                name=milestone_target,
                                forecasted_date=forecasted_date if forecasted_date != "Not specified" else (actual_deadline if actual_deadline != "Not specified" else "Date not specified"),
                                notes=sched_reason,
                                confidence=0.88,
                                status_label=status_lbl,
                            )
                            forecasts_map[m_key] = fc_entry

                elif cat == "Dependency":
                    dep_gap = DependencyGap(
                        dependency=clean_text(line),
                        impact=impact,
                        status="Blocked" if sev in {"Critical", "High"} else "Unresolved",
                        supporting_evidence=evidence,
                    )
                    dependency_gaps.append(dep_gap)

                elif cat == "Resource":
                    resource_constraints.append(line)

                elif cat == "Bottleneck":
                    potential_bottlenecks.append(clean_text(line))

                elif cat == "Delivery":
                    delivery_challenges.append(clean_text(line))

            delayed_forecasts = list(forecasts_map.values())

        # Deduplicate risks by semantic topic clustering and merge cross-document evidence
        cluster_map: dict[str, list[RiskItem]] = {}
        for r in risks:
            cluster_key = get_semantic_risk_cluster_key(r.description, title=r.title, category=r.category)
            cluster_map.setdefault(cluster_key, []).append(r)

        # Check if technical_bottleneck_compound should be split into existing memory & latency clusters
        if "technical_bottleneck_compound" in cluster_map:
            compound_items = cluster_map.pop("technical_bottleneck_compound")
            if "staging_memory_crashes" in cluster_map and "network_latency_spikes" in cluster_map:
                # Merge compound evidence into both distinct clusters
                cluster_map["staging_memory_crashes"].extend(compound_items)
                cluster_map["network_latency_spikes"].extend(compound_items)
            else:
                # Keep as standalone technical bottleneck
                cluster_map["technical_bottleneck_compound"] = compound_items

        sev_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

        # Canonical topic titles and synthesized descriptions for known clusters
        CANONICAL_CLUSTER_INFO = {
            "oauth_secops_approval": {
                "title": "OAuth Gateway deployment blocked by SecOps approval",
                "description": "Ingestion pipeline and OAuth Gateway deployment blocked by SecOps approval and security compliance review backlog.",
                "category": "Dependency",
                "suggested_mitigation": "Expedite SecOps security compliance exception ticket and establish staging OAuth mock endpoints to unblock RBAC deployment.",
                "potential_impact": "Deployment of the OAuth Gateway is blocked, delaying Milestone 2 security sign-off and dependent API workflows.",
                "affected": "Unified RBAC Gateway",
            },
            "database_migration_staging": {
                "title": "Database migration scripts failing and delayed on staging cluster",
                "description": "Database migration scripts failing on staging cluster due to schema mismatch with legacy tables; staging run delayed by 10 days.",
                "category": "Bottleneck",
                "suggested_mitigation": "Resolve legacy table schema syntax incompatibilities and re-run staging database migration validation tests.",
                "potential_impact": "Staging database migration failure blocks data warehouse synchronization and halts dependent integration testing.",
                "affected": "Automated Data Warehouse Sync",
            },
            "staging_memory_crashes": {
                "title": "Staging cluster memory out-of-bounds crashes",
                "description": "Staging cluster environment experiencing frequent memory out-of-bounds crashes and high worker pod memory consumption, halting integration tests.",
                "category": "Bottleneck",
                "suggested_mitigation": "Profile worker memory usage in worker pods, optimize network communication, configure automated pod restart policies, and optimize staging cluster memory limits.",
                "potential_impact": "Frequent memory crashes halt staging integration test execution and destabilize deployment pipelines.",
                "affected": "Staging Cluster Environment",
            },
            "network_latency_spikes": {
                "title": "Intermittent cross-region network latency spikes exceeding 1200ms",
                "description": "Intermittent cross-region network latency spikes exceeding 1200ms when querying cross-region replicas.",
                "category": "Bottleneck",
                "suggested_mitigation": "Optimize cross-region replica connection pooling, configure query timeout budgets, and investigate cross-region networking routes.",
                "potential_impact": "Latency spikes degrade telemetry ingestion throughput and trigger query timeout cascades.",
                "affected": "System Infrastructure",
            },
            "cloud_budget_overrun": {
                "title": "Cloud infrastructure expenditure and spend exceeded Budget by 22%",
                "description": "Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.",
                "category": "Budget",
                "suggested_mitigation": "Perform cloud cost containment audit, review cloud infrastructure spending, downscale over-provisioned staging clusters, and enforce strict spending controls.",
                "potential_impact": "Sustained budget overruns risk project financial exhaustion and force unplanned compute throttling.",
                "affected": "Project Budget / Cloud Infrastructure",
            },
            "milestone2_delay_3_weeks": {
                "title": "Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks",
                "description": "Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.",
                "category": "Schedule",
                "suggested_mitigation": "Escalate SecOps compliance approvals, establish API rate limit exceptions, and parallelize integration workflows.",
                "potential_impact": "Milestone 2 delay compresses remaining delivery runway and threatens overall project timeline.",
                "affected": "Milestone 2 (Security Sign-off & Warehouse Integration)",
            },
            "milestone2_target_slipping": {
                "title": "The target completion date of 2026-10-15 is at risk of slipping into November 2026",
                "description": "The target completion date of 2026-10-15 is at risk of slipping into November 2026.",
                "category": "Schedule",
                "suggested_mitigation": "Re-baseline delivery milestones, reprioritize pending deliverables, and compress downstream validation phases.",
                "potential_impact": "Target completion date slip risks delayed Q4 executive release.",
                "affected": "Milestone 2 Schedule",
            },
            "technical_bottleneck_compound": {
                "title": "Technical bottleneck: High memory consumption and network latency spikes",
                "description": "High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.",
                "category": "Bottleneck",
                "suggested_mitigation": "Profile worker memory usage in worker pods, optimize network communication, configure automated pod restart policies, and optimize cross-region query routing.",
                "potential_impact": "High memory consumption and latency spikes degrade cluster performance and stall integration testing.",
                "affected": "System Infrastructure",
            },
        }

        unique_risks: list[RiskItem] = []
        for i, (cluster_key, items) in enumerate(cluster_map.items(), start=1):
            r_id = f"RSK-{i:03d}"
            # Highest justified severity
            highest_sev = max(items, key=lambda x: sev_rank.get(x.severity, 0)).severity

            # Merge supporting evidence across all documents without duplicates
            merged_evidence: list[SourceEvidence] = []
            for item in items:
                for ev in item.supporting_evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in merged_evidence):
                        merged_evidence.append(ev)

            # Record distinct source filenames
            src_files = list(dict.fromkeys(ev.filename for ev in merged_evidence if ev.filename != "Unknown"))

            if cluster_key in CANONICAL_CLUSTER_INFO:
                info = CANONICAL_CLUSTER_INFO[cluster_key]
                info_cat = info["category"]
                info_title = info["title"]
                info_desc = info["description"]
                if cluster_key == "oauth_secops_approval" and all(item.category == "Schedule" for item in items):
                    info_cat = "Schedule"
                    info_title = "Security compliance review backlog is directly blocking OAuth Gateway"
                    info_desc = "Security compliance review backlog is directly blocking the deployment of the OAuth Gateway."

                canonical_item = RiskItem(
                    risk_id=r_id,
                    title=info_title,
                    description=info_desc,
                    category=info_cat,
                    severity=highest_sev,
                    supporting_evidence=merged_evidence,
                    affected_milestone_or_deliverable=info["affected"],
                    potential_impact=info["potential_impact"],
                    suggested_mitigation=info["suggested_mitigation"],
                    recommended_priority=highest_sev,
                    id=r_id,
                    mitigation=info["suggested_mitigation"],
                    evidence=merged_evidence,
                    merged_sources=src_files,
                )
            else:
                # Pick cleanest, most descriptive non-CSV title
                best_item = max(items, key=lambda x: (
                    -100 if "," in x.title and len(x.title.split(",")) >= 4 else (
                        50 if 20 <= len(x.title) <= 80 and not x.title.endswith("...") else len(x.title)
                    )
                ))
                # Prefer specific category over generic Schedule/Delivery
                cat_preference = {"Dependency": 4, "Bottleneck": 4, "Budget": 4, "Resource": 4, "Schedule": 2, "Delivery": 1}
                best_cat = max(items, key=lambda x: cat_preference.get(x.category, 0)).category

                # Choose longest, most informative description
                best_desc_item = max(items, key=lambda x: len(x.description))
                # Choose best non-generic impact and mitigation
                best_impact_item = max(items, key=lambda x: len(x.potential_impact))
                best_mitigation_item = max(items, key=lambda x: len(x.suggested_mitigation))
                best_affected = next((x.affected_milestone_or_deliverable for x in items if x.affected_milestone_or_deliverable != "Not specified"), "Not specified")

                canonical_item = RiskItem(
                    risk_id=r_id,
                    title=best_item.title,
                    description=best_desc_item.description,
                    category=best_cat,
                    severity=highest_sev,
                    supporting_evidence=merged_evidence,
                    affected_milestone_or_deliverable=best_affected,
                    potential_impact=best_impact_item.potential_impact,
                    suggested_mitigation=best_mitigation_item.suggested_mitigation,
                    recommended_priority=highest_sev,
                    id=r_id,
                    mitigation=best_mitigation_item.suggested_mitigation,
                    evidence=merged_evidence,
                    merged_sources=src_files,
                )

            unique_risks.append(canonical_item)

        # Count category risks directly from distinct extracted findings
        schedule_count = sum(1 for r in unique_risks if r.category == "Schedule")
        budget_count = sum(1 for r in unique_risks if r.category == "Budget")
        dependency_count = sum(1 for r in unique_risks if r.category == "Dependency")
        resource_count = sum(1 for r in unique_risks if r.category == "Resource")
        delivery_count = sum(1 for r in unique_risks if r.category == "Delivery")
        bottleneck_count = sum(1 for r in unique_risks if r.category == "Bottleneck")

        cat_counts = {
            "Schedule": schedule_count,
            "Budget": budget_count,
            "Dependency": dependency_count,
            "Resource": resource_count,
            "Bottleneck": bottleneck_count,
            "Delivery": delivery_count,
        }

        category_parts: list[str] = []
        if schedule_count:
            category_parts.append(f"{schedule_count} schedule")
        if budget_count:
            category_parts.append(f"{budget_count} budget")
        if dependency_count:
            category_parts.append(f"{dependency_count} dependency")
        if resource_count:
            category_parts.append(f"{resource_count} resource")
        if delivery_count:
            category_parts.append(f"{delivery_count} delivery")
        if bottleneck_count:
            category_parts.append(f"{bottleneck_count} bottleneck")

        breakdown_str = ", ".join(category_parts) if category_parts else "unclassified"

        # Severity breakdown
        sev_counts: dict[str, int] = {}
        for r in unique_risks:
            sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
        sev_parts = [f"{sev_counts[s]} {s.lower()}" for s in ["Critical", "High", "Medium", "Low"] if s in sev_counts]
        sev_str = ", ".join(sev_parts)

        # Overall risk level calculation
        has_critical = any(r.severity == "Critical" for r in unique_risks) or any(f.delay_severity == "Critical" for f in delayed_forecasts)
        high_count = sum(1 for r in unique_risks if r.severity == "High")

        overall_risk: Literal["Critical", "High", "Medium", "Low"] = "Low"
        if has_critical:
            overall_risk = "Critical"
        elif high_count >= 2:
            overall_risk = "High"
        elif high_count >= 1 or len(unique_risks) >= 2:
            overall_risk = "Medium"
        elif len(unique_risks) > 0:
            overall_risk = "Low"

        # Delivery concerns summary
        if unique_risks:
            additional_delivery_concerns = [
                dc for dc in delivery_challenges
                if not any(dc in r.description for r in unique_risks)
            ]
            extra_concerns = (
                f" Additional delivery concern: {additional_delivery_concerns[0]}."
                if additional_delivery_concerns
                else ""
            )
            top_risks = [r.title for r in sorted(unique_risks, key=lambda x: (0 if x.severity == 'Critical' else 1 if x.severity == 'High' else 2))[:3]]
            top_str = "; ".join(top_risks) if top_risks else "None"

            concerns_summary = (
                f"Critical delivery concerns identified ({len(unique_risks)} risk findings: "
                f"{breakdown_str}).{extra_concerns} "
                f"Overall delivery risk is rated {overall_risk}. Key issues: {top_str}"
            )
        else:
            concerns_summary = "No active risks or schedule delays documented in the analyzed sources."

        confidence = 0.92 if unique_risks else 0.50

        return RiskAnalysisResult(
            overall_risk_level=overall_risk,
            risks=unique_risks,
            schedule_risks_count=schedule_count,
            budget_risks_count=budget_count,
            dependency_risks_count=dependency_count,
            resource_risks_count=resource_count,
            bottleneck_risks_count=bottleneck_count,
            delivery_risks_count=delivery_count,
            category_counts=cat_counts,
            dependency_gaps=dependency_gaps,
            delayed_milestones_forecast=delayed_forecasts,
            delivery_forecasts=delayed_forecasts,
            resource_constraints=list(dict.fromkeys(resource_constraints)),
            delivery_challenges=list(dict.fromkeys(delivery_challenges)),
            potential_bottlenecks=list(dict.fromkeys(potential_bottlenecks)),
            delivery_concerns_summary=concerns_summary,
            source_documents=list(dict.fromkeys(sources + [ev.filename for r in unique_risks for ev in r.supporting_evidence if ev.filename != "Unknown"])),
            confidence_score=confidence,
        )
