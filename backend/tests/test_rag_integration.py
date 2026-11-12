import math
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import IngestedDocument
from app.services.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    SentenceTransformerEmbeddingService,
)
from app.services.rag_pipeline import RAGPipelineService
from app.services.vector_store import ChromaVectorStore


@pytest.fixture(scope="module")
def embedding_service() -> SentenceTransformerEmbeddingService:
    return SentenceTransformerEmbeddingService(DEFAULT_EMBEDDING_MODEL)


def make_document(filename: str, text: str) -> IngestedDocument:
    from datetime import datetime, timezone

    return IngestedDocument(
        document_id=str(uuid.uuid4()),
        filename=filename,
        file_type="txt",
        file_size_bytes=len(text.encode("utf-8")),
        text=text,
        uploaded_at=datetime.now(timezone.utc),
    )


def test_actual_sentence_transformer_generates_normalized_embeddings(
    embedding_service: SentenceTransformerEmbeddingService,
) -> None:
    vectors = embedding_service.embed_documents(
        ["The release is delayed by integration testing."]
    )
    assert len(vectors) == 1
    assert len(vectors[0]) == 384
    assert all(math.isfinite(value) for value in vectors[0])
    assert math.isclose(math.sqrt(sum(value * value for value in vectors[0])), 1.0, rel_tol=1e-4)
    assert embedding_service.is_loaded
    assert len(embedding_service.embed_query("When is the release?")) == 384


def test_embeddings_reject_empty_inputs(
    embedding_service: SentenceTransformerEmbeddingService,
) -> None:
    assert embedding_service.embed_documents([]) == []
    with pytest.raises(ValueError, match="cannot be empty"):
        embedding_service.embed_query(" \t")
    with pytest.raises(ValueError, match="cannot be empty"):
        embedding_service.embed_documents([""])


def test_indexing_is_idempotent_and_semantic_search_persists(
    embedding_service: SentenceTransformerEmbeddingService,
    tmp_path,
) -> None:
    storage_path = tmp_path / "chroma"
    service = RAGPipelineService(
        chunk_size=160,
        chunk_overlap=20,
        storage_path=storage_path,
    )
    service.embedding_service = embedding_service
    document = make_document(
        "delivery.txt",
        "The release is delayed because database migration tests failed. "
        "The platform team must repair the failing integration test before launch.",
    )
    indexed, count = service.index_document(document)
    assert count > 0
    first_count = service.vector_store.count()
    reindexed, count_again = service.index_document(document)
    assert reindexed.document_id == indexed.document_id
    assert count_again == count
    assert service.vector_store.count() == first_count

    results = service.search("Why might the software launch be late?", top_k=1)
    assert results
    assert results[0].document_id == indexed.document_id
    assert "database migration tests failed" in results[0].text
    assert results[0].similarity <= 1.0
    assert results[0].metadata["filename"] == "delivery.txt"

    reopened = ChromaVectorStore(storage_path)
    assert reopened.count() == first_count
    query_vector = embedding_service.embed_query("What testing problem delays release?")
    persisted_results = reopened.search(query_vector, top_k=1)
    assert persisted_results[0].document_id == indexed.document_id


def test_multiple_documents_and_document_deletion(
    embedding_service: SentenceTransformerEmbeddingService,
    tmp_path,
) -> None:
    service = RAGPipelineService(
        chunk_size=300,
        chunk_overlap=30,
        storage_path=tmp_path / "multiple-docs",
    )
    service.embedding_service = embedding_service
    first, _ = service.index_document(
        make_document(
            "onboarding.txt",
            "Employee onboarding includes identity verification and profile setup.",
        )
    )
    second, _ = service.index_document(
        make_document(
            "payments.txt",
            "Payment reconciliation compares invoices with completed transactions.",
        )
    )
    assert service.vector_store.count() == 2
    matches = service.search("How are invoices reconciled?", top_k=2)
    assert matches[0].document_id == second.document_id
    assert first.document_id != second.document_id
    assert service.vector_store.delete_document(first.document_id) == 1
    assert service.vector_store.count() == 1


def test_empty_query_and_empty_collection(
    embedding_service: SentenceTransformerEmbeddingService,
    tmp_path,
) -> None:
    service = RAGPipelineService(storage_path=tmp_path / "empty")
    service.embedding_service = embedding_service
    assert service.vector_store.count() == 0
    assert service.search("a meaningful query") == []
    with pytest.raises(ValueError, match="query cannot be empty"):
        service.search("  ")


def test_rag_api_indexes_searches_and_reports_status(
    embedding_service: SentenceTransformerEmbeddingService,
    tmp_path,
    monkeypatch,
) -> None:
    import app.api.rag_routes as rag_routes

    service = RAGPipelineService(storage_path=tmp_path / "api-chroma")
    service.embedding_service = embedding_service
    monkeypatch.setattr(rag_routes, "rag_service", service)
    client = TestClient(app)

    indexed = client.post(
        "/api/rag/index",
        files={
            "file": (
                "release-notes.txt",
                b"The release is delayed because database migration tests failed.",
                "text/plain",
            )
        },
    )
    assert indexed.status_code == 201
    indexed_body = indexed.json()
    assert indexed_body["vectors_stored"] == indexed_body["chunks_created"] == 1

    searched = client.post(
        "/api/rag/search",
        json={"query": "Why is the launch late?", "top_k": 1},
    )
    assert searched.status_code == 200
    assert "database migration tests failed" in searched.json()["results"][0]["text"]
    assert searched.json()["results"][0]["document_id"] == indexed_body["document"]["document_id"]

    status_response = client.get("/api/rag/status")
    assert status_response.status_code == 200
    assert status_response.json()["indexed_chunks"] == 1
    assert status_response.json()["embedding_model_loaded"] is True

    empty_query = client.post(
        "/api/rag/search",
        json={"query": " \t", "top_k": 1},
    )
    assert empty_query.status_code == 422
