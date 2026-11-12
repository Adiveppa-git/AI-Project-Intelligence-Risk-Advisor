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
