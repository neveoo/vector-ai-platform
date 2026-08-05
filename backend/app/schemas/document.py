from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus
    predicted_class: str | None
    predicted_class_confidence: float | None
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    message: str = "Document received and queued for processing."
