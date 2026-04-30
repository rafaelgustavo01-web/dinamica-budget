"""Add proposta_acl table with backfill

Revision ID: 021
Revises: 020
Create Date: 2026-04-26 11:42:26.514066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum
    proposta_papel_enum = postgresql.ENUM("OWNER", "EDITOR", "APROVADOR", name="proposta_papel_enum", create_type=True)
    proposta_papel_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "proposta_acl",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "papel",
            postgresql.ENUM("OWNER", "EDITOR", "APROVADOR", name="proposta_papel_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["proposta_id"], ["operacional.propostas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["operacional.usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["operacional.usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("proposta_id", "usuario_id", "papel", name="uq_proposta_acl"),
        schema="operacional",
    )
    op.create_index(op.f("ix_operacional_proposta_acl_proposta_id"), "proposta_acl", ["proposta_id"], unique=False, schema="operacional")
    op.create_index(op.f("ix_operacional_proposta_acl_usuario_id"), "proposta_acl", ["usuario_id"], unique=False, schema="operacional")

    # Backfill: criador de cada proposta vira OWNER
    op.execute(
        """
        INSERT INTO operacional.proposta_acl (id, proposta_id, usuario_id, papel, created_by, created_at, updated_at)
        SELECT gen_random_uuid(), id, criado_por_id, 'OWNER'::proposta_papel_enum, criado_por_id, NOW(), NOW()
        FROM operacional.propostas
        WHERE criado_por_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_operacional_proposta_acl_usuario_id"), table_name="proposta_acl", schema="operacional")
    op.drop_index(op.f("ix_operacional_proposta_acl_proposta_id"), table_name="proposta_acl", schema="operacional")
    op.drop_table("proposta_acl", schema="operacional")

    proposta_papel_enum = postgresql.ENUM("OWNER", "EDITOR", "APROVADOR", name="proposta_papel_enum", create_type=True)
    proposta_papel_enum.drop(op.get_bind(), checkfirst=True)
