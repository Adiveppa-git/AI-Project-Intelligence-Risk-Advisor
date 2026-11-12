# Data Model Design

## Purpose and boundary

This document specifies conceptual data contracts for the AI Project Intelligence & Risk Advisor. The examples use Python/Pydantic-style schemas to make field names, types, and relationships concrete. They are **documentation examples only**: no Python models, database tables, validation code, or application behavior are created in this step.

The design follows the architecture in [Step 2 System Architecture](./STEP2_SYSTEM_ARCHITECTURE.md). IDs are opaque identifiers; production implementations may use UUIDs or another stable ID format. Timestamps are timezone-aware. Nullable fields mean the source did not provide a value; the system must not invent one.

## Design principles

- Keep original document identity and source location so generated findings can be traced and corrected.
- Separate uploaded-source data from extracted chunks and derived project findings.
- Store embedding configuration with each vector so index versions remain interpretable.
- Represent project scope and operational records separately from evidence excerpts.
- Distinguish risk (a possible future event) from blocker (a current impediment).
- Treat AI-generated records as proposed until a human or an explicit workflow reviews them.
- Enforce project authorization in the service/storage layer; a `project_id` field alone is not access control.

## Shared types

```python
from datetime import date, datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class DocumentType(str, Enum):
    PROPOSAL = "proposal"
    SRS = "srs"
    MEETING_NOTES = "meeting_notes"
    PROGRESS_UPDATE = "progress_update"
    TASK_LIST = "task_list"
    OTHER = "other"

class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    PARTIAL = "partial"
    FAILED = "failed"

class FindingStatus(str, Enum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class SourceReference(BaseModel):
    document_id: str
    chunk_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)
    section: str | None = None
    row_number: int | None = Field(default=None, ge=1)
    quote: str | None = None

class Provenance(BaseModel):
    source_references: list[SourceReference] = Field(default_factory=list)
    generated_by: str | None = None
    generated_at: datetime | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
```

`SourceReference` points to the origin of a claim. Page, section, and row are optional because not every format provides all location types. `Provenance` records evidence and the origin of derived findings; confidence is optional and should not be treated as calibrated unless evaluated.

## Project information

```python
class Project(BaseModel):
    project_id: str
    name: str
    description: str | None = None
    objectives: list[str] = Field(default_factory=list)
    scope_in: list[str] = Field(default_factory=list)
    scope_out: list[str] = Field(default_factory=list)
    start_date: date | None = None
    target_end_date: date | None = None
    owner_id: str | None = None
    member_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

`Project` is the tenant boundary for documents and project findings. The implementation should apply authorization when reading and writing every project-scoped record.

## Uploaded document and document metadata

The uploaded document record identifies the original file and processing lifecycle. Metadata is separated so the content record stays focused on storage and processing; a document has one metadata object.

```python
class DocumentMetadata(BaseModel):
    document_type: DocumentType
    title: str | None = None
    author: str | None = None
    document_date: date | None = None
    language: str | None = None
    tags: list[str] = Field(default_factory=list)

class UploadedDocument(BaseModel):
    document_id: str
    project_id: str
    filename: str
    media_type: str
    file_size_bytes: int = Field(ge=0)
    checksum: str
    storage_uri: str
    uploaded_by: str
    uploaded_at: datetime
    metadata: DocumentMetadata
    processing_status: ProcessingStatus
    processing_error: str | None = None
    indexed_at: datetime | None = None
    active_revision: int = Field(default=1, ge=1)
```

The storage URI should be an internal reference, not a publicly accessible URL. A checksum can help detect identical content; duplicate behavior and revision policy need an explicit implementation decision. Metadata includes both user-provided and extracted values; the implementation should distinguish their source if both are editable.

## Document chunks

Chunks are text units prepared for retrieval. They inherit project and document identity so queries can be filtered and passages cited.

```python
class DocumentChunk(BaseModel):
    chunk_id: str
    project_id: str
    document_id: str
    document_revision: int = Field(ge=1)
    ordinal: int = Field(ge=0)
    text: str
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    section: str | None = None
    row_start: int | None = Field(default=None, ge=1)
    row_end: int | None = Field(default=None, ge=1)
    created_at: datetime
```

Page and row ranges are optional because different file formats have different structures. A chunk should stay linked to a specific document revision so replacing a file does not silently change the meaning of an old citation.

## Embeddings

An embedding belongs to a chunk and a particular model/index configuration. The vector dimension is model-specific and must be checked against the selected vector store. The vector itself may live in the vector database while this record stores its identity and configuration.

```python
class ChunkEmbedding(BaseModel):
    embedding_id: str
    project_id: str
    document_id: str
    chunk_id: str
    model_name: str
    model_version: str | None = None
    dimensions: int = Field(gt=0)
    vector: list[float] | None = None
    vector_store_key: str | None = None
    created_at: datetime
