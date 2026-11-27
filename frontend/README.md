# AI Project Intelligence & Risk Advisor — Frontend Dashboard

Modern, responsive enterprise dashboard built for **Infosys Springboard Milestone 1 & Milestone 2**.

## Tech Stack
- **Framework:** React 19 + Vite 8
- **Styling:** Tailwind CSS v4 (with `@tailwindcss/vite`)
- **Icons:** Lucide React
- **API Client:** Fetch API with CORS & Proxy support for FastAPI (`http://127.0.0.1:8000`)

---

## 9 Dashboard Views

1. **Executive Overview Dashboard (`/overview`):**
   - High-level system health indicator (connected to live `/health` endpoint).
   - Knowledge base stats (live indexed chunk count in ChromaDB).
   - Specialized agent capability cards with direct navigation.
   - Quick-launch presets to run live analysis on realistic sample datasets.

2. **Multi-Format Document Ingestion (`/upload`):**
   - Upload dropzone accepting `.pdf`, `.docx`, `.csv`, `.txt`.
   - Real-time parsed metadata: `document_id`, `file_type`, `character_count`, `word_count`, `line_count`.
   - Formatted text preview viewer with 1-click clipboard copy.
   - Direct-to-RAG indexing action and Multi-Agent analysis dispatch.

3. **RAG Vector Retrieval Pipeline (`/rag`):**
   - ChromaDB vector collection metrics: collection name, embedding model (`all-MiniLM-L6-v2`), 384-dimensional dense vectors, and total chunks.
   - Interactive semantic search interface with Top-K slider (1-10) and quick query suggestions.
   - Ranked semantic results with cosine similarity score bars and verbatim chunk evidence inspection modal.

4. **Scope & Deliverables Extraction Agent (`/scope`):**
   - Project title and core objectives extraction.
   - In-scope vs. Out-of-scope comparative layout.
   - Authoritative expected deliverables table preserving source deliverable names and assigned owners.
   - Milestones and team responsibilities breakdown.

5. **Risk Detection & Delivery Forecasting Agent (`/risks`):**
   - Overall project risk badge (Low, Medium, High, Critical).
   - Categorized risk findings across 5 core classifiers: **Schedule, Budget, Dependency, Resource, Delivery**.
   - Delivery concerns summary and potential resource bottleneck detection.
   - Delivery forecast dates and confidence ratings.

6. **Blocker & Action Item Identification Agent (`/blockers`):**
   - Active critical blockers with impact statements and verbatim evidence.
   - Pending executive decisions with designated decision-makers and deadlines.
   - Delayed activities and unresolved questions.
   - Action items matrix with priority badges and unassigned item alerts.

7. **Autonomous Multi-Agent Orchestrator (`/orchestrator`):**
   - Concurrent parallel execution of Scope, Risk, and Blocker agents via ThreadPoolExecutor.
   - Standardized 0-100 project health score gauge with rating badge.
   - Executive summary and strategic recommendations synthesis.
   - Partial failure resilience handling and tabbed deep-dive inspection.
   - 1-click executive report export to clipboard.

8. **Milestone Tracker & Audit (`/milestones`):**
   - Compliance dashboard tracking the exact 8 activities from the official internship specification.
   - 100% completion verification with 102 passing pytest tests.
   - Deliverables and code references for each activity.

9. **Technical Architecture Overview (`/architecture`):**
   - Detailed architectural blueprints for end-to-end data flow, RAG pipeline, multi-agent coordination, and Pydantic schema mappings.

---

## Quick Start Guide

### 1. Start the FastAPI Backend
From the repository root:
```powershell
$env:PYTHONPATH='backend'
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend Swagger API documentation will be available at `http://127.0.0.1:8000/docs`.

### 2. Start the React Frontend
In a separate terminal, navigate to the `frontend` directory:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at: **`http://localhost:5173`**

### 3. Build for Production
```powershell
cd frontend
npm run build
```
Production assets are generated in `frontend/dist/`.
