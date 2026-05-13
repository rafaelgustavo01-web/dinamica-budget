"""expand numeric precision proposta_resumo_recursos

Revision ID: b1c2d3e4f5a6
Revises: 42558547f530
Create Date: 2026-05-13 22:25:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f5a6'
down_revision = '42558547f530'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col in ('total_direto', 'total_indireto', 'total_geral'):
        op.alter_column(
            'proposta_resumo_recursos',
            col,
            existing_type=sa.Numeric(15, 4),
            type_=sa.Numeric(20, 4),
            schema='operacional',
        )


def downgrade() -> None:
    for col in ('total_direto', 'total_indireto', 'total_geral'):
        op.alter_column(
            'proposta_resumo_recursos',
            col,
            existing_type=sa.Numeric(20, 4),
            type_=sa.Numeric(15, 4),
            schema='operacional',
        )
