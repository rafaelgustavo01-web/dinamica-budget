"""Remove quantidade columns from BCU base tables (MO, EPI, Ferramentas).

Base tables define unit costs — quantities belong to the proposal/composition layer.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "031"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

_SCHEMA = "bcu"


def upgrade() -> None:
    op.drop_column("mao_obra_item", "quantidade", schema=_SCHEMA)
    op.drop_column("epi_item", "quantidade", schema=_SCHEMA)
    op.drop_column("ferramenta_item", "quantidade", schema=_SCHEMA)


def downgrade() -> None:
    op.add_column(
        "mao_obra_item",
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        schema=_SCHEMA,
    )
    op.add_column(
        "epi_item",
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        schema=_SCHEMA,
    )
    op.add_column(
        "ferramenta_item",
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
        schema=_SCHEMA,
    )
