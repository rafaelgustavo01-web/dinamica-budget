"""Consolidation fixes V2

Revision ID: 006
Revises: 005
Create Date: 2026-03-26

Changes:
  - historico_busca_cliente: add usuario_id FK (replaces usuario_origem text)
  - auditoria_log: add usuario_id FK, add cliente_id FK
  - enums: rename PerfilUsuario.CRIADOR → USUARIO (stored as VARCHAR, no PG enum change)
  - enums: extend tipo_operacao_auditoria_enum with APROVAR, REPROVAR values
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── historico_busca_cliente: add usuario_id FK ────────────────────────────
    op.add_column(
        "historico_busca_cliente",
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,  # nullable for backward compat with existing rows
        ),
    )
    op.create_index(
        "ix_historico_busca_usuario_id",
        "historico_busca_cliente",
        ["usuario_id"],
    )

    # Drop legacy usuario_origem text column
    op.drop_column("historico_busca_cliente", "usuario_origem")

    # ── auditoria_log: add usuario_id and cliente_id FKs ─────────────────────
    op.add_column(
        "auditoria_log",
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "auditoria_log",
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clientes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_auditoria_log_usuario_id", "auditoria_log", ["usuario_id"])
    op.create_index("ix_auditoria_log_cliente_id", "auditoria_log", ["cliente_id"])

    # Drop legacy usuario_origem text column from auditoria_log
    op.drop_column("auditoria_log", "usuario_origem")

    # ── tipo_operacao_auditoria_enum: add APROVAR and REPROVAR values ─────────
    op.execute("ALTER TYPE tipo_operacao_auditoria_enum ADD VALUE IF NOT EXISTS 'APROVAR'")
    op.execute("ALTER TYPE tipo_operacao_auditoria_enum ADD VALUE IF NOT EXISTS 'REPROVAR'")

    # ── servico_tcpo: add index on origem for scoped queries ──────────────────
    op.create_index("ix_servico_tcpo_origem", "servico_tcpo", ["origem"])


def downgrade() -> None:
    op.drop_index("ix_servico_tcpo_origem", "servico_tcpo")

    # Re-add legacy columns before dropping new ones
    op.add_column(
        "auditoria_log",
        sa.Column("usuario_origem", sa.String(255), nullable=True),
    )
    op.drop_index("ix_auditoria_log_cliente_id", "auditoria_log")
    op.drop_index("ix_auditoria_log_usuario_id", "auditoria_log")
    op.drop_column("auditoria_log", "cliente_id")
    op.drop_column("auditoria_log", "usuario_id")

    op.add_column(
        "historico_busca_cliente",
        sa.Column("usuario_origem", sa.String(100), nullable=True),
    )
    op.drop_index("ix_historico_busca_usuario_id", "historico_busca_cliente")
    op.drop_column("historico_busca_cliente", "usuario_id")
