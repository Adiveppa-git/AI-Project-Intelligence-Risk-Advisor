# AI-Driven Enterprise Project Intelligence & Risk Management Platform

An enterprise AI platform that ingests unstructured and structured project documentation (PDF, DOCX, CSV, Plain TXT), generates dense semantic vector representations using local sentence-transformers, indexes chunks in persistent ChromaDB storage, and deploys a specialized multi-agent cognitive architecture to automate scope extraction, risk detection, delivery forecasting, and blocker identification.

---

## Table of Contents

1. [Project Purpose & Value Proposition](#1-project-purpose--value-proposition)
2. [System Architecture & Multi-Agent Design](#2-system-architecture--multi-agent-design)
3. [Technology Stack](#3-technology-stack)
4. [Repository & Directory Structure](#4-repository--directory-structure)
5. [Environment Setup & Installation](#5-environment-setup--installation)
6. [Backend Startup & Execution](#6-backend-startup--execution)
7. [API Reference & Usage](#7-api-reference--usage)
8. [Document Ingestion & RAG Indexing Flow](#8-document-ingestion--rag-indexing-flow)
9. [AI Agent Execution & Capabilities](#9-ai-agent-execution--capabilities)
10. [Automated Testing & Verification](#10-automated-testing--verification)
11. [Current Implementation Limitations & Future Roadmap](#11-current-implementation-limitations--future-roadmap)

---

## 1. Project Purpose & Value Proposition

Enterprise software engineering initiatives routinely generate vast quantities of fragmented, cross-functional documentation: formal project charters, Software Requirement Specifications (SRS), sprint meeting minutes, Jira/Excel task export tables, and executive progress reports.

Engineering leaders and project management offices (PMOs) struggle to manually cross-reference these artifacts. The consequences are missed delivery dependencies, untracked scope creep, unassigned action items, and surprise budget overruns.

This platform bridges that gap by providing:
- **Universal Multi-Format Ingestion:** Digital parsing for PDF, Word (.docx), CSV spreadsheets, and Plain Text (.txt) with security limits and metadata preservation.
- **Explainable, Grounded RAG Pipeline:** Semantic vector search (384-dimensional cosine similarity via `all-MiniLM-L6-v2`) ensuring all extracted intelligence is directly grounded in source document snippets.
- **Interconnected Multi-Agent Architecture:** Autonomous agents for Project Scope extraction, Risk & Delivery Forecasting, and Blocker/Action Item tracking.
- **Cross-Functional Synthesis:** An orchestrator service that consolidates findings into an executive report with project health scoring and actionable management next steps.

---

## 2. System Architecture & Multi-Agent Design

The platform uses a modular 4-tier architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API Layer                          │
│   /health   /api/documents/upload   /api/rag/*   /api/agents/*         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Multi-Agent Orchestrator Service                    │
│   Consolidated Reporting | Health Scoring | Failure Isolation          │
└─────────┬─────────────────────────┬──────────────────────────┬─────────┘
          │                         │                          │
          ▼                         ▼                          ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   ScopeAgent     │      │    RiskAgent     │      │   BlockerAgent   │
│ - Scope & Goals  │      │ - Schedule Risks │      │ - Active Blockers│
│ - In/Out Scope   │      │ - Dependencies   │      │ - Action Items   │
│ - Deliverables   │      │ - Budget Overruns│      │ - Decisions      │
│ - Milestones     │      │ - Bottlenecks    │      │ - CSV Rows / Prio│
└─────────┬────────┘      └─────────┬────────┘      └─────────┬────────┘
          │                         │                          │
          └─────────────────────────┼──────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline Foundation                         │
│  Ingestion Engine (PDF/DOCX/CSV/TXT)  ->  Boundary Chunking (1000/150) │
│  Sentence-Transformers (384-d L2 Norm) -> Persistent ChromaDB Storage  │
└────────────────────────────────────────────────────────────────────────┘
```

### Specialized Agents:
1. **Scope and Deliverable Extraction Agent (`ScopeAgent`):** Identifies concise project titles, objectives, goals, in-scope/out-of-scope boundaries, deliverables, milestones, deadlines, start/end dates, and team responsibilities. Never hallucinates non-existent owners or dates.
2. **Risk Detection and Delivery Forecasting Agent (`RiskAgent`):** Analyzes documents for schedule risks, missed deadlines, dependency gaps, resource constraints, budget overruns, and delivery challenges. Classifies severity (`Critical`, `High`, `Medium`, `Low`) and forecasts milestone delivery concerns grounded in documented evidence.
3. **Blocker and Action Item Identification Agent (`BlockerAgent`):** Identifies active blockers, unresolved defects, pending decisions with decision-makers, delayed activities, and action items with owners, deadlines, priority, and status. Automatically filters report headings and completed tasks.
4. **Multi-Agent Orchestrator Service (`AgentOrchestratorService`):** Coordinates multi-document retrieval across agents with individual failure isolation, computes project health (`Healthy`, `Needs Attention`, `At Risk`, `Critical`), generates executive summaries, and synthesizes key recommendations.

---

## 3. Technology Stack

- **Backend Framework:** FastAPI 0.115+, Uvicorn (ASGI)
- **Document Parsers:**
  - PDF: PyMuPDF (`fitz` / `pymupdf` 1.24+)
  - DOCX: `python-docx` 1.1+ (with zip bomb & XML entity expansion guards)
  - CSV: Python native CSV module (labeled record generation)
  - TXT: Native UTF-8 engine (with UTF-8-BOM support)
- **NLP & Embedding Engine:** HuggingFace `sentence-transformers` 3.0+ (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, normalized embeddings)
- **Vector Database:** ChromaDB 0.5+ (Persistent SQLite / HNSW cosine space)
- **Data Validation & Schemas:** Pydantic v2
- **Testing:** Pytest 8.4+, HTTPX, FastAPI TestClient

---

## 4. Repository & Directory Structure

```
AI-Project-Intelligence-Risk-Advisor/
├── .gitignore                          # Git ignore rules for virtualenvs, cache, vector DB
├── .env.example                        # Template environment configuration
├── README.md                           # Main architectural documentation and usage guide
├── backend/
│   ├── .env.example                    # Backend environment defaults
│   ├── README.md                       # Backend-specific instructions
│   ├── requirements.txt                # Pinned dependency requirements
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application factory & route mounts
│   │   ├── agents/                     # Specialized cognitive agents
│   │   │   ├── __init__.py
│   │   │   ├── agent_utils.py          # Provenance tracking, date parsing, section blocks
│   │   │   ├── blocker_agent.py        # Blocker & Action Item Agent
│   │   │   ├── risk_agent.py           # Risk Detection & Delivery Forecasting Agent
│   │   │   └── scope_agent.py          # Scope & Deliverable Extraction Agent
│   │   ├── api/                        # REST API routers
│   │   │   ├── __init__.py
│   │   │   ├── agent_routes.py         # /api/agents/* endpoints
│   │   │   ├── rag_routes.py           # /api/rag/* endpoints
│   │   │   └── routes.py               # /api/documents/* endpoints
│   │   ├── models/                     # Pydantic data schemas
│   │   │   ├── __init__.py
│   │   │   ├── agent_models.py         # Multi-agent requests, reports, findings, evidence
│   │   │   ├── document.py             # Ingestion document models
│   │   │   └── rag.py                  # Chunks, vector search results, RAG status
│   │   └── services/                   # Core business logic services
│   │       ├── __init__.py
│   │       ├── agent_orchestrator.py   # Multi-agent coordinator & synthesizer
│   │       ├── chunking.py             # Boundary-aware chunker (1000/150)
│   │       ├── document_ingestion.py   # PDF, DOCX, CSV, TXT ingestion service
│   │       ├── embeddings.py           # Sentence-Transformers service
│   │       ├── rag_pipeline.py         # End-to-end RAG indexing & retrieval
│   │       └── vector_store.py         # ChromaDB persistence adapter
│   ├── data/                           # Local vector DB data storage
│   │   └── chroma/                     # Chroma SQLite & HNSW files
│   ├── sample_data/                    # Multi-format enterprise test dataset
│   │   ├── project_charter.pdf         # Official PDF charter
│   │   ├── progress_report.docx        # Progress report with status tables & delay warnings
│   │   ├── task_list.csv               # Operational spreadsheet with task priorities & blockers
│   │   ├── meeting_notes.txt           # Sprint sync minutes with blockers, issues, decisions
│   │   └── project_proposal.txt        # Full project charter text
│   └── tests/                          # Automated Pytest test suite (102 tests)
│       ├── test_agent_api.py           # Agent API endpoint tests
│       ├── test_agent_orchestrator.py  # Orchestrator & E2E pipeline tests
│       ├── test_blocker_agent.py       # Blocker agent extraction & deduplication tests
│       ├── test_chunking.py            # Chunker boundary & overlap tests
│       ├── test_document_ingestion.py  # Ingestion & parser validation tests
│       ├── test_rag_integration.py     # Embedding & ChromaDB vector tests
│       ├── test_risk_agent.py          # Risk agent detection & forecasting tests
│       └── test_scope_agent.py         # Scope agent extraction tests
└── docs/                               # Official project documentation
    ├── COMPLETE_MILESTONE_AUDIT.md     # Deep audit of all M1 & M2 requirements
    ├── DATA_MODEL_DESIGN.md            # Detailed schema design documentation
    ├── FINAL_MILESTONE_1_2_COMPLETION_REPORT.md # Final sign-off & acceptance report
    ├── MILESTONE_1_AUDIT.md            # Milestone 1 audit record
    ├── MILESTONE_2_ARCHITECTURE.md     # Milestone 2 architecture specification
    ├── MILESTONE_2_IMPLEMENTATION.md   # Milestone 2 implementation guide
    ├── MILESTONE_2_VALIDATION.md       # Milestone 2 empirical validation findings
    ├── STEP1_LEARNING_NOTES.md         # Learning notes: RAG, agents, project management
    ├── STEP2_SYSTEM_ARCHITECTURE.md    # High-level architecture specification
    ├── STEP3_DOCUMENT_INGESTION.md     # Document ingestion guide
    ├── STEP4_RAG_PIPELINE.md           # RAG pipeline implementation notes
    └── diagrams/                       # Architecture diagrams (Mermaid source)
```

---

## 5. Environment Setup & Installation

### Prerequisites
- Python 3.10.x or later installed.
- Git.

### Step 1: Clone Repository
```powershell
git clone https://github.com/Adiveppa-D-Mamadapur/AI-Project-Intelligence-Risk-Advisor.git
cd AI-Project-Intelligence-Risk-Advisor
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
backend\.venv\Scripts\python -m pip install --upgrade pip
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### Step 4: Environment Variables (Optional)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default parameters configured:
- `RAG_CHUNK_SIZE=1000`
- `RAG_CHUNK_OVERLAP=150`
- `RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`
- `RAG_VECTOR_DB_PATH=backend/data/chroma`
- `RAG_COLLECTION_NAME=project_chunks`

---

## 6. Backend Startup & Execution

Start the FastAPI application:
```powershell
$env:PYTHONPATH='backend'
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Access the service:
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc API Documentation: `http://127.0.0.1:8000/redoc`
- Service Health Check: `http://127.0.0.1:8000/health`
- Agent Readiness Status: `http://127.0.0.1:8000/api/agents/status`

---

## 7. API Reference & Usage

### 7.1 Health & Status Endpoints
- `GET /health`: Returns service operational status (`{"status": "ok"}`).
- `GET /api/rag/status`: Reports vector store readiness, indexed chunk count, embedding model metadata, and persistence path.
- `GET /api/agents/status`: Reports availability of all three agents, RAG readiness, and indexed knowledge statistics.

### 7.2 Ingestion & RAG Endpoints
- `POST /api/documents/upload` (`multipart/form-data`):
  Uploads any PDF, DOCX, CSV, or TXT document (up to 10 MB). Validates structure, extracts clean UTF-8 text, and returns an `IngestedDocument` with metadata.
- `POST /api/rag/index` (`multipart/form-data`):
  Uploads, extracts, chunks, generates normalized dense embeddings, and upserts vectors idempotently into persistent ChromaDB storage.
- `POST /api/rag/search` (`application/json`):
  Performs semantic similarity query:
  ```json
  {
    "query": "What are the active schedule delay risks and blockers?",
    "top_k": 5
  }
  ```

### 7.3 Multi-Agent Analysis Endpoints
- `POST /api/agents/analyze-scope` (`application/json`):
  Executes `ScopeAgent` to extract goals, in/out of scope items, deliverables, milestones, deadlines, and responsibilities.
- `POST /api/agents/detect-risks` (`application/json`):
  Executes `RiskAgent` to detect schedule, dependency, resource, budget, and delivery risks, severity levels, and forecasts.
- `POST /api/agents/identify-blockers` (`application/json`):
  Executes `BlockerAgent` to identify blockers, unresolved defects, pending decisions, delayed tasks, and action items.
- `POST /api/agents/analyze-project` (`application/json`):
  Executes `AgentOrchestratorService` across all three agents, returning a consolidated `ProjectIntelligenceReport` with health scoring, executive summary, and recommendations:
  ```json
  {
    "query": "Enterprise Cloud Analytics Platform status and risks",
    "top_k": 15
  }
  ```

---

## 8. Document Ingestion & RAG Indexing Flow

1. **Upload:** Client transmits file through `/api/documents/upload` or `/api/rag/index`.
2. **Security & Type Validation:**
   - Validates file extensions (`.pdf`, `.docx`, `.csv`, `.txt`).
   - Rejects empty uploads, binary files with null bytes, and files exceeding 10 MB.
   - Guard against DOCX decompression zip bombs (>50 MB uncompressed limit) and XML entity expansion.
3. **Structured Text Extraction:**
   - **PDF:** Extracted page-by-page using PyMuPDF (`fitz`).
   - **DOCX:** Extracted paragraph-by-paragraph and table cells (`python-docx`).
   - **CSV:** Labeled row extraction (`Row N: Column A: Value A; Column B: Value B`).
   - **TXT:** UTF-8 / UTF-8-BOM decoded text.
4. **Chunking Engine:** Splits text into 1,000-character segments with 150-character boundary overlap, searching backward for sentence ends (`. `, `\n\n`) and word boundaries.
5. **Vector Embedding:** Encodes chunks with `all-MiniLM-L6-v2` into 384-dimensional unit-normalized vectors.
6. **Persistent Indexing:** Upserts vectors and metadata into local ChromaDB with SHA-256 stable document IDs ensuring idempotent re-indexing.

---

## 9. AI Agent Execution & Capabilities

### Deduplication and Normalization
Findings across multi-document runs (e.g. blockers mentioned in both meeting notes and task tables) are normalized via `normalize_content_key`, stripping enumeration labels, bullet prefixes, and punctuation. Duplicate findings are merged into a canonical item while consolidating all distinct source evidence snippets.

### Anti-Hallucination & Evidence Provenance
- Agents never invent non-existent dates (defaulting to `"Not specified"`).
- Agents never invent fictitious owners (defaulting to `"Unassigned"` or `"Unknown"`).
- Every finding includes `supporting_evidence` preserving the originating `filename`, `document_id`, and `snippet`.

---

## 10. Automated Testing & Verification

The repository contains 102 automated tests executed with Pytest:

```powershell
$env:PYTHONPATH='backend'
backend\.venv\Scripts\pytest backend/tests -v
```

### Test Suite Summary:
- `backend/tests/test_document_ingestion.py` (22 tests): Tests PDF, DOCX, CSV, TXT parsing, empty files, corrupt files, size limits.
- `backend/tests/test_chunking.py` (9 tests): Tests boundary-aware chunking, character offsets, overlap repetition.
- `backend/tests/test_rag_integration.py` (6 tests): Tests SentenceTransformer embeddings, ChromaDB persistence, idempotent re-indexing, semantic search.
- `backend/tests/test_scope_agent.py` (17 tests): Tests project title isolation, scope boundaries, deliverables, milestones, responsibilities, Swagger single-line scenarios.
- `backend/tests/test_risk_agent.py` (9 tests): Tests schedule risks, dependency gaps, resource bottlenecks, budget overruns, delivery forecasting.
- `backend/tests/test_blocker_agent.py` (22 tests): Tests active blockers, action items, CSV task parsing, completed task exclusion, deduplication, provenance.
- `backend/tests/test_agent_orchestrator.py` (6 tests): Tests orchestrator coordination, health scoring, failure isolation, document_id/query propagation, and full end-to-end multi-format pipeline.
- `backend/tests/test_agent_api.py` (11 tests): Tests live FastAPI agent endpoints.

**Result: 102 passed, 0 failed, 1 warning (starlette deprecation)** in ~30s.

---

## 11. Current Implementation Limitations & Future Roadmap

### Current Limitations:
1. **Scanned PDF Bitmaps:** Operates on direct digital text; scanned PDF images require an external OCR pre-processor (e.g. Tesseract).
2. **Multi-Tenant Partitioning:** Current local ChromaDB persists all documents into a single collection namespace (`project_chunks`).

### Tracked Future Modules (Milestone 3 / Milestone 4):
- **Automated Documentation Generation:** Automated generation of formal project charters, risk registers, and release notes in Markdown/PDF.
- **Dynamic Project Health Scoring:** Advanced algorithmic health metrics factoring in blocker severity, budget burn velocity, and sprint burndown.
- **Conversational Project Assistant:** Interactive natural language Q&A agent with chat memory for stakeholder inquiries.
- **Executive Insights Dashboard:** Web frontend visualization for real-time risk heatmaps, milestone Gantt projections, and blocker dependency graphs.

---

## License

This project is developed for the Infosys Springboard Internship Program. All rights reserved.
