"""Create base tables

Revision ID: 001
Revises:
Create Date: 2026-03-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── usuarios ──────────────────────────────────────────────────────────────
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("is_admin", sa.Boolean, default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    # ── clientes ──────────────────────────────────────────────────────────────
    op.create_table(
        "clientes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome_fantasia", sa.String(255), nullable=False),
        sa.Column("cnpj", sa.String(14), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
    )
    op.create_index("ix_clientes_cnpj", "clientes", ["cnpj"], unique=True)

    # ── categoria_recurso ─────────────────────────────────────────────────────
    op.create_table(
        "categoria_recurso",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("descricao", sa.String(100), nullable=False),
        sa.Column(
            "tipo_custo",
            sa.Enum("HORISTA", "MENSALISTA", "GLOBAL", name="tipo_custo_enum"),
            nullable=False,
        ),
    )

    # ── servico_tcpo ──────────────────────────────────────────────────────────
    op.create_table(
        "servico_tcpo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo_origem", sa.String(50), nullable=False),
        sa.Column("descricao", sa.Text, nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=False),
        sa.Column("categoria_id", sa.Integer, sa.ForeignKey("categoria_recurso.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_servico_tcpo_codigo_origem", "servico_tcpo", ["codigo_origem"])

    # ── composicao_tcpo ───────────────────────────────────────────────────────
    op.create_table(
        "composicao_tcpo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("servico_pai_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("servico_tcpo.id"), nullable=False),
        sa.Column("insumo_filho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("servico_tcpo.id"), nullable=False),
        sa.Column("quantidade_consumo", sa.Numeric(10, 4), nullable=False),
    )
    op.create_index("ix_composicao_tcpo_pai", "composicao_tcpo", ["servico_pai_id"])
    op.create_index("ix_composicao_tcpo_filho", "composicao_tcpo", ["insumo_filho_id"])

    # ── historico_busca_cliente ───────────────────────────────────────────────
    op.create_table(
        "historico_busca_cliente",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("texto_busca", sa.Text, nullable=False),
        sa.Column("usuario_origem", sa.String(100), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_historico_busca_cliente_id", "historico_busca_cliente", ["cliente_id"])

    # ── associacao_tcpo ───────────────────────────────────────────────────────
    op.create_table(
        "associacao_tcpo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("texto_busca_original", sa.String(255), nullable=False),
        sa.Column("servico_tcpo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("servico_tcpo.id"), nullable=False),
        sa.Column(
            "origem_associacao",
            sa.Enum("MANUAL_USUARIO", "IA_CONSOLIDADA", name="origem_associacao_enum"),
            nullable=False,
        ),
        sa.Column("confiabilidade_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_associacao_tcpo_cliente", "associacao_tcpo", ["cliente_id"])
    op.create_index("ix_associacao_tcpo_servico", "associacao_tcpo", ["servico_tcpo_id"])


def downgrade() -> None:
    op.drop_table("associacao_tcpo")
    op.drop_table("historico_busca_cliente")
    op.drop_table("composicao_tcpo")
    op.drop_table("servico_tcpo")
    op.drop_table("categoria_recurso")
    op.drop_table("clientes")
    op.drop_table("usuarios")
    op.execute("DROP TYPE IF EXISTS tipo_custo_enum")
    op.execute("DROP TYPE IF EXISTS origem_associacao_enum")
