import hashlib
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from app.models.document import IngestedDocument
from app.models.rag import SearchResult
from app.services.chunking import DocumentChunkingService
from app.services.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    SentenceTransformerEmbeddingService,
)
from app.services.vector_store import ChromaVectorStore


class RAGPipelineService:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        embedding_model: str | None = None,
        storage_path: str | Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        resolved_chunk_size = (
            chunk_size
            if chunk_size is not None
            else int(os.getenv("RAG_CHUNK_SIZE", "1000"))
        )
        resolved_overlap = (
            chunk_overlap
            if chunk_overlap is not None
            else int(os.getenv("RAG_CHUNK_OVERLAP", "150"))
        )
        self.chunker = DocumentChunkingService(resolved_chunk_size, resolved_overlap)
        self.embedding_service = SentenceTransformerEmbeddingService(
            embedding_model or os.getenv("RAG_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        )
        default_storage = Path(__file__).resolve().parents[2] / "data" / "chroma"
        resolved_path = (
            storage_path
            or os.getenv("RAG_VECTOR_DB_PATH")
            or default_storage
        )
        self.vector_store = ChromaVectorStore(
            persist_directory=resolved_path,
            collection_name=collection_name or os.getenv(
                "RAG_COLLECTION_NAME", "project_chunks"
            ),
        )

    @property
    def embedding_model(self) -> str:
        return self.embedding_service.model_name

    def index_document(self, document: IngestedDocument) -> tuple[IngestedDocument, int]:
        stable_id = str(
            uuid5(
                NAMESPACE_URL,
                f"project-document:{document.filename}:"
                f"{hashlib.sha256(document.text.encode('utf-8')).hexdigest()}",
            )
        )
        indexed_document = document.model_copy(update={"document_id": stable_id})
        chunks = self.chunker.chunk_document(indexed_document.model_dump())
        embeddings = self.embedding_service.embed_documents(
            [chunk.text for chunk in chunks]
        )
        stored = self.vector_store.index_chunks(chunks, embeddings)
        return indexed_document, stored

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        if self.vector_store.count() == 0:
            return []
        query_embedding = self.embedding_service.embed_query(query)
        return self.vector_store.search(query_embedding, top_k=top_k)

    def status(self) -> dict[str, str | int | bool]:
        return {
            "status": "ready",
            "collection_name": self.vector_store.collection_name,
            "indexed_chunks": self.vector_store.count(),
            "embedding_model": self.embedding_model,
            "embedding_model_loaded": self.embedding_service.is_loaded,
            "persistent_storage": True,
            "storage_path": str(self.vector_store.persist_directory),
        }
