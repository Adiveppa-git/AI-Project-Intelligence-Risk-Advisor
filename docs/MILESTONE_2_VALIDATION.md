# Milestone 2 Validation Report: Multi-Agent AI Project Intelligence & Risk Advisor

**Validation Date:** 2026-11-23  
**Environment:** Python 3.10.11, FastAPI, ChromaDB, Sentence-Transformers, pytest 8.4.2  
**Dataset Location:** `backend/sample_data/`  
**Test Suite:** `backend/tests/` (102 passed, 0 failed)  

---

## 1. Validation Objectives

This document records the empirical validation of Milestone 2:
1. Validate that the three specialized agents (`ScopeAgent`, `RiskAgent`, `BlockerAgent`) and the `AgentOrchestratorService` function accurately across different document formats: **Plain Text (TXT), Word (DOCX), Comma-Separated Values (CSV)**.
2. Confirm that agents extract distinct, complementary intelligence without hallucinating dates, owners, or deliverables.
3. Validate that RAG-based semantic retrieval correctly feeds multi-document evidence into multi-agent orchestration.
4. Verify that all 37 Milestone 1 automated tests and 62 Milestone 2 automated tests (total 99 automated tests) pass completely.

---

## 2. Sample Dataset Profile

A realistic enterprise scenario was constructed representing the **Enterprise Cloud Analytics Platform (ECAP)** project:

| Document File | Format | Size | Document Character Count | Content Description |
|---|---|---|---|---|
| `project_charter.pdf` | PDF | 1,917 B | 1,721 chars | Formal enterprise project charter with objectives, deliverables, milestones, governance, and risk factors. |
| `project_proposal.txt` | TXT | 2,467 B | 2,466 chars | Project charter with objectives, in-scope/out-of-scope boundaries, deliverables, milestones, deadlines, and team responsibilities. |
| `meeting_notes.txt` | TXT | 2,012 B | 2,011 chars | Sprint 14 technical sync containing active blockers, pending decisions, unresolved defects, delayed activities, and action items. |
| `task_list.csv` | CSV | 1,172 B | 1,819 chars | Operational task list containing Task IDs, owners, priorities, statuses, deadlines, and dependency notes. |
| `progress_report.docx` | DOCX | 37,759 B | 1,827 chars | Formal executive report with schedule delay warnings, budget overruns, resource constraints, and tabular status breakdowns. |

---

## 3. Empirical Validation Results by Document Format

Each document was ingested through `DocumentIngestionService` and processed through the `AgentOrchestratorService`.

### 3.1 Project Proposal (`project_proposal.txt`)
- **Ingestion Result:** Extracted 2,466 characters of structured UTF-8 text.
- **Scope Agent Findings:**
  - **Project Title:** `Enterprise Cloud Analytics Platform (ECAP)`
  - **Objectives:** 4 extracted (e.g., telemetry modernization, sub-second query latency, unified zero-trust RBAC).
  - **Scope Boundaries:** 5 in-scope items (Kubernetes, Kafka, OAuth2 RBAC, Dashboard, Snowflake sync); 3 out-of-scope items (mainframe connectors, native mobile apps, public third-party endpoints).
  - **Deliverables:** 4 extracted with assigned owners (`Alice Chen`, `Bob Martinez`, `Carol Vance`, `David Kim`) and deadlines.
  - **Milestones:** 3 extracted (`Milestone 1: Architectural Foundation`, `Milestone 2: Security Sign-off`, `Milestone 3: Production Rollout`) with target dates.
  - **Timeline:** Start Date: `2026-06-01`, End Date: `2026-12-15`.
  - **Deadlines:** 3 important deadlines identified (Infrastructure Freeze, Security Audit, UAT).
  - **Assigned Owners:** Correctly detected all 4 project leads without fabricating non-existent persons.
- **Risk & Blocker Agents:** Low risk profile; 0 blockers or active impediments (expected for proposal).
- **Project Health Score:** `Needs Attention` (due to pending status of future deliverables).

