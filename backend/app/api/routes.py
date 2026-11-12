from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.document import IngestedDocument
from app.services.document_ingestion import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DocumentIngestionError,
    DocumentIngestionService,
)

router = APIRouter()
ingestion_service = DocumentIngestionService()


@router.post(
    "/documents/upload",
    response_model=IngestedDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and extract a project document",
)
async def upload_document(
    file: UploadFile = File(...),
) -> IngestedDocument:
    content = await file.read(DEFAULT_MAX_FILE_SIZE_BYTES + 1)
    await file.close()
    try:
        return ingestion_service.ingest(file.filename, content)
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
