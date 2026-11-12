# Step 1 Learning Notes: AI Project Intelligence & Risk Advisor

## Purpose and project context

This project helps software teams turn scattered project documents—such as proposals, requirements, meeting notes, progress updates, and task lists—into a shared, searchable source of project intelligence. It uses Retrieval-Augmented Generation (RAG) to ground answers in those documents and a multi-agent workflow to extract project information, identify risks and blockers, forecast delivery concerns, and generate useful project documentation.

These notes address Milestone 1's learning objective: **study RAG architecture, multi-agent design patterns, and project management fundamentals**. They also connect those ideas to the project’s proposed modules and next implementation steps.

## 1. Retrieval-Augmented Generation (RAG)

### The basic idea

A language model can write fluent answers, but it may not know the latest or private facts about a particular project. RAG gives it relevant information from a project's own documents at answer time.

RAG has two main phases:

1. **Prepare the knowledge base:** read project documents, split their text into useful passages, turn those passages into numerical vectors called embeddings, and store the vectors with the text and its source information.
2. **Answer a question:** find passages that are relevant to the question, add them to the model's prompt as context, and ask the model to answer using that context.

For example, if a team asks, “Why is the mobile release at risk?”, the system can retrieve a meeting note about a delayed mobile test environment and a proposal that sets the release date. The model can then explain the risk using those sources rather than guessing from general knowledge.

RAG is not model training. The documents are retrieved and supplied to the model for a particular request; they are not automatically incorporated into the model's permanent knowledge.

### The complete RAG workflow

#### 1. Document ingestion

Ingestion is the process of bringing project artifacts into the system. The proposed project accepts PDF, DOCX, CSV, and plain-text inputs, including proposals, SRS documents, meeting notes, progress updates, and task lists.

For each upload, the system should record useful metadata, such as project ID, filename, document type, upload time, and—where available—author, meeting date, or page number. It should validate file type and size, handle duplicate uploads deliberately, and report files it cannot process. Access controls matter: project documents may contain sensitive business information.

#### 2. Text extraction

An appropriate parser extracts readable text from each file type. PDF and DOCX files contain paragraphs and sometimes tables; CSV files contain rows and columns; plain-text files already contain text.

Extraction can lose structure. For example, a table row may have meaning only when its column headings are retained. The system should preserve useful structure and source references—such as page, section, row, or meeting date—so retrieved information can later be explained and checked.

Scanned PDFs may contain images rather than selectable text. They need OCR before their contents can be searched. Extraction quality should be checked because incorrect or missing text leads to poor retrieval and unreliable answers.

#### 3. Document chunking

Documents are split into smaller passages called **chunks**. Sending an entire large document for every question is inefficient and may exceed the model's context limit. Chunks let retrieval select only the relevant portions.

Chunk boundaries should preserve meaning. A section heading should stay associated with its paragraphs; a meeting action item should not be separated from its owner or due date. Chunking can use a target size with a small overlap between neighboring chunks so a fact near a boundary is not cut off from its explanation.

There is no universally correct chunk size. Very small chunks may lose context; very large chunks may include too much unrelated material. The right choice should be tested against realistic project questions. Each chunk should retain a link to its source document and relevant metadata.

#### 4. Embedding generation

An **embedding model** converts text into a list of numbers (a vector) that represents aspects of its meaning. Similar ideas tend to have vectors that are close under a chosen distance or similarity measure.

The system generates embeddings for stored chunks. At query time, it also embeds the user's question using a compatible embedding model. The same model and vector settings should be used consistently for a given index; changing them may require re-embedding the stored content.

Embeddings support semantic matching, so a question such as “What could delay launch?” can match a note saying “the test environment is not ready,” even though the wording differs.

#### 5. Vector database storage

A vector store keeps chunk embeddings and supports efficient similarity search. Each record should also include the chunk text or a retrievable reference to it, plus metadata such as project ID, document ID, filename, and page or section.

Metadata is important for more than citations. It enables the system to restrict retrieval to the right project, filter by document type or date, and trace every answer back to its source. Storage and access rules should prevent one project's content from appearing in another project's results.

#### 6. Similarity search

When a question arrives, its embedding is compared with stored vectors. The search returns the nearest candidates according to a configured similarity measure. A top-*k* setting limits how many candidates are considered.

Similarity is a relevance signal, not proof that a passage is correct. Search results can be incomplete, outdated, or close in wording but irrelevant. Practical systems can improve results with project and date filters, keyword-plus-vector (hybrid) search, or a reranking step that reorders candidate passages.

#### 7. Retrieval

Retrieval selects and prepares useful search results for the answer. It can remove duplicates, prioritize recent or authoritative sources, and include neighboring chunks when additional context is needed.

The system should preserve source identifiers and relevant metadata through this stage. If retrieval finds no sufficiently relevant evidence, the assistant should say that the uploaded documents do not provide enough information rather than inventing an answer.

#### 8. Context generation and answer generation

