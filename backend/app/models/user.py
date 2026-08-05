import enum
import uuid

from sqlalchemy import String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TenantScopedMixin, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"          # manage users, tenant settings
    APPROVER = "approver"    # can act on workflow approval steps
    MEMBER = "member"        # upload docs, search, ask questions


class User(Base, TenantScopedMixin, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.MEMBER)

    __table_args__ = ({"comment": "RLS-protected: see 0002_enable_row_level_security.py"},)