### 3.2 Meeting Notes (`meeting_notes.txt`)
- **Ingestion Result:** Extracted 2,011 characters of meeting minutes.
- **Blocker Agent Findings:**
  - **Active Blockers:** 4 blockers extracted, including SecOps approval block for OAuth exchange (Owner: `Bob Martinez`) and staging schema mismatch.
  - **Pending Decisions:** 2 decisions extracted: ClickHouse vs Snowflake (Decision Maker: `David Kim`, Deadline: `2026-09-25`) and Kafka retention sizing (Decision Maker: `Alice Chen`).
  - **Unresolved Issues:** 3 issues detected (1200ms latency spikes, incomplete token refresh tests, flaky CD pipeline).
  - **Action Items:** 6 action items extracted with owners (`Bob Martinez`, `Alice Chen`, `Carol Vance`, `David Kim`, and 2 `Unassigned`).
  - **Unassigned Action Items:** 2 items flagged for management assignment.
- **Risk Agent Findings:**
  - 6 risks detected (3 schedule risks, 2 dependency gaps, 1 bottleneck).
- **Project Health Score:** `At Risk`.

### 3.3 Task List Spreadsheet (`task_list.csv`)
- **Ingestion Result:** Extracted 1,819 characters formatted as labeled records (`Row N: Task ID: ...; Task Name: ...`).
- **Scope & Blocker Agent Findings:**
  - Extracted 7 distinct deliverable tasks (`TSK-101` through `TSK-107`).
  - Correctly mapped tasks to owners (`Alice Chen`, `Bob Martinez`, `Carol Vance`, `David Kim`, `Unassigned`).
  - Identified completed task (`TSK-101` Kafka Brokers) vs. in-progress and blocked tasks.
  - Detected critical blocker note on `TSK-102` ("Blocked by security compliance review").
  - Detected budget risk note on `TSK-105` ("Cloud spend exceeded budget by 22%").
- **Project Health Score:** `Critical` (due to critical blocker on `TSK-102`).

### 3.4 Progress Report Document (`progress_report.docx`)
- **Ingestion Result:** Extracted 1,827 characters from Word paragraphs and status tables.
- **Risk Agent Findings:**
  - **Schedule Risks:** Detected explicit schedule delay on Milestone 2 ("delayed by 3 weeks").
  - **Delivery Forecasting:** Linked delay to Milestone 2 target date (`2026-10-15`) and projected slip into November 2026.
  - **Budget Risks:** Detected that cloud spend exceeded budget by 22%.
  - **Resource Constraints:** Detected frontend engineering understaffing and shortage of senior SREs.
  - **Technical Bottlenecks:** Memory leaks and cross-region latency spikes exceeding 1200ms.
- **Scope Agent Findings:**
  - Extracted tabular data matching 3 milestones and 3 deliverables with owners and statuses.
- **Project Health Score:** `At Risk`.

### 3.5 Project Charter PDF (`project_charter.pdf`)
- **Ingestion Result:** Extracted 1,721 characters from PyMuPDF text stream across all document sections.
- **Scope Agent Findings:**
  - **Project Title:** `Enterprise Cloud Analytics Platform (ECAP)`
  - **Objectives:** 3 extracted (telemetry ingestion, zero-trust RBAC, executive reporting).
  - **Deliverables:** 4 key deliverables extracted (`Cloud Telemetry Pipeline`, `Unified RBAC Gateway`, `Real-Time Executive Dashboard`, `Data Warehouse Sync`).
  - **Milestones:** 3 milestones extracted (`Milestone 1: Architectural Foundation`, `Milestone 2: Security Sign-off`, `Milestone 3: Production Rollout`).
  - **Owners & Dates:** Correctly identified lead roles (`Alice Chen`, `Bob Martinez`, `Carol Vance`, `David Kim`) and start/end dates (`2026-06-01` to `2026-12-15`).
- **Risk Agent Findings:**
  - Detected governance constraints and regulatory compliance dependencies.
- **Blocker Agent Findings:**
  - Clean baseline with 0 active blockers or impediments.
