"""Add search indexes for S-05 benchmarks

Revision ID: 016
Revises: 015
Create Date: 2026-04-22
"""

from alembic import op


revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_base_tcpo_descricao_trgm
        ON referencia.base_tcpo
        USING gin (descricao gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tcpo_embeddings_vetor_hnsw
        ON referencia.tcpo_embeddings
        USING hnsw (vetor vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_associacao_cliente_texto
        ON operacional.associacao_inteligente (cliente_id, texto_busca_normalizado)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS operacional.idx_associacao_cliente_texto")
    op.execute("DROP INDEX IF EXISTS referencia.idx_tcpo_embeddings_vetor_hnsw")
    op.execute("DROP INDEX IF EXISTS referencia.idx_base_tcpo_descricao_trgm")
