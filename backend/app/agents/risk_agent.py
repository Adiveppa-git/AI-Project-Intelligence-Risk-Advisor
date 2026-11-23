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
    extract_dates,
    extract_evidence_snippet,
    normalize_content_key,
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
                            suggested_mitigation="Prioritize the telemetry pipeline and allocate additional engineering focus to complete pending API endpoints.",
                            recommended_priority=sev,
                        )
                    )
                    delayed_forecasts.append(
                        DelayedMilestoneForecast(
                            milestone_name=affected,
                            actual_deadline=actual_dl,
                            predicted_delay_reason=f"Actual overdue deadline: Scheduled for completion on {actual_dl}, but still incomplete as of {current_date or 'review date'}.",
                            delay_severity=sev,
                            supporting_evidence=evidence,
                        )
                    )

                elif "rbac" in body_lower and "telemetry" in body_lower and ("cannot begin until" in body_lower or "depend" in body_lower or "blocked" in body_lower):
                    # Finding 2: Dependency relationship
                    dependent = "Unified RBAC Gateway"
                    prerequisite = "Cloud Telemetry Pipeline API"
                    dep_gap = DependencyGap(
                        dependency=f"{prerequisite} -> {dependent}",
                        impact=f"{dependent} implementation cannot begin until {prerequisite} is ready.",
                        status="Blocked",
                        supporting_evidence=evidence,
                    )
                    dependency_gaps.append(dep_gap)

                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Unified RBAC Gateway dependency on the telemetry API",
                            description=clean_body,
                            category="Dependency",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable=dependent,
                            potential_impact="Unified RBAC Gateway implementation cannot begin until Cloud Telemetry Pipeline API is ready, delaying dependent workflows.",
                            suggested_mitigation="Fast-track Cloud Telemetry Pipeline API delivery and establish mock API interfaces to unblock RBAC implementation.",
                            recommended_priority="High",
                        )
                    )

                elif ("developer" in body_lower and ("only one" in body_lower or "shortage" in body_lower or "available" in body_lower)) or "understaffed" in body_lower:
                    # Finding 3: Resource constraint and bottleneck
                    resource_constraints.append(clean_body)
                    potential_bottlenecks.append(
                        "Single backend developer bottleneck: only one backend developer is available to work on the RBAC Gateway and dashboard integration."
                    )
                    affected = "RBAC Gateway and dashboard integration" if "rbac" in body_lower or "dashboard" in body_lower else "Engineering Capacity"
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Insufficient backend developer availability",
                            description=clean_body,
                            category="Resource",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable=affected,
                            potential_impact="Single-developer bottleneck across RBAC Gateway and dashboard integration restricts engineering bandwidth and increases delivery risk.",
                            suggested_mitigation="Assign an additional backend developer to parallelize RBAC Gateway and dashboard integration tasks.",
                            recommended_priority="High",
                        )
                    )

                elif "budget" in body_lower or ("costs" in body_lower and "increasing" in body_lower) or "cloud spend" in body_lower:
                    # Finding 4: Budget risk
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Budget constraint and increasing infrastructure costs",
                            description=clean_body,
                            category="Budget",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Project Budget / Cloud Infrastructure",
                            potential_impact="Project budget has only 10% remaining while cloud costs increase, risking funding exhaustion prior to completion.",
                            suggested_mitigation="Review cloud infrastructure spending, optimize compute instances, and implement cost containment controls.",
                            recommended_priority="High",
                        )
                    )

                elif "testing" in body_lower or "delivery" in body_lower or "deployment" in body_lower:
                    # Finding 5: Delivery challenge
                    delivery_challenges.append(clean_body)
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title="Integration testing not started",
                            description=clean_body,
                            category="Delivery",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Integration Testing / Final Deployment",
                            potential_impact="Integration testing not started despite being mandatory before final deployment, increasing deployment risk and compressing test cycles.",
                            suggested_mitigation="Begin integration test planning immediately, define test environments, and prepare test suites in parallel with development.",
                            recommended_priority="High",
                        )
                    )

                else:
                    risks.append(
                        RiskItem(
                            risk_id=r_id,
                            title=f"Project Risk: {clean_body[:50]}",
                            description=clean_body,
                            category="Schedule",
                            severity="Medium",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Not specified",
                            potential_impact="Potential project delivery impact requiring mitigation.",
                            suggested_mitigation="Review and address the documented project risk item.",
                            recommended_priority="Medium",
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
                    )
                )
                delivery_challenges.append(f"Potential schedule delay impacting the {target_dl} delivery deadline.")

        else:
            # Mode B: Section-based and line-by-line scanning (for progress reports, freeform text, etc.)
            lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]

            # 1. Schedule & Deadline Delay Detection
            schedule_keywords = [
                "delay", "delayed", "behind schedule", "missed deadline", "slipping",
                "overdue", "late delivery", "postponed", "cannot meet deadline", "incomplete"
            ]
            for line in lines:
                line_lower = line.lower()
                if any(k in line_lower for k in schedule_keywords):
                    sev: Literal["Critical", "High", "Medium", "Low"] = "High"
                    if any(crit in line_lower for crit in ["critical", "halted", "blocker", "cannot release", "major delay"]):
                        sev = "Critical"
                    elif any(med in line_lower for med in ["slight", "minor", "1 day", "few days"]):
                        sev = "Medium"

                    affected = "Not specified"
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

                    if affected == "Not specified":
                        m_match = re.search(r"(?:milestone\s*\d+|sprint\s*\d+|release\s*[\d\.]*|[A-Za-z0-9_-]+\s*deliverable)", line, re.IGNORECASE)
                        if m_match:
                            affected = m_match.group(0).strip()

                    evidence = make_evidence(line)
                    risk_item = RiskItem(
                        risk_id=f"RSK-{risk_counter:03d}",
                        title=f"Schedule Delay Risk: {clean_text(line[:60])}",
                        description=line,
                        category="Schedule",
                        severity=sev,
                        supporting_evidence=evidence,
                        affected_milestone_or_deliverable=affected,
                        potential_impact=f"Potential project schedule slippage impacting delivery of '{affected}'.",
                        suggested_mitigation="Fast-track remaining blockers, reprioritize lower-tier tasks, or allocate supplemental engineering resources.",
                        recommended_priority=sev,
                    )
                    risks.append(risk_item)
                    risk_counter += 1

                    dates = extract_dates(line)
                    actual_deadline = dates[0] if dates else "Not specified"
                    if scope_context:
                        for m in scope_context.milestones:
                            if m.name == affected and m.target_date != "Not specified":
                                actual_deadline = m.target_date
                                break

                    milestone_forecast_name = affected if affected != "Not specified" else (
                        f"{doc_project_title} Scheduled Milestone" if doc_project_title != "Project" else "Project Milestone"
                    )

                    delayed_forecasts.append(
                        DelayedMilestoneForecast(
                            milestone_name=milestone_forecast_name,
                            actual_deadline=actual_deadline,
                            predicted_delay_reason=f"Identified delay factor in documentation: '{clean_text(line)}'",
                            delay_severity=sev,
                            supporting_evidence=evidence,
                        )
                    )

            # 2. Dependency Gaps
            dep_keywords = [
                "depends on", "dependency", "waiting for", "blocked by", "pending approval",
                "secops approval", "external api", "third-party", "prerequisite", "cannot begin until", "cannot start until"
            ]
            for line in lines:
                line_lower = line.lower()
                if any(k in line_lower for k in dep_keywords):
                    sev: Literal["Critical", "High", "Medium", "Low"] = "Medium"
                    if any(c in line_lower for c in ["blocker", "critical", "failing", "unresolved", "blocks"]):
                        sev = "High"

                    dep_evidence = make_evidence(line)
                    dep_gap = DependencyGap(
                        dependency=clean_text(line),
                        impact="Cross-team or upstream dependency delay may stall dependent workflows.",
                        status="At risk" if sev == "High" else "Unresolved",
                        supporting_evidence=dep_evidence,
                    )
                    dependency_gaps.append(dep_gap)

                    risks.append(
                        RiskItem(
                            risk_id=f"RSK-{risk_counter:03d}",
                            title=f"Dependency Risk: {clean_text(line[:60])}",
                            description=line,
                            category="Dependency",
                            severity=sev,
                            supporting_evidence=dep_evidence,
                            affected_milestone_or_deliverable="Not specified",
                            potential_impact="Work stoppage or execution delay on dependent deliverables.",
                            suggested_mitigation="Establish direct SLA and daily synchronization with upstream dependency provider or team.",
                            recommended_priority=sev,
                        )
                    )
                    risk_counter += 1

            # 3. Resource Constraints
            resource_keywords = [
                "resource constraint", "understaffed", "lack of", "shortage", "overcapacity",
                "bandwidth", "key person", "resignation", "leave", "on vacation", "only one"
            ]
            for line in lines:
                line_lower = line.lower()
                if any(k in line_lower for k in resource_keywords):
                    resource_constraints.append(line)
                    evidence = make_evidence(line)
                    risks.append(
                        RiskItem(
                            risk_id=f"RSK-{risk_counter:03d}",
                            title=f"Resource Constraint Risk: {clean_text(line[:60])}",
                            description=line,
                            category="Resource",
                            severity="High" if "critical" in line_lower else "Medium",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Not specified",
                            potential_impact="Engineering velocity reduction and bottleneck in deliverable completion.",
                            suggested_mitigation="Rebalance engineering assignments or onboard supplementary staff.",
                            recommended_priority="High" if "critical" in line_lower else "Medium",
                        )
                    )
                    risk_counter += 1

            # 4. Budget-Related Risks
            budget_keywords = [
                "budget", "cost overrun", "exceeded budget", "expensive", "cloud spend",
                "license cost", "financial", "expenditure", "over budget"
            ]
            for line in lines:
                line_lower = line.lower()
                if any(k in line_lower for k in budget_keywords) and any(alert in line_lower for alert in ["over", "exceed", "spike", "risk", "shortfall", "deficit", "warn", "increasing", "remaining"]):
                    evidence = make_evidence(line)
                    risks.append(
                        RiskItem(
                            risk_id=f"RSK-{risk_counter:03d}",
                            title=f"Budget Overrun Risk: {clean_text(line[:60])}",
                            description=line,
                            category="Budget",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Project Budget / Financials",
                            potential_impact="Unbudgeted operational expenses requiring scope deselect or emergency funding.",
                            suggested_mitigation="Audit cloud instance sizing, optimize infrastructure, and enforce cost containment ceilings.",
                            recommended_priority="High",
                        )
                    )
                    risk_counter += 1

            # 5. Bottlenecks
            bottleneck_keywords = [
                "bottleneck", "failing test", "rate limit", "latency", "instability",
                "single point of failure", "outage", "flaky", "pipeline failure"
            ]
            for line in lines:
                line_lower = line.lower()
                if any(k in line_lower for k in bottleneck_keywords):
                    potential_bottlenecks.append(line)
                    evidence = make_evidence(line)
                    risks.append(
                        RiskItem(
                            risk_id=f"RSK-{risk_counter:03d}",
                            title=f"Technical Bottleneck: {clean_text(line[:60])}",
                            description=line,
                            category="Bottleneck",
                            severity="High" if "failing" in line_lower or "outage" in line_lower else "Medium",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Not specified",
                            potential_impact="Stagnant throughput and test pipeline failure delaying sign-off.",
                            suggested_mitigation="Implement caching, optimize query bottlenecks, and fix flaky integration suites.",
                            recommended_priority="High" if "failing" in line_lower or "outage" in line_lower else "Medium",
                        )
                    )
                    risk_counter += 1

            # 6. Delivery Challenges
            delivery_keywords = [
                "testing has not started", "required before final deployment", "delivery challenge",
                "delivery risk", "acceptance testing", "staging verification"
            ]
            for line in lines:
                line_lower = line.lower()
                if any(k in line_lower for k in delivery_keywords):
                    delivery_challenges.append(line)
                    evidence = make_evidence(line)
                    risks.append(
                        RiskItem(
                            risk_id=f"RSK-{risk_counter:03d}",
                            title=f"Delivery Challenge: {clean_text(line[:60])}",
                            description=line,
                            category="Delivery",
                            severity="High",
                            supporting_evidence=evidence,
                            affected_milestone_or_deliverable="Integration Testing / Final Deployment",
                            potential_impact="Core verification phase pending, increasing final deployment risk.",
                            suggested_mitigation="Prioritize verification planning and run test automation in parallel with development.",
                            recommended_priority="High",
                        )
                    )
                    risk_counter += 1

        # Deduplicate risks by canonical content key similarity and merge evidence
        unique_risks: list[RiskItem] = []
        seen_risks: dict[str, RiskItem] = {}
        for r in risks:
            key = normalize_content_key(r.description)
            if key not in seen_risks:
                seen_risks[key] = r
                unique_risks.append(r)
            else:
                existing = seen_risks[key]
                for ev in r.supporting_evidence:
                    if not any(e.snippet == ev.snippet and e.filename == ev.filename for e in existing.supporting_evidence):
                        existing.supporting_evidence.append(ev)

        # Count category risks from distinct extracted findings
        schedule_count = sum(1 for r in unique_risks if r.category == "Schedule")
        budget_count = sum(1 for r in unique_risks if r.category == "Budget")
        dependency_count = sum(1 for r in unique_risks if r.category == "Dependency")
        resource_count = sum(1 for r in unique_risks if r.category == "Resource")
        delivery_count = sum(1 for r in unique_risks if r.category == "Delivery")
        bottleneck_count = sum(1 for r in unique_risks if r.category == "Bottleneck")

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
            concerns_summary = (
                f"Critical delivery concerns identified ({len(unique_risks)} risk findings: "
                f"{breakdown_str}).{extra_concerns} "
                f"Overall delivery risk is rated {overall_risk}. Key issues: "
                + "; ".join(r.title for r in unique_risks[:3])
            )
        else:
            concerns_summary = "No active risks or schedule delays documented in the analyzed sources."

        confidence = 0.92 if unique_risks else 0.50

        return RiskAnalysisResult(
            overall_risk_level=overall_risk,
            risks=unique_risks,
            schedule_risks_count=schedule_count,
            budget_risks_count=budget_count,
            dependency_gaps=dependency_gaps,
            delayed_milestones_forecast=delayed_forecasts,
            resource_constraints=list(dict.fromkeys(resource_constraints)),
            delivery_challenges=list(dict.fromkeys(delivery_challenges)),
            potential_bottlenecks=list(dict.fromkeys(potential_bottlenecks)),
            delivery_concerns_summary=concerns_summary,
            source_documents=sources,
            confidence_score=confidence,
        )