- **Project Health Score:** `Needs Attention` (unstarted deliverables in charter).

---

## 4. Multi-Agent RAG Knowledge Base Integration Test

All 5 sample documents across all 4 formats (PDF, DOCX, CSV, TXT) were indexed into the local persistent ChromaDB collection (`project_chunks`):
- `project_charter.pdf`: 2 chunks stored
- `project_proposal.txt`: 3 chunks stored
- `meeting_notes.txt`: 3 chunks stored
- `progress_report.docx`: 2 chunks stored
- `task_list.csv`: 2 chunks stored
- **Total Indexed Knowledge Base:** 14 persistent vector chunks

**Multi-Agent Consolidated Intelligence Run Over Vector Index:**
- **Project Title:** `Enterprise Cloud Analytics Platform (ECAP)`
- **Project Health:** `Critical`
- **Milestones Identified:** 3
- **Deliverables Identified:** 11
- **Risks Identified:** 25 (10 schedule-related, 3 budget-related)
- **Delivery Forecasting:** 10 delayed milestone forecasts generated with supporting evidence snippets
- **Blockers & Actions:** 6 blockers, 13 action items (5 unassigned), 5 pending decisions
- **Executive Summary:** Consolidated cross-document intelligence report accurately synthesizing project risks, timeline delays, and unassigned work items.
- **Key Recommendations:**
  1. Immediately unblock SecOps approval for OAuth token exchange.
  2. Assign dedicated owners to 5 currently unassigned action items.
  3. Escalate pending warm-storage decision (ClickHouse vs. Snowflake) for executive sign-off.
  4. Mitigate Milestone 2 schedule delay risk through resource reallocation.

---

## 5. Automated Test Suite Execution

The automated test suite in `backend/tests/` was executed using pytest:

```
backend/tests/test_agent_api.py .......... [100%] (11 passed)
backend/tests/test_agent_orchestrator.py . [100%] (6 passed)
backend/tests/test_blocker_agent.py ...... [100%] (22 passed)
backend/tests/test_chunking.py ........... [100%] (9 passed)
backend/tests/test_document_ingestion.py . [100%] (22 passed)
backend/tests/test_rag_integration.py .... [100%] (6 passed)
backend/tests/test_risk_agent.py ......... [100%] (9 passed)
backend/tests/test_scope_agent.py ........ [100%] (17 passed)
```

**Summary:** **102 passed, 0 failed, 1 warning (starlette deprecation)** in 29.98s.

### 5.1 Scope Agent Precision & Accuracy Validation

Empirical testing specifically validated the accuracy improvements in `ScopeAgent`:
- **Project Title Isolation:** Unstructured narratives extract the concise entity title (`NextGen Banking Core`) rather than the entire narrative paragraph.
- **Objectives Separation:** Objectives extraction terminates cleanly at section boundary headers (`STOP_HEADER_REGEX`), preventing spillover into subsequent scope or deliverable sections.
- **Inline Scope Boundaries:** Supports conversational inline scope definitions (`"Scope covers X, while Y are out of scope"`).
- **Three-Tier Milestone Extraction:** Accurately separates numbered and named milestones (`Milestone 1`, `Milestone 2`, `Milestone 3`).
- **Anti-Hallucination:** Strictly falls back to model defaults (`"Unknown"`, `"Not specified"`, `[]`) when dates, owners, or scope boundaries are absent.

### 5.2 Deliverables, Responsibilities & Anti-Hallucination Refinement

