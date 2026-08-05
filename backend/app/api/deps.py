"""
Shared request dependencies.

`get_tenant_db` is the one every tenant-scoped route should depend on:
it decodes the JWT, pulls tenant_id + user_id out of it, opens a DB
session, and calls set_tenant_context so RLS policies are active for
the lifetime of the request. Routes never need to remember to filter
by tenant -- the database does it for them.
"""
from collections.abc import Generator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, set_tenant_context

settings = get_settings()
bearer_scheme = HTTPBearer()


class CurrentUser:
    def __init__(self, user_id: UUID, tenant_id: UUID, role: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return CurrentUser(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]),
            role=payload.get("role", "member"),
        )
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def get_tenant_db(
    current_user: CurrentUser = Depends(get_current_user),
) -> Generator[Session, None, None]:
    """
    The dependency almost every route in this app should use.
    Opens a session, sets the RLS tenant context for it, yields it,
    and closes it -- all scoped to a single request.
    """
    db = SessionLocal()
    try:
        set_tenant_context(db, current_user.tenant_id)
        yield db
    finally:
        db.close()


def require_role(*allowed_roles: str):
    """Simple RBAC dependency factory, e.g. Depends(require_role('admin', 'approver'))."""

    def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return checker
