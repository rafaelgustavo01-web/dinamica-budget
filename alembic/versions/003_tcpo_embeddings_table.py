"""Create tcpo_embeddings table with Vector column and HNSW index

Revision ID: 003
Revises: 002
Create Date: 2026-03-26

Requires migration 002 (pgvector extension) to be applied first.
The embedding column is nullable so existing rows are not blocked.
Embeddings are populated via POST /admin/compute-embeddings.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


def upgrade() -> None:
    # Create base table first (always succeeds)
    op.create_table(
        "tcpo_embeddings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("servico_tcpo.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("vetor", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
    )

    # Conditionally upgrade vetor column to vector type if pgvector is installed
    op.execute(
        f"""
        DO $emb$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
                ALTER TABLE tcpo_embeddings DROP COLUMN IF EXISTS vetor;
                EXECUTE 'ALTER TABLE tcpo_embeddings ADD COLUMN vetor vector({EMBEDDING_DIM})';
                CREATE INDEX ix_tcpo_embeddings_hnsw
                    ON tcpo_embeddings
                    USING hnsw (vetor vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
            ELSE
                RAISE NOTICE 'pgvector not installed; tcpo_embeddings.vetor kept as TEXT';
            END IF;
        END $emb$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tcpo_embeddings_hnsw")
    op.drop_table("tcpo_embeddings")
