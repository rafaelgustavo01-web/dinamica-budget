"""Extend smart_import_jobs with pipeline metadata columns."""
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

_SCHEMA = "operacional"
_TABLE = "smart_import_jobs"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("proposta_id", PGUUID(as_uuid=True), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("detected_header_row", sa.Integer(), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("detected_data_range", JSONB(), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("row_classifications", JSONB(), nullable=True), schema=_SCHEMA)
    op.create_foreign_key(
        "fk_smart_import_jobs_proposta_id",
        _TABLE, "propostas",
        ["proposta_id"], ["id"],
        source_schema=_SCHEMA, referent_schema=_SCHEMA,
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_smart_import_jobs_proposta_id", _TABLE, schema=_SCHEMA, type_="foreignkey")
    op.drop_column(_TABLE, "row_classifications", schema=_SCHEMA)
    op.drop_column(_TABLE, "detected_data_range", schema=_SCHEMA)
    op.drop_column(_TABLE, "detected_header_row", schema=_SCHEMA)
    op.drop_column(_TABLE, "proposta_id", schema=_SCHEMA)
