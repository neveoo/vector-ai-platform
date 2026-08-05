import enum
import uuid

from sqlalchemy import String, Text, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TenantScopedMixin, TimestampMixin


class WorkflowInstanceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecision(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WorkflowTemplate(Base, TenantScopedMixin, TimestampMixin):
    """
    A reusable approval workflow definition, e.g. 'Contract Review'.
    Kept intentionally simple (a single linear approver chain) --
    this is a portfolio project, not a full BPMN engine. The README
    should note a real state-machine/DAG engine as a 'next step'.
    """
    __tablename__ = "workflow_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Document classes that trigger this workflow automatically, e.g. ["contract", "invoice"]
    trigger_classes: Mapped[list[str] | None] = mapped_column(ARRAY(String(100)), nullable=True)

    __table_args__ = ({"comment": "RLS-protected: see 0002_enable_row_level_security.py"},)


class WorkflowInstance(Base, TenantScopedMixin, TimestampMixin):
    """One in-flight (or completed) run of a WorkflowTemplate against a specific document."""
    __tablename__ = "workflow_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    status: Mapped[WorkflowInstanceStatus] = mapped_column(
        Enum(WorkflowInstanceStatus, name="workflow_instance_status"), default=WorkflowInstanceStatus.PENDING
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = ({"comment": "RLS-protected: see 0002_enable_row_level_security.py"},)


class Approval(Base, TenantScopedMixin, TimestampMixin):
    """A single approver's decision within a workflow instance."""
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision"), default=ApprovalDecision.PENDING
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = ({"comment": "RLS-protected: see 0002_enable_row_level_security.py"},)
