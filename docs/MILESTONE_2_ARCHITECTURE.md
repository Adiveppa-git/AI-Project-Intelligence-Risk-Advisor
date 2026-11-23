# Milestone 2 System Architecture: Multi-Agent AI Project Intelligence & Risk Advisor

## 1. Architectural Overview

Milestone 2 extends the foundational document ingestion and Retrieval-Augmented Generation (RAG) platform into an interconnected, multi-agent AI intelligence platform. The architecture decomposes complex project analysis into three specialized, autonomous agents coordinated by a central orchestrator.

The system is designed to work completely locally without requiring paid external API keys, utilizing explainable rule-based pattern recognition, deterministic semantic RAG retrieval, and strict anti-hallucination constraints.

```
                              +---------------------------------------+
                              |      FastAPI Application Layer        |
                              | (/api/agents/*, /api/rag/*, /health)  |
                              +---------------------------------------+
                                                  |
                                                  v
                              +---------------------------------------+
                              |       Agent Orchestrator Service       |
                              |    (Multi-Agent Coordination & Flow)  |
                              +---------------------------------------+
                                     /            |            \
                                    /             |             \
                                   v              v              v
            +------------------------+  +-------------------+  +-------------------------+
            |      Scope Agent       |  |    Risk Agent     |  |      Blocker Agent      |
            | (Goals, Deliverables,  |  | (Risk Detection & |  | (Impediments, Decisions,|
            |  Milestones, Owners)   |  |  Delivery Forecast|  |  Action Items, Issues) |
            +------------------------+  +-------------------+  +-------------------------+
                                   \              |              /
                                    \             |             /
                                     v            v            v
                              +---------------------------------------+
                              |      RAG Knowledge Base & Store       |
                              | (Sentence Transformers + ChromaDB)   |
                              +---------------------------------------+
                                                  |
                                                  v
                              +---------------------------------------+
                              |     Document Ingestion Service        |
                              |   (PDF, DOCX, CSV, UTF-8 TXT)         |
                              +---------------------------------------+
```

---

## 2. Agent Responsibilities & Interaction Contracts

### 2.1 Scope and Deliverable Extraction Agent (`ScopeAgent`)
- **Primary Goal:** Extract project commitments, timeline boundaries, and operational deliverables.
- **Key Extractions:**
  - Project Title & High-level Objectives.
  - In-Scope vs. Out-of-Scope boundaries.
  - Expected Deliverables with identified owners, deadlines, and current status.
  - Project Milestones with target dates, owners, and deliverable associations.
  - Project Start Date, Target End Date, and critical milestone deadlines.
  - Team Responsibilities mapping roles and individuals to project tracks.
- **RAG & Evidence:**
  - Semantic query targeting project charter, milestones, deliverables, and team responsibilities.
  - Attaches `SourceEvidence` snippets and confidence scores to every extracted entity.
  - Enforces negative constraints: never fabricates dates or owners; unassigned or missing fields are marked as `"Unknown"` or `"Not specified"`.

### 2.2 Risk Detection and Delivery Forecasting Agent (`RiskAgent`)
- **Primary Goal:** Identify latent and explicit threats to project success and forecast milestone delivery impact.
- **Key Extractions:**
  - Schedule risks, approaching deadlines, and delays.
  - Dependency gaps (upstream bottlenecks, external approvals, third-party APIs).
  - Resource constraints (understaffed tracks, key-person dependencies).
  - Budget-related risks (cost overruns, unbudgeted infrastructure spend).
  - Technical bottlenecks and delivery challenges.
- **Severity Classification:**
  - **Critical:** Blockers halting releases, major delivery failures, or severe budget deviations.
  - **High:** Core dependency gaps, slipping primary milestones, or persistent pipeline failures.
  - **Medium:** Moderate delays, resource bandwidth strain, or non-critical defects.
  - **Low:** Minor backlog drift or cosmetic issues.
