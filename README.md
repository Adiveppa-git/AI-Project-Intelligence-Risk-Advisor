# AI-Driven Enterprise Project Intelligence & Risk Management Platform

An AI-powered full-stack platform that transforms enterprise project documents into actionable project intelligence. It combines a **FastAPI backend, Retrieval-Augmented Generation (RAG), local semantic embeddings, persistent ChromaDB storage, specialized AI agents, and a React dashboard** to help project teams understand scope, monitor delivery risks, identify blockers, and track project health.

The platform supports PDF, DOCX, CSV, and TXT documents. Its multi-agent architecture extracts project scope, deliverables, milestones, risks, blockers, action items, and pending decisions, while preserving source evidence for traceability.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [System Architecture](#3-system-architecture)
4. [AI Agents and Capabilities](#4-ai-agents-and-capabilities)
5. [Technology Stack](#5-technology-stack)
6. [Repository Structure](#6-repository-structure)
7. [Environment Setup](#7-environment-setup)
8. [Running the Application](#8-running-the-application)
9. [API Reference](#9-api-reference)
10. [Document Ingestion and RAG Workflow](#10-document-ingestion-and-rag-workflow)
11. [Dashboard Modules](#11-dashboard-modules)
12. [Evidence, Deduplication, and Data Reliability](#12-evidence-deduplication-and-data-reliability)
13. [Testing and Validation](#13-testing-and-validation)
14. [Current Limitations](#14-current-limitations)
15. [Future Enhancements](#15-future-enhancements)

---

## 1. Project Overview

Enterprise projects generate information across project proposals, project charters, requirement documents, meeting notes, progress reports, and task spreadsheets.

Manually reviewing these documents makes it difficult for project managers and stakeholders to identify:

- Whether project deliverables and milestones are clearly defined.
- Which activities are delayed or at risk.
- What dependencies and resource constraints may affect delivery.
- Which blockers require immediate attention.
- Which action items have assigned owners and deadlines.
- Whether multiple documents describe the same risk or issue.

This platform addresses these challenges by combining document intelligence, semantic retrieval, and specialized AI agents.

### Project Objectives

- Ingest and process structured and unstructured project documents.
- Convert document content into searchable semantic representations.
- Extract project scope, deliverables, milestones, and responsibilities.
- Detect project risks and delivery concerns.
- Identify blockers, action items, and pending decisions.
- Consolidate findings from multiple agents into a unified project report.
- Display project intelligence through an interactive dashboard.
- Preserve supporting evidence to make extracted findings traceable to their source documents.

---

## 2. Key Features

### Multi-Format Document Ingestion

Supports:
- PDF documents
- Microsoft Word documents (`.docx`)
- CSV spreadsheets
- Plain text documents (`.txt`)

### Retrieval-Augmented Generation (RAG)

- Text extraction and boundary-aware chunking.
- Semantic embeddings using Sentence Transformers.
- 384-dimensional embeddings with `all-MiniLM-L6-v2`.
- Persistent vector indexing using ChromaDB.
- Semantic similarity search across indexed documents.

### Specialized Multi-Agent Intelligence

- Scope and deliverable extraction.
- Risk detection and delivery forecasting.
- Blocker and action item identification.
- Multi-agent orchestration and report consolidation.

### Evidence-Based Findings

- Source filename and document identification.
- Supporting evidence snippets.
- Evidence provenance across multiple documents.
- Duplicate finding consolidation.
- Traceable risk and blocker relationships.

### Project Intelligence Dashboard

- Executive project overview.
- Project health and key statistics.
- Risk findings and severity classification.
- Blocker and action item tracking.
- Milestone and deliverable visibility.
- Multi-agent analysis results.
- Document upload and RAG pipeline views.

---

## 3. System Architecture

The platform follows a modular full-stack architecture.

```text
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend                            │
│                                                              │
│ Overview Dashboard | Scope | Risks | Blockers | Milestones   │
│ Document Upload | RAG Pipeline | Multi-Agent | Architecture  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                           │
│                                                              │
│ Health | Document Ingestion | RAG | Agent Endpoints          │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 Multi-Agent Orchestrator                      │
│                                                              │
│ Agent Coordination | Failure Isolation | Report Synthesis    │
│ Project Health | Executive Summary | Recommendations         │
└──────────────┬────────────────┬────────────────┬──────────────┘
               │                │                │
               ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
       │ Scope Agent │  │ Risk Agent  │  │ Blocker Agent│
       │             │  │             │  │              │
       │ Goals       │  │ Risk Types  │  │ Blockers     │
       │ Scope       │  │ Severity    │  │ Action Items │
       │ Deliverables│  │ Dependencies│  │ Decisions    │
       │ Milestones  │  │ Forecasting │  │ Ownership    │
       └──────┬──────┘  └──────┬──────┘  └──────┬───────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                       RAG Pipeline                            │
│                                                              │
│ Document Parsing → Text Chunking → Embedding Generation      │
│                                                              │
│                 Persistent ChromaDB Storage                   │
└──────────────────────────────────────────────────────────────┘
```

### Architecture Layers

1. **Frontend Layer:** React-based user interface for document uploads, analysis results, and project monitoring.
2. **API Layer:** FastAPI endpoints for document ingestion, semantic search, and agent execution.
3. **Intelligence Layer:** Specialized agents coordinated through the multi-agent orchestrator.
4. **RAG Layer:** Document parsing, chunking, semantic embedding generation, retrieval, and vector persistence.

---

## 4. AI Agents and Capabilities

### 4.1 Scope and Deliverable Extraction Agent (`ScopeAgent`)

Extracts project definition and planning information, including:

- Project title and objectives.
- Project goals.
- In-scope and out-of-scope items.
- Deliverables and target dates.
- Milestones and timelines.
- Team responsibilities and ownership.

The agent uses document evidence to identify available information rather than inventing missing owners or dates.

### 4.2 Risk Detection and Delivery Forecasting Agent (`RiskAgent`)

Identifies project risks and delivery concerns, including:

- Schedule delays.
- Dependency gaps.
- Resource constraints.
- Budget concerns.
- Delivery bottlenecks.
- Milestone-related risks.

Risk findings are classified by severity:

- Critical
- High
- Medium
- Low

The agent also uses supporting evidence to explain why a finding was identified.

### 4.3 Blocker and Action Item Identification Agent (`BlockerAgent`)

Identifies operational issues and pending work, including:

- Active blockers.
- Unresolved issues.
- Pending decisions.
- Delayed activities.
- Action items.
- Assigned owners.
- Deadlines, priorities, and statuses.

The extraction process handles structured task information and filters completed tasks and irrelevant report headings.

### 4.4 Multi-Agent Orchestrator (`AgentOrchestratorService`)

Coordinates the three specialized agents and consolidates their outputs.

Responsibilities include:

- Coordinating analysis across indexed project documents.
- Isolating individual agent failures.
- Combining scope, risk, and blocker findings.
- Consolidating duplicate findings.
- Linking related risks and blockers.
- Generating an executive summary.
- Producing project health information and recommendations.

---

## 5. Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, JavaScript, Vite 8 |
| Styling | Tailwind CSS 4, CSS |
| UI Icons | Lucide React |
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Data Validation | Pydantic |
| PDF Processing | PyMuPDF |
| Word Processing | python-docx |
| CSV Processing | Python CSV module |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Testing | Pytest, HTTPX, frontend test suite |
| Version Control | Git and GitHub |

---

## 6. Repository Structure

```text
AI-Project-Intelligence-Risk-Advisor/
│
├── .gitignore
├── .env.example
├── README.md
│
├── backend/
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   │
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── agents/
│   │   │   ├── agent_utils.py
│   │   │   ├── blocker_agent.py
│   │   │   ├── risk_agent.py
│   │   │   └── scope_agent.py
│   │   │
│   │   ├── api/
│   │   │   ├── agent_routes.py
│   │   │   ├── rag_routes.py
│   │   │   └── routes.py
│   │   │
│   │   ├── models/
│   │   │   ├── agent_models.py
│   │   │   ├── document.py
│   │   │   └── rag.py
│   │   │
│   │   └── services/
│   │       ├── agent_orchestrator.py
│   │       ├── chunking.py
│   │       ├── document_ingestion.py
│   │       ├── embeddings.py
│   │       ├── rag_pipeline.py
│   │       └── vector_store.py
│   │
│   ├── data/
│   │   └── chroma/
│   │
│   ├── sample_data/
│   │
│   └── tests/
│       ├── test_agent_api.py
│       ├── test_agent_orchestrator.py
│       ├── test_blocker_agent.py
│       ├── test_chunking.py
│       ├── test_document_ingestion.py
│       ├── test_rag_integration.py
│       ├── test_risk_agent.py
│       └── test_scope_agent.py
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── vite.config.js
│   │
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   │
│   ├── src/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── main.jsx
│   │   │
│   │   ├── assets/
│   │   │
│   │   ├── components/
│   │   │   ├── Badge.jsx
│   │   │   ├── EvidenceModal.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── StatCard.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── ArchitectureOverview.jsx
│   │   │   ├── BlockerAgentPage.jsx
│   │   │   ├── DocumentUpload.jsx
│   │   │   ├── MilestoneTracker.jsx
│   │   │   ├── MultiAgentPage.jsx
│   │   │   ├── OverviewDashboard.jsx
│   │   │   ├── RAGPipeline.jsx
│   │   │   ├── RiskAgentPage.jsx
│   │   │   └── ScopeAgentPage.jsx
│   │   │
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── sampleData.js
│   │   │
│   │   └── utils/
│   │       ├── evidenceProvenance.js
│   │       └── safeRender.js
│   │
│   └── test/
│       └── blocker_render.test.js
│
└── docs/
    └── Project design, milestone, and validation documentation
```

The ChromaDB directory contains locally generated vector data and is not required to be committed to GitHub.

---

## 7. Environment Setup

### Prerequisites

- Python 3.10 or later.
- Node.js and npm.
- Git.
- Internet access for installing dependencies and downloading the embedding model when required.

### Step 1: Clone the Repository

```powershell
git clone https://github.com/Adiveppa-git/AI-Project-Intelligence-Risk-Advisor.git

cd AI-Project-Intelligence-Risk-Advisor
```

### Step 2: Create the Python Virtual Environment

```powershell
python -m venv backend\.venv
```

Activate it:

```powershell
backend\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

### Step 3: Install Backend Dependencies

```powershell
python -m pip install --upgrade pip

python -m pip install -r backend\requirements.txt
```

### Step 4: Install Frontend Dependencies

Open a terminal in the project root:

```powershell
cd frontend

npm install
```

Return to the project root when finished:

```powershell
cd ..
```

### Step 5: Environment Configuration

Environment templates are available in the repository.

Copy the root template if you need a root-level environment file:

```powershell
Copy-Item .env.example .env
```

Keep real credentials and local environment files private. Do not commit `.env` files.

---

## 8. Running the Application

The backend and frontend run in separate terminals.

### 8.1 Start the Backend

From the project root, activate the backend virtual environment if it is not already active.

```powershell
$env:PYTHONPATH='backend'

python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

| Service | URL |
|---|---|
| API base | http://127.0.0.1:8000 |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| Health check | http://127.0.0.1:8000/health |

### 8.2 Start the Frontend

Open a second terminal:

```powershell
cd frontend

npm run dev
```

Vite displays the local frontend URL in the terminal, normally:

```text
http://localhost:5173
```

Open that address in your browser.

### 8.3 Production Build

From the `frontend` directory:

```powershell
npm run build
```

This generates the production build in the frontend distribution directory.

---

## 9. API Reference

The backend exposes endpoints for health checks, document ingestion, semantic retrieval, and agent execution.

### 9.1 Health and Status

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Checks backend availability |
| GET | `/api/rag/status` | Reports RAG and vector-store status |
| GET | `/api/agents/status` | Reports agent readiness |

### 9.2 Document and RAG Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/documents/upload` | Uploads and parses a document |
| POST | `/api/rag/index` | Processes and indexes document content |
| POST | `/api/rag/search` | Performs semantic document retrieval |

Example semantic search request:

```json
{
  "query": "What are the active schedule delay risks and blockers?",
  "top_k": 5
}
```

### 9.3 Multi-Agent Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/agents/analyze-scope` | Extracts project scope and deliverables |
| POST | `/api/agents/detect-risks` | Identifies project risks |
| POST | `/api/agents/identify-blockers` | Identifies blockers and action items |
| POST | `/api/agents/analyze-project` | Runs consolidated multi-agent analysis |

Example consolidated analysis request:

```json
{
  "query": "Analyze the enterprise project status, risks, and blockers.",
  "top_k": 15
}
```

For the exact request schemas and response models, use the interactive Swagger documentation at:

http://127.0.0.1:8000/docs

---

## 10. Document Ingestion and RAG Workflow

The document intelligence pipeline follows these stages:

1. **Document Upload:** The user uploads a PDF, DOCX, CSV, or TXT file.
2. **Validation:** The ingestion service checks file type, content, and applicable upload limits.
3. **Text Extraction:** Text is extracted using format-specific parsing logic.
4. **Chunking:** Extracted content is divided into manageable text segments while preserving useful boundaries and overlap.
5. **Embedding Generation:** Sentence Transformers converts each chunk into a 384-dimensional semantic vector.
6. **Vector Indexing:** ChromaDB stores embeddings and associated document metadata.
7. **Semantic Retrieval:** User queries are converted into embeddings and matched against indexed document content.
8. **Agent Analysis:** Relevant document content is supplied to specialized agents.
9. **Report Consolidation:** The orchestrator combines the agent outputs into a unified project intelligence report.
10. **Dashboard Visualization:** The frontend presents findings, evidence, risks, blockers, milestones, and project health.

### Embedding Model

`sentence-transformers/all-MiniLM-L6-v2`

### Vector Store

ChromaDB with persistent local storage.

### Chunking Configuration

The documented default configuration is:

- Chunk size: 1,000 characters.
- Chunk overlap: 150 characters.

Actual runtime values depend on the active configuration.

---

## 11. Dashboard Modules

The React frontend provides dedicated pages for project monitoring and AI analysis.

| Module | Purpose |
|---|---|
| Overview Dashboard | Displays consolidated project intelligence and key statistics |
| Architecture Overview | Presents the system architecture and its components |
| Document Upload | Provides document upload and ingestion functionality |
| RAG Pipeline | Presents document indexing and retrieval information |
| Scope Agent | Displays extracted scope, goals, deliverables, and milestones |
| Risk Agent | Displays identified risks and severity information |
| Blocker Agent | Displays blockers, action items, and pending decisions |
| Milestone Tracker | Displays milestone and delivery information |
| Multi-Agent Analysis | Presents consolidated results from the specialized agents |

Reusable frontend components include the application header, sidebar, status badges, statistic cards, and evidence modal.

---

## 12. Evidence, Deduplication, and Data Reliability

### 12.1 Evidence Provenance

The platform maintains source information for extracted findings.

Evidence can include:

- Source filename.
- Document identifier.
- Supporting text snippet.

This allows users to understand which document content supports a reported risk, blocker, or other finding.

### 12.2 Finding Deduplication

The multi-agent processing pipeline normalizes finding content to identify repeated issues across documents.

For example, a delivery blocker appearing in both a meeting report and a task spreadsheet can be consolidated into a canonical finding rather than displayed as unrelated duplicates.

Distinct supporting evidence can be retained when findings are merged.

### 12.3 Cross-Agent Relationships

The consolidated analysis can associate related risks and blockers.

This helps stakeholders understand how an operational blocker may contribute to a broader project delivery risk.

### 12.4 Safe Frontend Rendering

Frontend rendering utilities and evidence components handle structured analysis results safely, including findings that contain nested data.

### 12.5 Project Health

The orchestrator generates project health information using consolidated project findings. Health status should be interpreted alongside the underlying risks, blockers, and milestone information rather than as a standalone guarantee of delivery performance.

---

## 13. Testing and Validation

The project includes backend and frontend regression tests.

### Backend Tests

From the project root:

```powershell
$env:PYTHONPATH='backend'

python -m pytest backend/tests -v
```

The backend test suite covers:

- Document ingestion and parser validation.
- Chunking and overlap behavior.
- RAG integration and vector-store behavior.
- Scope extraction.
- Risk detection.
- Blocker and action item extraction.
- Deduplication and evidence provenance.
- Multi-agent orchestration.
- API behavior and failure handling.

### Frontend Tests

The frontend includes regression coverage for safe blocker rendering.

From the frontend directory, inspect available test scripts:

```powershell
npm run
```

Run the test script configured in `package.json`.

### Production Build

```powershell
cd frontend

npm run build
```

### Latest Recorded Validation

The latest development verification reported:

- Backend: 118 tests passed.
- Frontend: 12 tests passed.
- Frontend production build: successful.
- Lint: zero errors, with 56 style warnings reported.

These are the latest recorded development results; rerun the commands above to verify the current local checkout.

---

## 14. Current Limitations

1. **Scanned PDF OCR:** Image-based scanned PDFs may require an OCR preprocessing stage to extract text reliably.
2. **Multi-Tenant Isolation:** The current local vector-store design uses a project collection and does not constitute a complete multi-tenant access-control architecture.
3. **Health Score Interpretation:** Project health is an analytical indicator based on available findings and should be reviewed with supporting evidence.
4. **Document Quality:** Missing, outdated, or inconsistent source documents can affect extraction and analysis quality.
5. **AI Extraction:** Extracted findings should be reviewed by project stakeholders before being used for critical project decisions.

---

## 15. Future Enhancements

Potential future improvements include:

- OCR support for scanned PDF documents.
- Multi-project and multi-tenant data isolation.
- Role-based authentication and authorization.
- Conversational project assistant for natural-language questions.
- Automated project documentation and report generation.
- Advanced project health and delivery forecasting.
- Interactive risk heatmaps and dependency visualizations.
- Notifications for critical blockers and overdue actions.
- Cloud deployment and scalable vector storage.
- Audit history and project analysis versioning.

---

## License

This project is developed as part of the **Infosys Springboard Internship Program**.

All rights reserved.
