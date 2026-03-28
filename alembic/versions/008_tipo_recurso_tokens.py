"""Add TipoRecurso enum and tipo_recurso/descricao_tokens to servico_tcpo

Revision ID: 008
Revises: 007
Create Date: 2026-03-28

Changes:
  - CREATE TYPE tipo_recurso_enum (MO, INSUMO, FERRAMENTA, EQUIPAMENTO, SERVICO)
  - servico_tcpo.tipo_recurso: nullable column (TipoRecurso)
  - servico_tcpo.descricao_tokens: nullable text column
  - GIN trigram index on descricao_tokens for fuzzy search
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create the enum type (idempotent)
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE tipo_recurso_enum AS ENUM
                ('MO', 'INSUMO', 'FERRAMENTA', 'EQUIPAMENTO', 'SERVICO');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    # 2. Add tipo_recurso column
    op.add_column(
        "servico_tcpo",
        sa.Column(
            "tipo_recurso",
            postgresql.ENUM(
                "MO", "INSUMO", "FERRAMENTA", "EQUIPAMENTO", "SERVICO",
                name="tipo_recurso_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # 3. Add descricao_tokens column
    op.add_column(
        "servico_tcpo",
        sa.Column("descricao_tokens", sa.Text, nullable=True),
    )

    # 4. GIN trigram index for fast fuzzy search on descricao_tokens
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_servico_tcpo_tokens
        ON servico_tcpo USING gin (descricao_tokens gin_trgm_ops);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_servico_tcpo_tokens;")
    op.drop_column("servico_tcpo", "descricao_tokens")
    op.drop_column("servico_tcpo", "tipo_recurso")
    op.execute("DROP TYPE IF EXISTS tipo_recurso_enum;")
