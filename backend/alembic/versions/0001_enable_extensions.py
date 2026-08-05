"""enable required postgres extensions

Revision ID: 0001
Revises:
Create Date: 2026-08-02
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector: gives us the `vector` column type + similarity search
    # operators (<->, <#>, <=>) used by DocumentChunk.embedding
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # pgcrypto: gen_random_uuid() as a DB-side default if ever needed
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
    op.execute("DROP EXTENSION IF EXISTS vector")
