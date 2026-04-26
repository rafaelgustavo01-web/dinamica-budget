"""Add pq_layout_cliente and pq_importacao_mapeamento

Revision ID: 018
Revises: 017
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE campo_sistema_pq_enum AS ENUM (
                'codigo', 'descricao', 'unidade', 'quantidade', 'observacao'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.create_table(
        "pq_layout_cliente",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False, server_default="Layout Padrao"),
        sa.Column("aba_nome", sa.String(100), nullable=True),
        sa.Column("linha_inicio", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cliente_id"], ["operacional.clientes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cliente_id", name="uq_pq_layout_cliente_cliente_id"),
        schema="operacional",
    )
    op.create_index(
        "ix_pq_layout_cliente_cliente_id", "pq_layout_cliente", ["cliente_id"], schema="operacional"
    )

    op.create_table(
        "pq_importacao_mapeamento",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("layout_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "campo_sistema",
            postgresql.ENUM(
                "codigo", "descricao", "unidade", "quantidade", "observacao",
                name="campo_sistema_pq_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("coluna_planilha", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["layout_id"], ["operacional.pq_layout_cliente.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("layout_id", "campo_sistema", name="uq_pq_mapeamento_layout_campo"),
        schema="operacional",
    )
    op.create_index(
        "ix_pq_mapeamento_layout_id", "pq_importacao_mapeamento", ["layout_id"], schema="operacional"
    )


def downgrade() -> None:
    op.drop_index("ix_pq_mapeamento_layout_id", table_name="pq_importacao_mapeamento", schema="operacional")
    op.drop_table("pq_importacao_mapeamento", schema="operacional")
    op.drop_index("ix_pq_layout_cliente_cliente_id", table_name="pq_layout_cliente", schema="operacional")
    op.drop_table("pq_layout_cliente", schema="operacional")
    op.execute("DROP TYPE IF EXISTS campo_sistema_pq_enum")
