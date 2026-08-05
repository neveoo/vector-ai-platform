import enum
import uuid

from sqlalchemy import String, BigInteger, Enum, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TenantScopedMixin, TimestampMixin


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"          # file stored, not yet processed
    PROCESSING = "processing"      # chunking + embedding in progress
    READY = "ready"                # searchable / RAG-queryable
    FAILED = "failed"


class Document(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)  # S3 object key
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.UPLOADED
    )

    # Populated by the classifier (Phase 3: fine-tuned model, falls back
    # to LLM-prompted classification if no trained model is available yet)
    predicted_class: Mapped[str | None] = mapped_column(String(100), nullable=True)
    predicted_class_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "trained_model" | "llm_prompt"

    # Free-form metadata (page count, extracted title, etc.)
    doc_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = ({"comment": "RLS-protected: see 0002_enable_row_level_security.py"},)