Targeted regression testing validated the critical fixes for deliverables and responsibilities:
- **Compound & Hyphenated Deliverables:** Preserves hyphenated compound names (e.g. `Real-Time Dashboard`, `Zero-Trust Ingress`, `End-to-End Test Suite`) without splitting or fragmenting.
- **Deliverable Fragment Exclusion:** Tokens such as `"Real"`, `"Time"`, `"Pipeline"`, `"Dashboard"` are strictly prevented from entering `assigned_owners` or deliverable owners.
- **Natural Language Responsibility Parsing:** Accurately extracts `Person Name owns responsibility` patterns (e.g. `Alice Chen owns the telemetry pipeline`, `Bob Martinez owns the RBAC gateway`, `Carol Vance owns the dashboard`, `David Kim owns data warehouse integration`) even when packed within comma-separated sentences ending in `"and"`.
- **Semantic Deliverable-Owner Correlation:** Accurately correlates owners to deliverables even when phrasing varies slightly (e.g. `David Kim owns data warehouse integration` $\rightarrow$ `Data Warehouse Sync`).
- **Pending vs. Expected Deliverable Separation:** Items under `Pending deliverable:` (e.g. `Complete integration testing`) are extracted strictly into `pending_deliverables` and kept separate from `expected_deliverables`. Deliverables without explicit pending status remain `status="unknown"` and are not hallucinated into `pending_deliverables`.

### 5.3 Preservation of Original Deliverable Names & Single-Line Section Normalization

- **Original Deliverable Name Preservation:** Deliverable names from the explicit `Deliverables:` section are authoritative and are never mutated or replaced by paraphrased responsibility strings. In the test scenario, the fourth deliverable is strictly `Data Warehouse Sync` (owner: `David Kim`), while David Kim's responsibility remains `data warehouse integration`.
- **Numbered Milestone Stop Boundary:** Added `Milestones?(?:\s*\d+)?|M\d+` to `STOP_HEADER_REGEX`, preventing deliverables parsing from overflowing into subsequent milestones (`Milestone 1: ...`, `Milestone 3: Deploy dashboard and data warehouse integration`).
- **Inline Section Pre-Normalization:** Added period-boundary section normalization in `split_into_section_blocks`, allowing single-line or unstructured Swagger test payloads to be isolated cleanly into independent section blocks.

### 5.4 Risk Agent Accuracy & Individual Risk Extraction Validation

Empirical testing specifically validated the accuracy improvements in `RiskAgent` (`POST /api/agents/detect-risks`):
- **Individual Risk Finding Extraction:** Eliminates monolithic paragraph collapse. In single-line continuous payloads (typical Swagger inputs) or multi-line documents, the agent pre-normalizes period boundaries before risk labels (`Risk 1:`, `Risk 2:`) and extracts five distinct, cleanly partitioned findings:
  1. `Cloud Telemetry Pipeline overdue` (Schedule / Critical)
  2. `Unified RBAC Gateway dependency on the telemetry API` (Dependency / High)
  3. `Insufficient backend developer availability` (Resource / High)
  4. `Budget constraint and increasing infrastructure costs` (Budget / High)
  5. `Integration testing not started` (Delivery / High)
- **Unique Identification & Metadata Grounding:** Each finding is assigned a unique identifier (`RSK-001` through `RSK-005`), a specific title, an affected deliverable/milestone, potential impact analysis, suggested mitigation aligned with project context, and a recommended priority.
- **Dependency & Blocked Upstream Tracking:** Detects prerequisite relationships (e.g., `Cloud Telemetry Pipeline API -> Unified RBAC Gateway`, status `Blocked`), populating both the `risks` collection and `dependency_gaps`.
- **Resource Constraint Detection:** Detects developer capacity limitations (`Only one backend developer is available to work on the RBAC Gateway and dashboard integration.`), populating both `risks` and `resource_constraints`.
- **Budget Constraint Detection:** Identifies remaining budget limits against increasing infrastructure expenditures (`10 percent remaining, while cloud infrastructure costs are increasing`), incrementing `budget_risks_count`.
- **Delivery Forecasting & Deadline Differentiation:**
  - **Overdue Deliverable vs. Upcoming Milestone:** Accurately distinguishes an overdue deadline (`Cloud Telemetry Pipeline` scheduled for `2026-11-20`, incomplete as of current date `2026-11-22`, Critical severity) from potential schedule impacts on future deadlines (`2026-12-15` project delivery deadline, High severity).
  - **Anti-Hallucination:** Strictly avoids inventing generic milestone placeholders such as `"Upcoming Project Milestone"`. Names are drawn from confirmed entities or the project title.
