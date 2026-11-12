# Step 2: System Architecture Design

## Purpose and scope

This document designs the system architecture, agent responsibilities, and RAG data flow for the AI Project Intelligence & Risk Advisor. It follows the official Milestone 1 brief and builds on [Step 1 learning notes](./STEP1_LEARNING_NOTES.md).

This is a design deliverable only. It does not implement services, agents, APIs, persistence, or a user interface. The architecture is intentionally technology-neutral: a vector database, embedding model, language model, and file storage provider can be selected during implementation.

## Architecture at a glance

The system has two related flows:

1. **Knowledge-base preparation:** uploads are validated and extracted; text is chunked, embedded, and indexed with project and source metadata.
2. **Project intelligence:** user questions and analysis requests retrieve relevant indexed evidence. The orchestrator routes evidence to specialized agents or the conversational assistant, validates their results, and makes grounded findings available to dashboards and reports.

See [system architecture diagram](./diagrams/system_architecture.mmd), [RAG pipeline diagram](./diagrams/rag_pipeline.mmd), and [multi-agent workflow diagram](./diagrams/multi_agent_workflow.mmd).

## Components and responsibilities

| Component | Responsibility |
|---|---|
| Document upload | Accept project proposals, SRS documents, meeting notes, progress updates, task-list CSVs, and plain text for a selected project. |
| Document ingestion | Validate inputs, associate them with a project, capture upload metadata, detect duplicates as a defined policy, and coordinate extraction. |
| Text extraction | Convert supported file formats to text while retaining useful structure and source locations. Scanned documents may require OCR in a later implementation. |
| Chunking | Divide extracted content into coherent, searchable passages while retaining source and project references. |
| Embedding generation | Convert chunks and later user queries into compatible semantic vectors. |
| Vector database | Store/search chunk vectors and associated text or text references, with metadata for project filtering and citations. |
| RAG retrieval | Search for relevant evidence, apply project/access filters, prepare context, and retain provenance. |
| Orchestrator | Coordinate retrieval and agent execution, route structured findings, handle failures explicitly, and reconcile outputs. |
| Specialized agents | Perform bounded scope, risk/forecasting, blocker/action, and documentation tasks based on evidence. |
| Project intelligence assistant | Answer natural-language questions with evidence and citations; communicate uncertainty or insufficient evidence. |
| Project data store | Persist project records and reviewed structured findings such as tasks, milestones, risks, blockers, and action items. It complements—not replaces—the source documents and vector index. |
| Dashboard and reports | Present project scope, progress, health indicators, risks, blockers, actions, and generated documentation with supporting evidence. |

## Data flow

### Upload and knowledge-base preparation

1. A user selects a project and uploads one or more files.
2. The ingestion component checks the file and associates it with project and document metadata.
3. The extractor reads PDF, DOCX, CSV, or plain text and returns text plus source locations where available.
4. The chunker produces coherent passages. Each passage retains its document ID, project ID, and source location.
5. The embedding component creates a vector for each passage.
6. The vector store indexes the vector alongside chunk text or a durable text reference and metadata.
7. The document and processing status are available to the project data layer. Errors are visible as failed or partial processing, not silently reported as success.

### Question and analysis

1. A user asks a project question or requests an analysis.
2. The assistant or orchestrator identifies the project and checks access.
3. The retrieval component embeds the query, searches the vector store with project/access filters, and selects relevant passages.
4. A context builder packages passages with source information and sends them to the assistant or appropriate agent.
5. The assistant generates a cited answer, or the orchestrator invokes one or more specialized agents.
6. The orchestrator checks result structure and provenance, and can persist proposed findings for review. Contradictions and missing evidence are surfaced.
7. The dashboard and reports display available findings and their supporting sources. Generated documentation remains a draft until reviewed or approved according to team policy.

## Agent roles and interactions

The orchestrator owns routing and coordination; agents do not independently change approved project records. Agent outputs should be structured, evidence-linked, and explicit about uncertainty. The proposed agent contracts below are described in detail in [Data Model Design](./DATA_MODEL_DESIGN.md).

