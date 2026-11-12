from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.document import IngestedDocument


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexDocumentResponse(BaseModel):
    document: IngestedDocument
    chunks_created: int = Field(ge=0)
    vectors_stored: int = Field(ge=0)
    embedding_model: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    distance: float
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class RAGStatusResponse(BaseModel):
    status: str
    collection_name: str
    indexed_chunks: int = Field(ge=0)
    embedding_model: str
    embedding_model_loaded: bool
    persistent_storage: bool
    storage_path: str
    checked_at: datetime