- **Evidence Snippet Conciseness:** Supporting evidence snippets contain only the focused risk sentence/context (<250 characters) and never absorb the entire input document.
- **Overall Risk Level Calculation:** Accurately evaluates to `Critical` due to the confirmed presence of an overdue deliverable, with a detailed `delivery_concerns_summary`.
- **Reporting Consistency Improvements:**
  - **Accurate Category Breakdown in Delivery Concerns Summary:** Dynamic category counting guarantees that the breakdown matches the exact categories of the five extracted risk findings (`"5 risk findings: 1 schedule, 1 budget, 1 dependency, 1 resource, 1 delivery"`). Additional operational concerns (e.g. prospective impact on the 2026-12-15 delivery deadline) are cited separately without distorting the finding count.
  - **Resource Bottleneck Population:** `potential_bottlenecks` is now properly populated with a concise description of the developer availability constraint (`"Single backend developer bottleneck: only one backend developer is available to work on the RBAC Gateway and dashboard integration."`), preventing the bottlenecks collection from being empty when single-developer constraints are documented.

### 5.5 Blocker & Action Item Agent Accuracy Validation (`POST /api/agents/identify-blockers`)

#### Root Cause of Extraction Failure
1. **Sentence Boundary Agglomeration:** `BlockerAgent` previously expected explicit markdown section headings (`Current Blockers:`, `Action Items:`) or newline-separated items. Unstructured paragraphs and single-line continuous Swagger inputs had no section headers and no newlines, causing the entire document to be treated as a single line.
2. **Delayed Activity Ingestion:** Because the single line contained `"delayed"`, the agent captured the entire document paragraph as a single `DelayedActivity` description.
3. **Missing Conversational & Modal Keyword Recognizers:** The agent lacked recognizers for common narrative and meeting phrases such as `must complete`, `must prepare`, `cannot start ... until`, `has not decided whether to use ... or ...`, `pending from`, and `reported that`. Consequently, all other arrays (`blockers`, `unresolved_issues`, `pending_decisions`, `action_items`, `dependencies_requiring_attention`, `recommended_next_steps`) returned empty.

#### Technical Corrections Implemented
1. **Period-Boundary Sentence Pre-Normalization:** Normalized sentence breaks on `([a-zA-Z0-9\)])\.\s+(?=[A-Z0-9#\-\*])` so continuous single-line paragraphs parse cleanly into distinct sentences.
2. **Individual Blocker Extraction:**
   - Detects `delayed because ... incomplete` $\rightarrow$ `Authentication testing incomplete, blocking the Cloud Telemetry Pipeline API.` (Affected: `Cloud Telemetry Pipeline API`, Owner: `Unassigned`).
   - Detects `cannot start ... until` $\rightarrow$ `RBAC integration blocked until telemetry API is available.` (Affected: `RBAC integration`, Owner: `Bob Martinez`).
   - Detects `pending from` $\rightarrow$ `Data warehouse credentials pending from the infrastructure team.` (Affected: `Data warehouse integration`, Owner: `Infrastructure Team`).
3. **Unresolved Issues Detection:** Accurately extracts `Authentication testing remains incomplete.` and `Data warehouse credentials have not yet been received.`.
4. **Pending Decisions Detection:** Identifies `Selection between Redis and RabbitMQ for event processing.` without choosing either option automatically.
5. **Delayed Activities Refinement:** Isolates delayed activity to `Cloud Telemetry Pipeline API completion, delayed because authentication testing is incomplete.` (Reason: `authentication testing is incomplete.`) with a concise evidence snippet, eliminating paragraph-wide copying.
6. **Action Items Extraction with Role & Modal Parsing:**
   - Detects `[Person/Role] must [action] by [deadline]`.
   - Extracts:
     - `Alice Chen` – `Complete authentication testing` – Deadline: `2026-11-24` (Priority: `Critical`).
     - `Carol Vance` – `Prepare dashboard integration tests` – Deadline: `2026-11-25` (Priority: `High`).
     - `Project Manager` – `Schedule dependency review meeting` – Deadline: `2026-11-23` (Priority: `High`).
   - Associates `David Kim` with reporting the pending credentials issue without fabricating an action item or deadline.