| Agent | Responsibilities | Inputs | Outputs | RAG dependency and interactions |
|---|---|---|---|---|
| Scope and Deliverable Extraction Agent | Identify objectives, in-scope/out-of-scope items, requirements, deliverables, assumptions, and acceptance criteria. Distinguish approved commitments from suggestions. | Retrieved proposal/SRS/plan passages; optional current project records for comparison. | Structured scope and deliverable findings with source references, confidence/ambiguity notes, and questions for review. | Normally RAG-dependent for source-grounded extraction. Can compare its extracted findings with structured project records without another retrieval call if those records and provenance are supplied. Supplies baseline commitments to risk analysis and documentation. |
| Risk Detection and Delivery Forecasting Agent | Identify potential delivery risks, assess likelihood and impact where evidence supports it, identify schedule concerns, and suggest mitigations. | Retrieved commitments and status evidence; structured tasks, milestones, dependencies, blockers, and dates when available. | Risks and forecast observations with causes, possible impacts, assumptions, evidence, uncertainty, and mitigation suggestions. | Depends on RAG for document evidence and benefits from structured project data. It can calculate simple indicators from supplied structured records independently of a new retrieval call, but document-based claims still need provenance. Can consume blocker/action and scope findings from the orchestrator. |
| Blocker and Action Item Identification Agent | Extract current impediments, decisions needed, follow-ups, owners, dates, and statuses; distinguish current blockers from future risks. | Retrieved meeting-note/progress passages; optional existing task and action records for deduplication. | Blocker and action-item candidates with source references and unset fields where details are absent. | Normally RAG-dependent for extracting unstructured notes. Can inspect structured task/action records independently if they are supplied. Provides current delivery signals to risk analysis and dashboard reporting. |
| Documentation Generation Agent | Draft user stories, risk-register entries, and action-item summaries from grounded findings. | Validated scope, risk, blocker, and action findings plus their evidence; requested output format. | Draft documentation with links to evidence, clearly marked assumptions, and unresolved questions. | Uses RAG directly when it needs additional source evidence; otherwise it can work from validated, provenance-bearing agent outputs without a new retrieval. Depends on upstream findings and does not approve or publish commitments. |

### Coordination pattern

For a document-analysis run, the orchestrator can retrieve source passages and invoke scope extraction and blocker/action identification in parallel. It can then send those results and relevant project records to risk/forecast analysis. Documentation generation follows after the relevant findings are validated. Independent agents may run in parallel only when their inputs are ready; explicit dependencies prevent analysis from treating missing upstream data as facts.

For a conversational query, the assistant can retrieve evidence and answer directly when no specialized analysis is needed. If the question asks for a risk assessment or action-item extraction, the orchestrator invokes the corresponding agent and returns its evidence-linked result. A failed agent or invalid response should be reported as incomplete; it must not be represented as a successful analysis.

## RAG pipeline design

The RAG flow has an indexing path and a query path. The indexing path prepares project knowledge; the query path finds relevant evidence and uses it to answer.

| Stage | Input | Processing and output |
|---|---|---|
| Document ingestion | Uploaded file and selected project | Validate the upload; assign document/project IDs; capture upload metadata and processing status. |
| Text extraction | Document reference and file type | Extract text and structure from PDF, DOCX, CSV, or plain text. Return text segments and source locations such as page, section, or row where available. |
| Chunking | Extracted segments and source locations | Split into semantically coherent chunks. Return chunk text, ordinal, source location, and parent document/project IDs. |
| Embeddings | Chunk text and embedding-model configuration | Encode each chunk into a vector. Preserve model identifier and dimensionality so vectors are interpreted consistently. |
| Vector storage | Vector, chunk text/reference, and metadata | Index the vector with chunk/document/project IDs and searchable metadata. Enforce project and access boundaries at retrieval time. |
| Similarity search | User question, query vector, filters, and retrieval settings | Search for nearest candidate vectors, optionally using keyword and metadata filters. Return ranked candidates and similarity scores; a score is not a truth guarantee. |
| Context retrieval | Ranked candidates and query | Select, deduplicate, and package relevant text with citations and source metadata. Detect insufficient or conflicting evidence where possible. |
| LLM response generation | User question, instructions, and evidence context | Generate a grounded answer or analysis. Cite sources, state uncertainty, and avoid inventing absent owners, dates, or commitments. |

The stages exchange IDs and provenance as well as text. This enables an answer to cite a document and location, lets teams identify stale evidence, and supports corrections or re-indexing when a source changes. The implementation should select chunk sizes, embedding model, similarity measure, and retrieval count through evaluation on representative project questions rather than assuming universal values.

## Cross-cutting design principles

- **Traceability:** retain document, chunk, and source-location references in retrieval and agent results.
- **Project isolation:** constrain every query and stored finding to the authorized project and user.
- **Evidence versus inference:** label directly extracted facts separately from risk assessments and forecasts.
- **Freshness and conflicts:** retain document dates/status; surface conflicting or superseded information for review.
- **Visible processing state:** communicate extraction and indexing failures and partial results.
- **Human review:** treat generated user stories, risk entries, scope changes, and forecasts as candidates for review, not approved decisions.
- **Technology neutrality:** choose concrete infrastructure only after implementation constraints and evaluation needs are known.

## Step 3 boundary

This step defines the design only. Step 3 should implement the document ingestion module for PDF, DOCX, CSV, and plain text, including extraction and clear processing status. The RAG chunking, embedding, and vector-indexing implementation should follow the milestone's sequence and use these source IDs and metadata contracts. The agents, dashboard, and assistant are not implemented here.
