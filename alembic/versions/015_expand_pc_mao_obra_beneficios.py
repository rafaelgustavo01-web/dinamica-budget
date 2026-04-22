"""Add benefit columns to pc_mao_obra_item

Revision ID: 015
Revises: 014
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pc_mao_obra_item", sa.Column("periculosidade_insalubridade", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("refeicao", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("agua_potavel", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("vale_alimentacao", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("plano_saude", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("ferramentas_val", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("seguro_vida", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("abono_ferias", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("uniforme_val", sa.Numeric(15, 4), nullable=True))
    op.add_column("pc_mao_obra_item", sa.Column("epi_val", sa.Numeric(15, 4), nullable=True))


def downgrade() -> None:
    op.drop_column("pc_mao_obra_item", "epi_val")
    op.drop_column("pc_mao_obra_item", "uniforme_val")
    op.drop_column("pc_mao_obra_item", "abono_ferias")
    op.drop_column("pc_mao_obra_item", "seguro_vida")
    op.drop_column("pc_mao_obra_item", "ferramentas_val")
    op.drop_column("pc_mao_obra_item", "plano_saude")
    op.drop_column("pc_mao_obra_item", "vale_alimentacao")
    op.drop_column("pc_mao_obra_item", "agua_potavel")
    op.drop_column("pc_mao_obra_item", "refeicao")
    op.drop_column("pc_mao_obra_item", "periculosidade_insalubridade")