7. **Dependencies Requiring Attention:** Extracts `Cloud Telemetry Pipeline API → RBAC integration (Status: Blocked - RBAC integration cannot begin until the telemetry API is available)`.
8. **Recommended Next Steps:** Generates five evidence-based recommendations:
   1. `Complete authentication testing.`
   2. `Resolve the telemetry API blocker.`
   3. `Obtain data warehouse credentials.`
   4. `Finalize the Redis/RabbitMQ decision.`
   5. `Schedule the dependency review meeting.`

#### Before-and-After Comparison

| Metric / Collection | Before Fix (Live Swagger Test) | After Fix (Verified Output) |
|---|---|---|
| `blockers` | `0` (Empty) | `3` (`Authentication testing`, `RBAC integration`, `Data warehouse credentials`) |
| `unresolved_issues` | `0` (Empty) | `2` (`Authentication testing incomplete`, `Credentials not received`) |
| `pending_decisions` | `0` (Empty) | `1` (`Selection between Redis and RabbitMQ for event processing`) |
| `delayed_activities` | `1` (Entire paragraph copied: ~700 chars) | `1` (Concise: `Cloud Telemetry Pipeline API completion...`, 78 chars) |
| `action_items` | `0` (Empty) | `3` (`Alice Chen`, `Carol Vance`, `Project Manager`) |
| `dependencies_requiring_attention` | `0` (Empty) | `1` (`Cloud Telemetry Pipeline API → RBAC integration`, Status: `Blocked`) |
| `recommended_next_steps` | `0` (Empty) | `5` (Targeted recommendations addressing each issue) |

### 5.6 Blocker Agent Deduplication, Document Classification & Evidence Provenance Refinement

Targeted improvements and 13 comprehensive regression tests were implemented to resolve extraction quality, cross-document duplication, document classification, and evidence provenance issues:

1. **Normalized Deduplication Across All Collections:**
   - **Key Canonicalization:** Normalizes whitespace, bullet markers (`-`, `*`, `•`), enumeration labels (`Blocker 1:`, `Issue 2:`, `Row N:`), punctuation, and semantic equivalents (e.g., `ClickHouse vs Snowflake` vs. `Selection between ClickHouse and Snowflake for warm-storage analytics`).
   - **Cross-Document Merging:** When an entity (such as the SecOps OAuth blocker or warm-storage decision) appears across both `meeting_notes.txt` and `task_list.csv`, the findings are merged into a single canonical entry rather than producing duplicate entries (`BLK-001` vs `BLK-002`).
   - **Evidence Snippet Consolidation:** Merged findings retain supporting evidence snippets from each distinct source document rather than dropping provenance or duplicating findings.

2. **Accurate Blocker Identification & False Positive Prevention:**
   - Identifies genuine blockers from explicit narrative blocks, meeting notes, and structured task rows with blocker notes (`Blocked by security compliance review`, `Database migration scripts failing on staging cluster`, `Staging cluster memory out-of-bounds crashes halting integration tests`).
   - Populates `affected_activities` cleanly (e.g., `Ingestion pipeline`, `Database migration scripts`, `Integration tests`).
   - Normalizes titles to strip redundant enumeration labels (`Blocker 1:`, `Current Blocker:`).
   - Standard task-table rows are not classified as blockers unless explicit notes indicate an active blocker or failure condition.

3. **Unresolved Issues vs. Blockers Separation:**
   - Detects genuine technical defects and operational issues (e.g., `cross-region latency spikes exceeding 1200ms`, `token refresh failure modes`, `flaky integration tests`).
   - Excludes non-issues such as completed tasks, ordinary task rows, project titles, report headings, and out-of-scope clauses.

