"""Add import_profile and import_profile_correction tables."""
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

_SCHEMA = "operacional"


def upgrade() -> None:
    op.create_table(
        "import_profile",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cliente_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("aba_pattern", sa.String(200), nullable=True),
        sa.Column("header_row_strategy", JSONB(), nullable=False,
                  server_default=sa.text('\'{"mode": "scan"}\'::jsonb')),
        sa.Column("column_aliases", JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("score_confianca", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("uso_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_aprovado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema=_SCHEMA,
    )

    correction_type_enum = sa.Enum(
        "COLUMN_REMAP", "HEADER_ROW_FIX", "ROW_RECLASSIFY", "SHEET_CHANGE",
        name="import_correction_type_enum",
    )
    correction_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "import_profile_correction",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.import_profile.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("job_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.smart_import_jobs.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("tipo", sa.Enum("COLUMN_REMAP", "HEADER_ROW_FIX", "ROW_RECLASSIFY", "SHEET_CHANGE",
                                  name="import_correction_type_enum", create_type=False), nullable=False),
        sa.Column("detalhe", JSONB(), nullable=True),
        sa.Column("aplicada", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema=_SCHEMA,
    )

    op.add_column("smart_import_jobs",
                  sa.Column("profile_id", PGUUID(as_uuid=True), nullable=True),
                  schema=_SCHEMA)
    op.create_foreign_key(
        "fk_smart_import_jobs_profile_id",
        "smart_import_jobs", "import_profile",
        ["profile_id"], ["id"],
        source_schema=_SCHEMA, referent_schema=_SCHEMA,
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_smart_import_jobs_profile_id", "smart_import_jobs",
                       schema=_SCHEMA, type_="foreignkey")
    op.drop_column("smart_import_jobs", "profile_id", schema=_SCHEMA)
    op.drop_table("import_profile_correction", schema=_SCHEMA)
    op.drop_table("import_profile", schema=_SCHEMA)
    sa.Enum(name="import_correction_type_enum").drop(op.get_bind(), checkfirst=True)
