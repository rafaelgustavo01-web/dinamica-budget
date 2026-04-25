"""Expand numeric ranges for PC ETL fields

Revision ID: 013
Revises: 012a
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa


revision = "013"
down_revision = "012a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pc_mao_obra_item",
        "encargos_percent",
        existing_type=sa.Numeric(10, 6),
        type_=sa.Numeric(15, 6),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "pc_mao_obra_item",
        "encargos_percent",
        existing_type=sa.Numeric(15, 6),
        type_=sa.Numeric(10, 6),
        existing_nullable=True,
    )
