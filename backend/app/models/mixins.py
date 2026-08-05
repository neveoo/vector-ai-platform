import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin


@declarative_mixin
class TenantScopedMixin:
    """
    Mix into any model that belongs to a tenant. Every table using this
    mixin MUST have a matching RLS policy created in an Alembic
    migration (see 0002_enable_row_level_security.py) -- the column
    alone does not enforce isolation, the policy does.
    """
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
