"""app config

Revision ID: 034_app_config
Revises: 033_import_profile_tables
Create Date: 2026-05-15
"""

from alembic import op
import sqlalchemy as sa

revision = "034_app_config"
down_revision = "033"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("app_config", sa.Column("key", sa.String(length=80), primary_key=True), sa.Column("value", sa.Text(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), schema="operacional")
    op.execute("insert into operacional.app_config (key, value) values ('proposal_number_pattern', 'PROP-{YYYY}-{seq:04d}') on conflict (key) do nothing")

def downgrade() -> None:
    op.drop_table("app_config", schema="operacional")
