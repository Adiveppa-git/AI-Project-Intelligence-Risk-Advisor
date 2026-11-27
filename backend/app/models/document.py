from datetime import datetime

from pydantic import BaseModel, Field


class IngestedDocument(BaseModel):
    """Metadata and extracted text returned for an uploaded document."""

    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int = Field(ge=0)
    text: str
    uploaded_at: datetime


class UploadedDocumentItem(BaseModel):
    """Represents a unique uploaded and indexed document in the vector store."""

    document_id: str
    filename: str
    file_type: str | None = None
    file_size_bytes: int | None = None
    uploaded_at: str | None = None
    chunk_count: int = Field(default=0, ge=0)
    status: str = "Indexed"


class UploadedDocumentsResponse(BaseModel):
    """Response containing all unique uploaded documents and aggregate counts."""

    documents: list[UploadedDocumentItem] = Field(default_factory=list)
    total_documents: int = Field(default=0, ge=0)
    total_chunks: int = Field(default=0, ge=0)

