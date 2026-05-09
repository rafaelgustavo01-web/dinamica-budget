revision = "028"
down_revision = "027"

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID


def upgrade():
    """
    F4-02 — PQ Client Profiles + Learning Loop.

    Adiciona à tabela existente pq_layout_cliente:
      - is_aprovado: indica se o perfil foi validado por humano
      - aprovado_por_id / aprovado_em: rastreabilidade da aprovação
      - aliases_json: aliases extras por campo (JSON text) para flexibilidade de colunas
      - score_confianca: último score de matching do perfil contra um arquivo

    Cria pq_layout_historico: audit trail de mudanças no perfil
    (criação, alteração, aprovação, uso) com snapshot JSON imutável.
    """
    # ── Colunas novas em pq_layout_cliente ────────────────────────────────
    op.add_column(
        "pq_layout_cliente",
        sa.Column("is_aprovado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        schema="operacional",
    )
    op.add_column(
        "pq_layout_cliente",
        sa.Column(
            "aprovado_por_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("operacional.usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="operacional",
    )
    op.add_column(
        "pq_layout_cliente",
        sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "pq_layout_cliente",
        sa.Column("aliases_json", sa.Text(), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "pq_layout_cliente",
        sa.Column("score_confianca", sa.Numeric(5, 4), nullable=True),
        schema="operacional",
    )

    # Índice leve para buscar perfis aprovados por cliente
    op.create_index(
        "ix_pq_layout_cliente_aprovado",
        "pq_layout_cliente",
        ["cliente_id", "is_aprovado"],
        schema="operacional",
    )

    # ── Tabela de histórico / audit trail ─────────────────────────────────
    op.create_table(
        "pq_layout_historico",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "layout_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("operacional.pq_layout_cliente.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "cliente_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("acao", sa.String(20), nullable=False),
        sa.Column(
            "usuario_id",
            PGUUID(as_uuid=True),
            sa.ForeignKey("operacional.usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("detalhe_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="operacional",
    )


def downgrade():
    """Rollback completo: remove colunas, índices e tabela de histórico."""
    op.drop_table("pq_layout_historico", schema="operacional")
    op.drop_index("ix_pq_layout_cliente_aprovado", table_name="pq_layout_cliente", schema="operacional")
    op.drop_column("pq_layout_cliente", "score_confianca", schema="operacional")
    op.drop_column("pq_layout_cliente", "aliases_json", schema="operacional")
    op.drop_column("pq_layout_cliente", "aprovado_em", schema="operacional")
    op.drop_column("pq_layout_cliente", "aprovado_por_id", schema="operacional")
    op.drop_column("pq_layout_cliente", "is_aprovado", schema="operacional")
