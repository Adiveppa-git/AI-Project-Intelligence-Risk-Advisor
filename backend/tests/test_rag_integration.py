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


def test_list_documents_groups_chunks_and_preserves_metadata(
    embedding_service: SentenceTransformerEmbeddingService,
    tmp_path,
) -> None:
    storage_path = tmp_path / "list-chroma"
    service = RAGPipelineService(
        chunk_size=100,
        chunk_overlap=20,
        storage_path=storage_path,
    )
    service.embedding_service = embedding_service

    # 1. Empty store check
    empty_docs = service.list_documents()
    assert empty_docs == []
    assert service.vector_store.get_indexed_documents() == []

    # 2. Index first document (long text => multiple chunks)
    doc1 = make_document(
        "architecture_spec.pdf",
        "The Enterprise Cloud Analytics Platform modernizes telemetry collection. "
        "It provides real-time event streaming via Kafka brokers and RBAC gateway security. "
        "Integration testing occurs on staging Kubernetes clusters before production rollout.",
    )
    doc1.file_type = "pdf"
    indexed1, chunks1 = service.index_document(doc1)
    assert chunks1 >= 2, "Expected at least 2 chunks for document 1"

    # 3. Index second document (short text => 1 chunk)
    doc2 = make_document(
        "sprint_notes.txt",
        "Sprint 14 meeting notes: Blocker on SecOps approval for OAuth tokens.",
    )
    doc2.file_type = "txt"
    indexed2, chunks2 = service.index_document(doc2)
    assert chunks2 == 1, "Expected 1 chunk for document 2"

    # Total chunks in vector store is sum of chunks
    total_stored_chunks = service.vector_store.count()
    assert total_stored_chunks == chunks1 + chunks2

    # 4. Verify list_documents groups by document_id
    docs = service.list_documents()
    # Distinct documents count MUST be 2, NOT total chunks
    assert len(docs) == 2, f"Expected 2 documents, got {len(docs)}"

    doc1_entry = next((d for d in docs if d["document_id"] == indexed1.document_id), None)
    assert doc1_entry is not None
    assert doc1_entry["filename"] == "architecture_spec.pdf"
    assert doc1_entry["file_type"] == "pdf"
    assert doc1_entry["chunk_count"] == chunks1
    assert doc1_entry["status"] == "Indexed"
    assert doc1_entry["uploaded_at"] is not None

    doc2_entry = next((d for d in docs if d["document_id"] == indexed2.document_id), None)
    assert doc2_entry is not None
    assert doc2_entry["filename"] == "sprint_notes.txt"
    assert doc2_entry["file_type"] == "txt"
    assert doc2_entry["chunk_count"] == 1
    assert doc2_entry["status"] == "Indexed"


def test_list_documents_api_endpoints(
    embedding_service: SentenceTransformerEmbeddingService,
    tmp_path,
    monkeypatch,
) -> None:
    import app.api.routes as doc_routes
    import app.api.rag_routes as rag_routes

    service = RAGPipelineService(
        chunk_size=120,
        chunk_overlap=20,
        storage_path=tmp_path / "api-list-chroma",
    )
    service.embedding_service = embedding_service
    monkeypatch.setattr(doc_routes, "rag_service", service)
    monkeypatch.setattr(rag_routes, "rag_service", service)

    client = TestClient(app)

    # 1. Check empty state returns 200 with empty list
    res_empty = client.get("/api/documents")
    assert res_empty.status_code == 200
    assert res_empty.json()["total_documents"] == 0
    assert res_empty.json()["total_chunks"] == 0
    assert res_empty.json()["documents"] == []

    # 2. Index a document via API
    res_index = client.post(
        "/api/rag/index",
        files={
            "file": (
                "project_charter.txt",
                b"Enterprise Cloud Analytics Platform charter specification.",
                "text/plain",
            )
        },
    )
    assert res_index.status_code == 201

    # 3. Query GET /api/documents
    res_docs = client.get("/api/documents")
    assert res_docs.status_code == 200
    data = res_docs.json()
    assert data["total_documents"] == 1
    assert data["total_chunks"] >= 1
    doc_item = data["documents"][0]
    assert doc_item["filename"] == "project_charter.txt"
    assert doc_item["chunk_count"] >= 1
    assert doc_item["status"] == "Indexed"

    # 4. Query GET /api/rag/documents (matches /api/documents)
    res_rag_docs = client.get("/api/rag/documents")
    assert res_rag_docs.status_code == 200
    assert res_rag_docs.json() == data