4. **Pending Decisions Neutrality & Owner Preservation:**
   - Accurately captures open architectural and technical choices (e.g., `ClickHouse vs Snowflake`, `Kafka partition retention sizing`, `Redis vs RabbitMQ`).
   - Strips numbering and prefix labels while preserving decision makers (`David Kim`, `Alice Chen`) and deadlines (`2026-09-25`).
   - Strictly neutral: never automatically resolves or selects an option.

5. **Delayed Activities Refinement:**
   - Extracts genuine delayed activities and their root-cause reasons.
   - Rejects generic delivery impact statements (`Project delivery may be delayed...`) from being misclassified as delayed activity items.

6. **Structured CSV Task Extraction & Concise Descriptions:**
   - For CSV task rows (`Row N: Task ID: ...; Task Name: ...`), extracts concise task names (e.g., `Configure RBAC OAuth Gateway`) instead of swallowing the full semicolon-delimited row string into the description.
   - Maps status, priority, deadline, and assigned owner faithfully.
   - Strictly excludes `Status: Completed` rows (`Deploy Kafka Ingestion Brokers`) from action items and issues.
   - For narrative/meeting notes items, removes `Action Item N:` prefixes and formats clean, actionable descriptions (`Submit SecOps compliance exception ticket`, `Mock dashboard response models`).

7. **Multi-Document Evidence & Chunk Provenance:**
   - Introduced `DocumentChunkContext` across chunk processing so that each extracted item and supporting evidence snippet accurately references its true originating document (`task_list.csv`, `meeting_notes.txt`, `progress_report.docx`) rather than attributing all items to a single global source.

8. **Deduplicated Grounded Next Steps:**
   - Generates actionable, prioritized, and deduplicated recommendations grounded in confirmed blockers and decisions.
   - Rejects duplicate recommendations when similar issues are cited across multiple sections.

### 5.6 Cross-Agent Canonical Deduplication & Multi-Document Chunk Provenance

To support end-to-end multi-document RAG over heterogeneous formats (PDF, DOCX, CSV, TXT):
- **Centralized Canonical Normalizer:** `normalize_content_key(text)` in `agent_utils.py` removes enumerations, formatting prefixes, bullet points, punctuation, and whitespace variations to enable robust cross-document entity deduplication.
- **Multi-Document Chunk Provenance:** `DocumentChunkContext` preserves chunk ID, document ID, filename, text, and cosine similarity for each retrieved chunk.
- **Risk Agent Evidence Attribution:** Risks detected across different document chunks (e.g., budget overrun in both `progress_report.docx` and `task_list.csv`) merge into a single canonical finding while retaining distinct supporting evidence citations referencing each actual source file.
- **Scope Agent Chunk Context:** Deliverables and milestones accurately link evidence excerpts to their specific originating document (`project_charter.pdf`, `project_proposal.txt`, `task_list.csv`).

### 5.7 Agent Orchestrator Resilience & Parameter Propagation

- **Failure Isolation:** `AgentOrchestratorService` wraps each agent call in an isolated `try...except` block. If an individual agent encounters a failure, a graceful fallback response is generated, health calculation proceeds with available data, and the pipeline avoids raising HTTP 500.
- **Query & Document Filter Propagation:** `MultiAgentAnalysisRequest` accepts an optional `query` string and `document_ids` list, which are faithfully propagated to child agents and RAG retrieval.
- **Automated Verification:** 3 new integration tests in `test_agent_orchestrator.py` verify failure isolation, parameter propagation, and end-to-end multi-format pipeline execution, expanding the test suite to 102 passing tests.

---

## 6. Known Limitations

1. **Non-Standard Free-Form Formats:** Documents that do not utilize any headings, bullet points, colons, or standard organizational indicators may yield lower extraction confidence.
2. **Scanned Images / Handwritten Notes:** Milestone 1 & 2 ingestion operates on direct digital text in PDF/DOCX/CSV/TXT; scanned PDF bitmaps require external OCR.
3. **Multi-Tenant Scoping:** The current vector database persists all chunks into the local `project_chunks` collection. Future multi-tenant milestones can introduce project-partitioned collection namespaces.
