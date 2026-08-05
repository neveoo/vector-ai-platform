"""
Database session management.

The important pattern here is `set_tenant_context`: every request that
touches tenant-scoped data must call this before running any queries.
It sets a Postgres session variable that our Row-Level Security (RLS)
policies check against. This means tenant isolation is enforced by the
database itself, not just by remembering to add `WHERE tenant_id = ...`
in every query -- a bug in application code can't leak data across
tenants because Postgres will silently filter rows the session isn't
allowed to see.

See: alembic/versions/0002_enable_row_level_security.py for the policies.
"""
from collections.abc import Generator
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def set_tenant_context(db: Session, tenant_id: UUID) -> None:
    """
    Set the Postgres session variable RLS policies key off of.

    `set_config(..., is_local=True)` scopes this to the current
    transaction only, so it can never leak between requests even if
    connections are pooled and reused.
    """
    db.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": str(tenant_id)})


def get_db() -> Generator[Session, None, None]:
    """
    Plain DB session dependency, with NO tenant context set.
    Use only for tenant-agnostic operations (e.g. creating a new tenant,
    system-level admin tasks). Everything else should use
    get_tenant_db below.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
