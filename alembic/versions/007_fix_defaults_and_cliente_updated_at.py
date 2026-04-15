"""Fix status_homologacao default and add updated_at to clientes

Revision ID: 007
Revises: 006
Create Date: 2026-03-27

Changes:
  - servico_tcpo.status_homologacao: server_default APROVADO → PENDENTE (defense-in-depth)
  - clientes: add updated_at column with TimestampMixin consistency
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix server_default: APROVADO → PENDENTE for defense-in-depth
    op.alter_column(
        "servico_tcpo",
        "status_homologacao",
        server_default="PENDENTE",
    )

    # Add updated_at to clientes (BUG-05: missing TimestampMixin field)
    op.add_column(
        "clientes",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("clientes", "updated_at")

    op.alter_column(
        "servico_tcpo",
        "status_homologacao",
        server_default="APROVADO",
    )
