from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.routes import ingestion_service
from app.models.rag import (
    IndexDocumentResponse,
    RAGStatusResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.embeddings import EmbeddingError
from app.services.document_ingestion import DocumentIngestionError
from app.services.rag_pipeline import RAGPipelineService
from app.services.vector_store import VectorStoreError

router = APIRouter(prefix="/rag", tags=["rag"])
rag_service = RAGPipelineService()
MAX_UPLOAD_BYTES = ingestion_service.max_file_size_bytes


@router.post(
    "/index",
    response_model=IndexDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest, chunk, embed, and index a document",
)
async def index_document(file: UploadFile = File(...)) -> IndexDocumentResponse:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    try:
        document = ingestion_service.ingest(file.filename, content)
    except DocumentIngestionError as exc:
        message = str(exc)
        code = (
            413
            if message.startswith("File exceeds")
            else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            if message.startswith("Unsupported file type")
            else 422
        )
        raise HTTPException(status_code=code, detail=message) from exc

    try:
        indexed_document, stored = rag_service.index_document(document)
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return IndexDocumentResponse(
        document=indexed_document,
        chunks_created=stored,
        vectors_stored=stored,
        embedding_model=rag_service.embedding_model,
    )


@router.post("/search", response_model=SearchResponse, summary="Search indexed documents")
def search_documents(request: SearchRequest) -> SearchResponse:
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="query cannot be empty",
        )
    try:
        results = rag_service.search(request.query, top_k=request.top_k)
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return SearchResponse(query=request.query, results=results)


@router.get("/status", response_model=RAGStatusResponse, summary="Check RAG pipeline status")
def rag_status() -> RAGStatusResponse:
    try:
        details = rag_service.status()
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return RAGStatusResponse(**details, checked_at=datetime.now(timezone.utc))
