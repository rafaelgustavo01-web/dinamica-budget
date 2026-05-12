"""Quantidade as INTEGER on proposta_pc_* and add quantidade to equipamento."""

from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "030"
down_revision: Union[str, None] = "029"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


_SCHEMA = "operacional"


def upgrade() -> None:
    # 1) Add quantidade column to equipamento (was missing)
    op.add_column(
        "proposta_pc_equipamento",
        sa.Column("quantidade", sa.Integer(), nullable=False, server_default="1"),
        schema=_SCHEMA,
    )

    # 2) Convert quantidade from NUMERIC to INTEGER on the other tables.
    #    USING round(...)::int handles existing fractional values.
    for table in ("proposta_pc_mao_obra", "proposta_pc_epi", "proposta_pc_ferramenta"):
        op.execute(
            f"""
            ALTER TABLE {_SCHEMA}.{table}
                ALTER COLUMN quantidade TYPE INTEGER
                USING COALESCE(ROUND(quantidade)::int, 1),
                ALTER COLUMN quantidade SET NOT NULL,
                ALTER COLUMN quantidade SET DEFAULT 1
            """
        )


def downgrade() -> None:
    for table in ("proposta_pc_mao_obra", "proposta_pc_epi", "proposta_pc_ferramenta"):
        op.execute(
            f"""
            ALTER TABLE {_SCHEMA}.{table}
                ALTER COLUMN quantidade DROP NOT NULL,
                ALTER COLUMN quantidade DROP DEFAULT,
                ALTER COLUMN quantidade TYPE NUMERIC(12,4) USING quantidade::numeric
            """
        )
    op.drop_column("proposta_pc_equipamento", "quantidade", schema=_SCHEMA)