- **Delivery Forecasting Engine:**
  - Correlates documented schedule delays with baseline milestone target dates (provided via `ScopeAnalysisResult`).
  - Distinguishes confirmed target deadlines from predicted delay causes.
  - Does not emit fabricated future calendar dates without explicit textual justification.

### 2.3 Blocker and Action Item Identification Agent (`BlockerAgent`)
- **Primary Goal:** Extract current impediments and actionable follow-ups from meeting minutes, sprint logs, and progress reports.
- **Key Extractions:**
  - Current Blockers & Impediments (active vs. resolved).
  - Unresolved Technical Issues & Defect Reports.
  - Pending Decisions with assigned decision-makers and target deadlines.
  - Delayed Activities and root causes.
  - Action Items with assigned owners, deadlines, priority levels, and completion status.
- **Anti-Hallucination & Integrity:**
  - Distinguishes completed (`[x]`) vs. pending (`[ ]`) action items.
  - Identifies unassigned tasks and surfaces `unassigned_action_items_count`.
  - Links action items to related blockers where contextual matches exist.

---

## 3. Multi-Agent Orchestration & Workflow

The `AgentOrchestratorService` executes the coordination workflow:

1. **Ingestion & Knowledge Base Preparation:** Project documents (proposals, meeting notes, progress reports, task spreadsheets) are uploaded, validated, chunked, and embedded into persistent ChromaDB storage.
2. **Phase A - Upstream Extraction:** Orchestrator queries the RAG store or provided text using high-recall semantic prompts, triggering:
   - `ScopeAgent` to establish baseline project title, goals, deliverables, and milestones.
   - `BlockerAgent` to identify active blockers, pending decisions, and action items.
3. **Phase B - Correlated Risk & Forecast Analysis:** Orchestrator invokes `RiskAgent`, supplying the `ScopeAnalysisResult` context. The Risk Agent correlates detected delays and blockers against confirmed milestone targets to generate evidence-backed delivery forecasts.
4. **Phase C - Consolidation & Health Scoring:**
   - Evaluates overall project health:
     - **Critical:** Presence of Critical risks or unresolved Critical blockers.
     - **At Risk:** High overall risk level or $\ge 3$ active blockers.
     - **Needs Attention:** Medium risk level or unassigned action items.
     - **Healthy:** All deliverables on track with no severe blockers.
   - Synthesizes an executive summary and actionable recommendations prioritizing unblocking critical items, assigning orphan actions, and resolving pending decisions.

---

## 4. API Endpoints

The API is exposed under `/api/agents` via FastAPI:

| Method | Endpoint | Description | Response Model |
|---|---|---|---|
| `POST` | `/api/agents/analyze-scope` | Run Scope & Deliverable Agent independently | `ScopeAnalysisResult` |
| `POST` | `/api/agents/detect-risks` | Run Risk & Delivery Forecast Agent independently | `RiskAnalysisResult` |
| `POST` | `/api/agents/identify-blockers` | Run Blocker & Action Item Agent independently | `BlockerAnalysisResult` |
| `POST` | `/api/agents/analyze-project` | Run full multi-agent orchestration pipeline | `ProjectIntelligenceReport` |
| `GET` | `/api/agents/status` | Health check for all agents and RAG vector store | `AgentStatusResponse` |

---

## 5. Security, Traceability, and Non-Functional Principles

- **No Paid APIs:** Utilizes local CPU-based SentenceTransformers (`all-MiniLM-L6-v2`) and explainable rule-based heuristic extraction. No OpenAI/Anthropic API keys required.
- **Source Traceability:** Every extracted milestone, risk, blocker, and action item carries a `SourceEvidence` payload containing the source document name, document ID, chunk ID, and exact textual snippet.
- **Idempotency:** Vector upserts and deterministic chunk IDs ensure re-indexing documents does not produce duplicate entities.
- **Strict Validation:** All endpoints validate inputs using Pydantic models with defensive defaults.
