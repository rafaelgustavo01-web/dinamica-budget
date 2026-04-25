"""Enable pgvector extension

Revision ID: 002
Revises: 001
Create Date: 2026-03-26

NOTE: Requires superuser or rds_superuser role in managed PostgreSQL.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use PL/pgSQL DO block so PostgreSQL handles the error gracefully
    # without propagating it through asyncpg to Python.
    op.execute(
        """
        DO $pgv$ BEGIN
            CREATE EXTENSION IF NOT EXISTS vector;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pgvector not installed, skipping: %', SQLERRM;
        END $pgv$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $pgv$ BEGIN
            DROP EXTENSION IF EXISTS vector;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pgvector drop skipped: %', SQLERRM;
        END $pgv$;
        """
    )
