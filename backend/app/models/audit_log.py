import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TenantScopedMixin


class AuditLog(Base, TenantScopedMixin):
    """
    Append-only record of every meaningful action in the system.

    Deliberately has no `updated_at` column -- audit rows should never
    be modified. The migration that creates this table also adds a
    Postgres trigger that raises an exception on UPDATE or DELETE, so
    this isn't just a convention, it's enforced by the database even
    against a bug or a compromised app-layer credential.
    """
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # null = system action
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "document.upload", "approval.decide"
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "document", "workflow_instance"
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = ({"comment": "RLS-protected + append-only via trigger, see 0002_enable_row_level_security.py"},)
