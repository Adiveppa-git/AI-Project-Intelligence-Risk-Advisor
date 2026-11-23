# Backend: AI Project Intelligence & Risk Advisor

This Python backend implements document ingestion, local RAG vector retrieval, and a multi-agent AI system for enterprise project intelligence, deliverable tracking, risk detection, delivery forecasting, and blocker resolution.

---

## Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

## Environment Configuration

A template configuration is provided in `backend/.env.example` (and repository root `.env.example`):

```powershell
cp backend/.env.example backend/.env
```

Configurable variables:
- `RAG_CHUNK_SIZE`: Maximum chunk size in characters (default: `1000`)
- `RAG_CHUNK_OVERLAP`: Overlap between adjacent chunks (default: `150`)
- `RAG_EMBEDDING_MODEL`: Hugging Face model ID or path (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `RAG_VECTOR_DB_PATH`: Persistent ChromaDB storage path (default: `backend/data/chroma`)
- `RAG_COLLECTION_NAME`: ChromaDB collection name (default: `project_chunks`)
- `MAX_UPLOAD_SIZE_BYTES`: Max file upload limit in bytes (default: `10485760` = 10 MB)

## Install

From the project root:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

---

## Run the API

From the project root:

```powershell
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

The service is available at `http://127.0.0.1:8000`.
- Interactive OpenAPI docs: `http://127.0.0.1:8000/docs`
- Service health check: `http://127.0.0.1:8000/health`
- Agent status check: `http://127.0.0.1:8000/api/agents/status`

---

## Milestone 1 Endpoints (Document Ingestion & RAG Foundation)

- `POST /api/documents/upload`: Upload and extract text from PDF, DOCX, CSV, or UTF-8 TXT.
- `POST /api/rag/index`: Ingest, chunk, generate sentence embeddings (`all-MiniLM-L6-v2`), and persist in ChromaDB.
- `POST /api/rag/search`: Semantic similarity search against indexed document chunks.
- `GET /api/rag/status`: Inspect ChromaDB collection and embedding model status.

---

## Milestone 2 Endpoints (Multi-Agent Intelligence & Risk Advisor)

### 1. Scope & Deliverable Extraction Agent
- **Endpoint:** `POST /api/agents/analyze-scope`
- **Payload:** `{"query": "scope deliverables milestones", "top_k": 10}` or `{"text": "<direct text>"}`
- **Functionality:** Extracts project title, objectives, in-scope/out-of-scope boundaries, deliverables, milestones, deadlines, start/end dates, and team responsibilities. Never invents missing owners or dates.

### 2. Risk Detection & Delivery Forecasting Agent
- **Endpoint:** `POST /api/agents/detect-risks`
- **Payload:** `{"query": "risks delays blockers dependencies budget", "top_k": 10}` or `{"text": "<direct text>"}`
- **Functionality:** Detects schedule risks, dependency gaps, resource constraints, budget overruns, and technical bottlenecks. Classifies severity (`Critical`, `High`, `Medium`, `Low`) and forecasts milestone delivery concerns backed by textual evidence.

### 3. Blocker & Action Item Identification Agent
- **Endpoint:** `POST /api/agents/identify-blockers`
- **Payload:** `{"query": "blockers action items pending decisions", "top_k": 10}` or `{"text": "<direct text>"}`
- **Functionality:** Extracts active blockers, unresolved defects, pending decisions with assigned decision-makers, delayed activities, and action items with owners, deadlines, priorities, and statuses. Identifies unassigned action items.

### 4. Multi-Agent Project Intelligence Report
- **Endpoint:** `POST /api/agents/analyze-project`
- **Payload:** `{"top_k": 15}` or `{"text": "<direct project documentation>"}`
- **Functionality:** Coordinates all three agents, computes overall project health (`Healthy`, `Needs Attention`, `At Risk`, `Critical`), generates an executive summary, and synthesizes actionable recommendations.

### 5. Agents Status
- **Endpoint:** `GET /api/agents/status`
- **Functionality:** Checks the status and availability of all three agents and the underlying RAG vector database.

---

## Sample Data

Realistic sample enterprise documents are located in `backend/sample_data/`:
- `project_charter.pdf`: Formal enterprise PDF project charter with objectives, deliverables, milestones, and governance.
- `project_proposal.txt`: Project charter, objectives, deliverables, milestones, and timeline.
- `meeting_notes.txt`: Sprint 14 sync with blockers, decisions, issues, and action items.
- `progress_report.docx`: Executive progress report with delay warnings, budget overruns, and status tables.
- `task_list.csv`: Operational spreadsheet tracking tasks, owners, priorities, statuses, and dependencies.

---

## Run Automated Tests

From the project root:

```powershell
$env:PYTHONPATH='backend'; .\backend\.venv\Scripts\pytest backend/tests -v
```

The test suite contains 102 tests across 8 test suites (100% passing):
- `test_document_ingestion.py`: 22 tests (PDF, DOCX, CSV, TXT validation and security limits)
- `test_chunking.py`: 9 tests (boundary-aware chunking and offset tracking)
- `test_rag_integration.py`: 6 tests (embeddings, ChromaDB persistence, semantic retrieval)
- `test_scope_agent.py`: 17 tests (objectives, deliverables, milestones, missing-data handling)
- `test_risk_agent.py`: 9 tests (schedule risks, severity, budget, dependencies, forecasting)
- `test_blocker_agent.py`: 22 tests (blockers, decisions, action items, unassigned tasks, deduplication)
- `test_agent_orchestrator.py`: 6 tests (multi-agent coordination, health scoring, failure isolation, multi-doc RAG)
- `test_agent_api.py`: 11 tests (FastAPI route integration and sample data verification)