The application assembles a prompt containing the user's question, instructions for using only the supplied evidence, and the selected passages with source details. This is often called **context building** or **prompt construction**; it is distinct from generating the final natural-language answer.

The language model uses that context to produce an answer. The application can ask it to cite the supporting documents and distinguish facts from estimates or recommendations. The result should be checked for unsupported claims and presented with source references where possible. If evidence conflicts—for example, two documents give different dates—the system should surface the conflict and its sources instead of silently choosing one.

### Practical RAG quality and safety checks

- **Grounding:** Can each factual claim be traced to a retrieved source?
- **Retrieval quality:** Did the search find the passages a project member would expect?
- **Freshness:** Are superseded plans or old meeting notes being mistaken for current status?
- **Completeness:** Were tables, dates, owners, and action items extracted accurately?
- **Privacy:** Is retrieval restricted to documents the requesting user may access?
- **Uncertainty:** Does the assistant acknowledge missing, ambiguous, or conflicting evidence?

## 2. Multi-agent AI architecture

A multi-agent system uses multiple specialized AI roles to complete a task that is too broad for one undirected prompt. An agent is not necessarily a separate model: it may be a configured model call with a defined responsibility, instructions, permitted tools, and structured input and output.

For this project, an orchestrator can coordinate the work:

1. Receive a question or a request to analyze newly uploaded documents.
2. Retrieve relevant project evidence through RAG.
3. Send suitable evidence to one or more specialized agents.
4. Validate and combine their structured findings.
5. Return results with source references and uncertainty.

Agents can run in sequence when later work depends on earlier findings. Independent analyses—such as extracting scope and identifying blockers—may run in parallel, provided their results are reconciled. A shared, structured project record can store the outputs. It should distinguish extracted facts from inferred assessments and retain provenance for each item.

An orchestrator should handle errors explicitly: if an agent fails or returns invalid data, the system should report an incomplete analysis rather than presenting a success-shaped result. Human review is appropriate for consequential decisions, such as changing an approved scope, declaring a delivery date, or accepting a high-impact risk.

### Proposed agent responsibilities

#### Scope and Deliverable Extraction Agent

- Reads relevant proposals, SRS documents, and approved project plans.
- Extracts project goals, in-scope and out-of-scope work, requirements, deliverables, assumptions, and acceptance criteria.
- Produces structured items with source citations and marks ambiguous or missing details for review.
- Helps compare later updates against the agreed scope; it should not treat every suggestion in a meeting note as approved scope.

#### Risk Detection and Delivery Forecasting Agent

- Examines project commitments alongside evidence such as task status, dependencies, missed dates, and unresolved issues.
- Identifies risk statements with cause, possible event, impact, likelihood, and evidence.
- Estimates delivery concerns from available information and states assumptions and uncertainty. A forecast is an estimate, not a guarantee.
- Can suggest mitigations and flag when there is too little or contradictory evidence to make a useful forecast.

#### Blocker and Action Item Identification Agent

- Finds impediments, decisions needed, follow-ups, and action items in meeting notes and progress updates.
- Extracts an action's description, owner (if stated), due date (if stated), status, and source.
- Distinguishes a confirmed blocker from a possible concern, and leaves missing owners or dates unset rather than inventing them.
- Can identify overdue or unowned actions when it has reliable dates and status information.

#### Documentation Generation Agent

- Drafts missing project artifacts from retrieved and structured evidence, including user stories, a risk register, and action-item lists.
- Uses a consistent format and traces generated statements to the documents that support them.
- Labels assumptions and unresolved questions, and avoids presenting drafts as approved decisions.
- Produces material for team review; it does not independently approve or publish project commitments.

## 3. Project management fundamentals

#### Project scope

Scope defines what the project will and will not deliver, including its boundaries, goals, and constraints. A clear scope helps teams recognize scope changes and avoid treating every new idea as an agreed requirement.

#### Deliverables

Deliverables are the tangible outputs or outcomes the project promises, such as a tested release, an API, a user guide, or a risk register. They should have clear acceptance criteria so the team can determine whether they are complete.

#### Tasks and milestones

Tasks are pieces of work assigned to people or teams, ideally with an owner, status, and target date. Tasks may depend on other tasks. A milestone is a significant checkpoint or event—such as requirements approval or release readiness—not simply another name for a task.

#### Risks and blockers

A **risk** is an uncertain future event that could affect objectives. It is often assessed by likelihood and impact and managed with a mitigation or contingency plan. For example, a vendor API change may threaten integration work.

A **blocker** is a current impediment preventing or materially delaying work, such as an unavailable test environment. A blocker may create a risk to a future milestone. These terms should not be conflated: the blocker exists now, while a risk describes a possible effect or event.

#### Project progress

Progress describes what has been completed and what remains, relative to the plan and acceptance criteria. Useful evidence includes task status, completed deliverables, dependency status, and milestone dates. A percentage alone can be misleading if work is not consistently sized or if completion has not been verified.

