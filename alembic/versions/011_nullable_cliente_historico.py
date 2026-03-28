"""Make historico_busca_cliente.cliente_id nullable and populate descricao_tokens

Revision ID: 011
Revises: 010
Create Date: 2026-03-28

Changes:
  - historico_busca_cliente.cliente_id: NOT NULL → NULL (supports busca genérica)
  - Populate servico_tcpo.descricao_tokens for existing rows using SQL normalization
    (lowercase + strip accents via unaccent equivalent using pg_catalog + regexp_replace)
"""

from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Make cliente_id nullable to support busca genérica (no client context)
    op.alter_column(
        "historico_busca_cliente",
        "cliente_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    # 2. Populate descricao_tokens for existing servico_tcpo rows.
    #    Uses immutable SQL normalization: lowercase + remove accents (unaccent extension
    #    may not be available; fall back to translate for common PT diacritics).
    #    Full Python-equivalent normalize_text runs at application level on new records.
    op.execute(
        r"""
        UPDATE servico_tcpo
        SET descricao_tokens = lower(
            regexp_replace(
                translate(
                    lower(descricao),
                    'áàãâäéèêëíìîïóòõôöúùûüçñÁÀÃÂÄÉÈÊËÍÌÎÏÓÒÕÔÖÚÙÛÜÇÑ',
                    'aaaaaeeeeiiiiooooouuuucnAAAAAEEEEIIIIOOOOOUUUUCN'
                ),
                '[^a-z0-9\s]',
                ' ',
                'g'
            )
        )
        WHERE descricao_tokens IS NULL;
        """
    )


def downgrade() -> None:
    op.alter_column(
        "historico_busca_cliente",
        "cliente_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
