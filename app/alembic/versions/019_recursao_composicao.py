"""Add recursive columns to proposta_item_composicoes

Revision ID: 019
Revises: 017
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "019"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("pai_composicao_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("nivel", sa.Integer(), nullable=False, server_default="0"),
        schema="operacional",
    )
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("e_composicao", sa.Boolean(), nullable=False, server_default="false"),
        schema="operacional",
    )
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("composicao_explodida", sa.Boolean(), nullable=False, server_default="false"),
        schema="operacional",
    )
    op.create_foreign_key(
        "fk_pic_pai_composicao_id",
        "proposta_item_composicoes",
        "proposta_item_composicoes",
        ["pai_composicao_id"],
        ["id"],
        source_schema="operacional",
        referent_schema="operacional",
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_pic_pai_composicao_id",
        "proposta_item_composicoes",
        ["pai_composicao_id"],
        schema="operacional",
    )


def downgrade() -> None:
    op.drop_index("ix_pic_pai_composicao_id", table_name="proposta_item_composicoes", schema="operacional")
    op.drop_constraint(
        "fk_pic_pai_composicao_id", "proposta_item_composicoes",
        schema="operacional", type_="foreignkey",
    )
    op.drop_column("proposta_item_composicoes", "composicao_explodida", schema="operacional")
    op.drop_column("proposta_item_composicoes", "e_composicao", schema="operacional")
    op.drop_column("proposta_item_composicoes", "nivel", schema="operacional")
    op.drop_column("proposta_item_composicoes", "pai_composicao_id", schema="operacional")
