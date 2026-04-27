"""Add versioning and approval fields to propostas

Revision ID: 022
Revises: 021
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# revision identifiers, used by Alembic.
revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ADD VALUE ao enum FORA de transação (PostgreSQL não aceita dentro de transação)
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE status_proposta_enum "
            "ADD VALUE IF NOT EXISTS 'AGUARDANDO_APROVACAO'"
        )

    # 2. Adicionar colunas de versionamento e aprovação
    op.add_column(
        "propostas",
        sa.Column("proposta_root_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("numero_versao", sa.Integer(), nullable=True, server_default="1"),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("versao_anterior_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("is_versao_atual", sa.Boolean(), nullable=True, server_default="TRUE"),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("is_fechada", sa.Boolean(), nullable=True, server_default="FALSE"),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("requer_aprovacao", sa.Boolean(), nullable=True, server_default="FALSE"),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("aprovado_por_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "propostas",
        sa.Column("motivo_revisao", sa.Text(), nullable=True),
        schema="operacional",
    )

    # 3. Índice em proposta_root_id
    op.create_index(
        op.f("ix_operacional_propostas_proposta_root_id"),
        "propostas",
        ["proposta_root_id"],
        unique=False,
        schema="operacional",
    )

    # 4. Backfill: todas as propostas existentes viram versão 1 com root_id = id
    op.execute("""
        UPDATE operacional.propostas
        SET proposta_root_id = id,
            numero_versao = 1,
            is_versao_atual = TRUE,
            is_fechada = FALSE
        WHERE proposta_root_id IS NULL
    """)

    # 5. FK versao_anterior_id (auto-referência, nullable)
    op.create_foreign_key(
        "fk_proposta_versao_anterior",
        "propostas",
        "propostas",
        ["versao_anterior_id"],
        ["id"],
        source_schema="operacional",
        referent_schema="operacional",
    )

    # 6. FK aprovado_por_id → usuarios
    op.create_foreign_key(
        "fk_proposta_aprovado_por",
        "propostas",
        "usuarios",
        ["aprovado_por_id"],
        ["id"],
        source_schema="operacional",
        referent_schema="operacional",
    )

    # 7. Unique constraint (proposta_root_id, numero_versao)
    op.create_unique_constraint(
        "uq_proposta_versao",
        "propostas",
        ["proposta_root_id", "numero_versao"],
        schema="operacional",
    )


def downgrade() -> None:
    op.drop_constraint("uq_proposta_versao", "propostas", schema="operacional")
    op.drop_constraint("fk_proposta_aprovado_por", "propostas", schema="operacional", type_="foreignkey")
    op.drop_constraint("fk_proposta_versao_anterior", "propostas", schema="operacional", type_="foreignkey")
    op.drop_index(
        op.f("ix_operacional_propostas_proposta_root_id"),
        table_name="propostas",
        schema="operacional",
    )
    op.drop_column("propostas", "motivo_revisao", schema="operacional")
    op.drop_column("propostas", "aprovado_em", schema="operacional")
    op.drop_column("propostas", "aprovado_por_id", schema="operacional")
    op.drop_column("propostas", "requer_aprovacao", schema="operacional")
    op.drop_column("propostas", "is_fechada", schema="operacional")
    op.drop_column("propostas", "is_versao_atual", schema="operacional")
    op.drop_column("propostas", "versao_anterior_id", schema="operacional")
    op.drop_column("propostas", "numero_versao", schema="operacional")
    op.drop_column("propostas", "proposta_root_id", schema="operacional")
    # Note: AGUARDANDO_APROVACAO cannot be removed from enum in PostgreSQL without recreating it
