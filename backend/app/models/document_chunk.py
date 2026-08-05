import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base
from app.models.mixins import TenantScopedMixin, TimestampMixin

settings = get_settings()


class DocumentChunk(Base, TenantScopedMixin, TimestampMixin):
    """
    A single retrievable unit of text from a document, plus its
    embedding vector. This is what RAG retrieval actually searches
    over -- not the whole document.

    Dimensions must match settings.embedding_dimensions, which in turn
    must match whatever embedding_model_name produces. Swapping
    embedding models later requires re-embedding all chunks (there's
    no cheap way around this -- flag it in the README as a known
    migration cost).
    """
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # order within the document
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Which section/heading this chunk fell under, if we could detect one.
    # Improves both retrieval (semantic chunking) and citation display.
    section_heading: Mapped[str | None] = mapped_column(String(500), nullable=True)

    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions), nullable=False)

    __table_args__ = ({"comment": "RLS-protected: see 0002_enable_row_level_security.py"},)
