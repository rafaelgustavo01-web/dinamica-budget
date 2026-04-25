"""Expand text lengths for PC encargo fields

Revision ID: 014
Revises: 013
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa


revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pc_encargo_item",
        "grupo",
        existing_type=sa.String(length=20),
        type_=sa.String(length=80),
        existing_nullable=True,
    )
    op.alter_column(
        "pc_encargo_item",
        "codigo_grupo",
        existing_type=sa.String(length=20),
        type_=sa.String(length=255),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "pc_encargo_item",
        "codigo_grupo",
        existing_type=sa.String(length=255),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
    op.alter_column(
        "pc_encargo_item",
        "grupo",
        existing_type=sa.String(length=80),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