```

For large indexes, duplicating vectors in an application database may be unnecessary. The schema allows either a vector value or a reference to the vector-store entry; the implementation should choose one source of truth. Model/version and dimensions must remain consistent within a searchable index.

## Tasks and milestones

```python
class WorkStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"

class ProjectTask(BaseModel):
    task_id: str
    project_id: str
    title: str
    description: str | None = None
    status: WorkStatus = WorkStatus.NOT_STARTED
    owner_id: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    milestone_id: str | None = None
    depends_on_task_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    finding_status: FindingStatus = FindingStatus.PROPOSED

class ProjectMilestone(BaseModel):
    milestone_id: str
    project_id: str
    name: str
    description: str | None = None
    target_date: date | None = None
    status: WorkStatus = WorkStatus.NOT_STARTED
    task_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    finding_status: FindingStatus = FindingStatus.PROPOSED
```

Task dependencies and milestone membership are explicit references. Dates may be unknown. AI-extracted tasks and milestones begin as proposed findings until reviewed.

## Risks and blockers

Risks and blockers share project context and provenance but represent different states of concern. A risk describes an uncertain future event; a blocker describes an existing impediment to work.

```python
class RiskStatus(str, Enum):
    OPEN = "open"
    MITIGATING = "mitigating"
    MATERIALIZED = "materialized"
    CLOSED = "closed"

class Risk(BaseModel):
    risk_id: str
    project_id: str
    title: str
    cause: str | None = None
    event: str | None = None
    impact: str | None = None
    likelihood: Literal["low", "medium", "high", "unknown"] = "unknown"
    impact_level: Literal["low", "medium", "high", "unknown"] = "unknown"
    mitigation: str | None = None
    owner_id: str | None = None
    status: RiskStatus = RiskStatus.OPEN
    identified_at: datetime
    provenance: Provenance = Field(default_factory=Provenance)
    finding_status: FindingStatus = FindingStatus.PROPOSED

class Blocker(BaseModel):
    blocker_id: str
    project_id: str
    title: str
    description: str | None = None
    affected_task_ids: list[str] = Field(default_factory=list)
    owner_id: str | None = None
    identified_at: datetime
    resolved_at: datetime | None = None
    is_resolved: bool = False
    provenance: Provenance = Field(default_factory=Provenance)
    finding_status: FindingStatus = FindingStatus.PROPOSED
```

Likelihood and impact categories are intentionally simple for an initial design. A delivery forecast should retain assumptions and evidence instead of presenting a categorical risk level as a guaranteed prediction.

## Action items

```python
class ActionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class ActionItem(BaseModel):
    action_item_id: str
    project_id: str
    description: str
    owner_id: str | None = None
    due_date: date | None = None
    status: ActionStatus = ActionStatus.OPEN
    related_blocker_id: str | None = None
    related_risk_id: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    finding_status: FindingStatus = FindingStatus.PROPOSED
```

An action can have no assigned owner or due date if the source did not state one. Its provenance points back to the meeting note, progress update, or other source from which it was identified.

## Relationships

- One `Project` has many `UploadedDocument`, `ProjectTask`, `ProjectMilestone`, `Risk`, `Blocker`, and `ActionItem` records.
- One `UploadedDocument` has one `DocumentMetadata` object and many revision-specific `DocumentChunk` records.
- Each `DocumentChunk` belongs to one project and document revision and can have one or more `ChunkEmbedding` records when indexes or embedding models change.
- A `ProjectTask` may reference a milestone and other dependent tasks.
- A `ProjectMilestone` may reference multiple tasks.
- A `Blocker` may affect tasks; an `ActionItem` may be related to a blocker or risk.
- Any extracted or generated finding may contain one or more `SourceReference` entries through `Provenance`.

## Example end-to-end record lineage

For a meeting note that says, “The identity-provider test environment is unavailable; Priya will contact the platform team by 12 September”:

1. `UploadedDocument` identifies the meeting note and its project.
2. `DocumentChunk` stores the passage with a page/section reference if available.
3. `ChunkEmbedding` indexes the passage for semantic retrieval.
4. A proposed `Blocker` records the unavailable test environment, citing the chunk.
5. A proposed `ActionItem` records Priya's follow-up and due date, citing the same source.
6. A proposed `Risk` may link the blocker to possible test-schedule impact, but should include the additional evidence and assumptions behind that inference.

This lineage makes it possible to review an AI-generated finding against the original uploaded source.

## Implementation decisions deferred

These are intentionally left open for implementation planning: concrete database and vector-store products; ID generation; file storage and retention; chunk-size and overlap settings; embedding model and vector dimensions; deduplication and document revision policy; exact access-control roles; forecast calibration; and review/approval workflow. None needs to be guessed in this design deliverable.
