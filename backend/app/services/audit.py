"""
Central place to write audit log entries so every route logs the same
shape of data. Call this at the end of any state-changing action.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    *,
    tenant_id: UUID,
    actor_user_id: UUID | None,
    action: str,
    resource_type: str,
    resource_id: UUID,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.add(entry)
    db.flush()  # get entry.id populated without committing the caller's transaction early
    return entry