#### Project health

Project health is a summary of how well the project is positioned to meet its objectives. Teams commonly consider schedule, scope, quality, resources, dependencies, and risks. A dashboard may use Green/Amber/Red indicators, but the criteria should be explicit and backed by evidence; a color is not itself an explanation.

For this advisor, health indicators should be explainable—for example: “Amber: two actions due before the release milestone have no owner; the latest meeting note says mobile test access is still pending.” The system should separate measured facts from AI-generated interpretation and allow a person to review important conclusions.

## 4. How RAG and multi-agent architecture work together

RAG supplies the agents and conversational assistant with project-specific evidence. Agents organize and interpret that evidence for different project-management tasks.

For instance, the RAG layer can retrieve a proposal's release commitment and a recent meeting note about a delayed dependency. The forecasting agent can assess whether that dependency threatens the commitment, while the blocker agent can extract the immediate action needed. The documentation agent can draft a risk-register entry using those findings. The assistant can then explain the project status with citations to the proposal and meeting note.

The distinction is useful:

- **RAG answers “what do the project documents say?”** by finding and providing source passages.
- **Agents answer “what structured project insight can we derive from that evidence?”** within defined roles.
- **The orchestrator answers “which analyses should run, and how should their results be combined?”**

Neither retrieval nor multiple agents guarantees correctness. Source quality, retrieval relevance, clear responsibilities, validation, uncertainty handling, and human oversight remain necessary.

## 5. Practical enterprise project example

Consider a proposal for an internal employee-onboarding portal:

- The first release is due on **30 September**.
- The agreed deliverables are employee profile setup, an onboarding checklist, and an HR dashboard.
- Integration with the identity provider must be completed before user acceptance testing.

A later meeting note says:

- The identity-provider test environment is still unavailable.
- Priya will contact the platform team by **12 September**.
- The team discussed adding automated email reminders, but no scope decision was made.
- User acceptance testing is planned to start on **15 September**.

### What the system does

1. **Ingests and extracts:** It reads the proposal and meeting note, preserving their dates, headings, and source locations.
2. **Chunks and indexes:** It creates searchable passages, including the release commitment and the meeting's dependency and action item. It attaches each passage to its source document.
3. **Retrieves evidence:** For “What could delay user acceptance testing?”, it finds the test-environment issue and the proposal's dependency requirement.
4. **Extracts scope:** The Scope and Deliverable Extraction Agent reports the three approved deliverables. It marks automated reminders as a discussed idea, not an approved deliverable.
5. **Identifies a blocker and action:** The Blocker and Action Item Identification Agent records the unavailable test environment as a current blocker and Priya's follow-up as an action due 12 September.
6. **Assesses delivery risk:** The Risk Detection and Delivery Forecasting Agent flags a risk to the 15 September testing start because a required dependency is not ready. It can note that the available evidence does not establish whether the 30 September release will actually slip.
7. **Drafts documentation:** The Documentation Generation Agent can prepare a risk-register entry: “If the identity-provider test environment remains unavailable, user acceptance testing may start late. Mitigation: Priya to follow up with the platform team by 12 September.” It includes the source references and leaves any unstated owner or contingency blank.
8. **Answers with evidence:** Asked “Is automated email reminder work part of the release?”, the assistant responds that the meeting notes show it was discussed but no scope decision was recorded. It cites the meeting note and recommends confirming the decision rather than assuming it is in scope.

This example shows why combining project artifacts matters: the proposal establishes the commitment and dependency, while the meeting note shows current status and the next action. The system can connect them without confusing a discussion with an approved plan or turning a possible delay into a certainty.

## 6. Summary of what I learned

- RAG prepares project documents for retrieval and supplies relevant evidence to a language model at answer time; it does not retrain the model.
- The RAG workflow runs from ingestion and extraction through chunking, embeddings, vector storage, similarity search, retrieval, and context construction for grounded answers.
- Metadata, source references, access control, freshness, and uncertainty handling are essential to make project answers useful and auditable.
- A multi-agent design assigns bounded responsibilities to specialized agents and uses an orchestrator to validate and combine their results.
- Scope, deliverables, tasks, milestones, risks, blockers, progress, and health are related but distinct project-management concepts.
- RAG provides the evidence; agents extract and analyze it; the assistant communicates the result with citations and appropriate limits.

## 7. What needs to be implemented next

The next step should turn the learning into a design before building the full project. In line with the milestone, define:

1. The system architecture and data flow from upload to grounded answer.
2. Agent roles, input/output contracts, orchestration, and human-review points.
3. Document and chunk data models, including project and source metadata.
4. The ingestion module for PDF, DOCX, CSV, and plain text, with extraction and validation.
5. The initial RAG pipeline: chunking, embedding generation, vector-store indexing, and a basic retrieval test.

After that foundation is designed and reviewed, implementation can proceed incrementally. This step intentionally contains learning notes only, not the complete application or frontend/backend code.
