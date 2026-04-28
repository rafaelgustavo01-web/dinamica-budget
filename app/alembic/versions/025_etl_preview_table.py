revision = "025"
down_revision = "024"

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID


def upgrade():
    """Create operacional.etl_preview — durable token store for ETL upload/execute flow."""
    op.create_table(
        "etl_preview",
        sa.Column("token", PGUUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("arquivo", sa.String(260), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        schema="operacional",
    )
    op.create_index(
        "ix_etl_preview_expira_em",
        "etl_preview",
        ["expira_em"],
        schema="operacional",
    )


def downgrade():
    op.drop_index("ix_etl_preview_expira_em", table_name="etl_preview", schema="operacional")
    op.drop_table("etl_preview", schema="operacional")
