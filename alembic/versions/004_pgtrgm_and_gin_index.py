"""Enable pg_trgm extension and GIN index for fuzzy search

Revision ID: 004
Revises: 003
Create Date: 2026-03-26

pg_trgm enables similarity() function used in Phase 2 fuzzy search.
The GIN index makes similarity() queries fast (avoids full table scan).
"""

from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE INDEX ix_servico_tcpo_descricao_gin
        ON servico_tcpo
        USING gin (descricao gin_trgm_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_servico_tcpo_descricao_gin")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
