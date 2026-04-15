"""V2: Governance, RBAC, Audit Log and AssociacaoInteligente

Revision ID: 005
Revises: 004
Create Date: 2026-03-26

Changes:
  - servico_tcpo: add origem, status_homologacao, aprovado_por_id, data_aprovacao, cliente_id
  - Drop associacao_tcpo → create associacao_inteligente (frequencia_uso, status_validacao)
  - Create usuario_perfil (RBAC)
  - usuarios: add external_id_ad
  - Create auditoria_log
  - New enums: origem_item_enum, status_homologacao_enum,
               status_validacao_associacao_enum, tipo_operacao_auditoria_enum
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New enums ─────────────────────────────────────────────────────────────
    # PL/pgSQL DO blocks make creation idempotent. SQLAlchemy DDL event
    # listeners (fired when op.create_table is called) may race with the
    # explicit CREATE TYPE statements here when ORM models are imported via
    # env.py. The EXCEPTION clause absorbs the duplicate_object error cleanly.
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE origem_item_enum AS ENUM ('TCPO', 'PROPRIA');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE status_homologacao_enum AS ENUM ('PENDENTE', 'APROVADO', 'REPROVADO');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE status_validacao_associacao_enum AS ENUM ('SUGERIDA', 'VALIDADA', 'CONSOLIDADA');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tipo_operacao_auditoria_enum AS ENUM ('CREATE', 'UPDATE', 'DELETE');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── usuarios: add external_id_ad ─────────────────────────────────────────
    op.add_column(
        "usuarios",
        sa.Column("external_id_ad", sa.String(255), nullable=True),
    )
    op.create_index("ix_usuarios_external_id_ad", "usuarios", ["external_id_ad"], unique=True)

    # ── usuario_perfil (RBAC) ─────────────────────────────────────────────────
    op.create_table(
        "usuario_perfil",
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clientes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("perfil", sa.String(50), primary_key=True),
    )

    # ── servico_tcpo: governance columns ─────────────────────────────────────
    op.add_column(
        "servico_tcpo",
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clientes.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "servico_tcpo",
        sa.Column(
            "origem",
            sa.Enum("TCPO", "PROPRIA", name="origem_item_enum", create_type=False),
            nullable=False,
            server_default="TCPO",
        ),
    )
    op.add_column(
        "servico_tcpo",
        sa.Column(
            "status_homologacao",
            sa.Enum(
                "PENDENTE", "APROVADO", "REPROVADO",
                name="status_homologacao_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="APROVADO",
        ),
    )
    op.add_column(
        "servico_tcpo",
        sa.Column(
            "aprovado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "servico_tcpo",
        sa.Column("data_aprovacao", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_servico_tcpo_cliente_id", "servico_tcpo", ["cliente_id"])
    op.create_index("ix_servico_tcpo_status_hom", "servico_tcpo", ["status_homologacao"])

    # ── Drop old associacao_tcpo, create associacao_inteligente ──────────────
    op.drop_table("associacao_tcpo")
    op.execute("DROP TYPE IF EXISTS origem_associacao_enum")

    op.execute(
        "CREATE TYPE origem_associacao_enum AS ENUM ('MANUAL_USUARIO', 'IA_CONSOLIDADA')"
    )

    op.create_table(
        "associacao_inteligente",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clientes.id"),
            nullable=False,
        ),
        sa.Column("texto_busca_normalizado", sa.String(255), nullable=False),
        sa.Column(
            "servico_tcpo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("servico_tcpo.id"),
            nullable=False,
        ),
        sa.Column(
            "origem_associacao",
            # Use postgresql.ENUM (not sa.Enum) so create_type=False is preserved.
            # sa.Enum.adapt_emulated_to_native() only propagates create_type when
            # impl is already NativeForEmulated — sa.Enum is Emulated, so the flag
            # is silently dropped and the adapted ENUM gets create_type=True.
            postgresql.ENUM("MANUAL_USUARIO", "IA_CONSOLIDADA", name="origem_associacao_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("confiabilidade_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("frequencia_uso", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "status_validacao",
            postgresql.ENUM(
                "SUGERIDA", "VALIDADA", "CONSOLIDADA",
                name="status_validacao_associacao_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="SUGERIDA",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_assoc_inteligente_cliente", "associacao_inteligente", ["cliente_id"])
    op.create_index("ix_assoc_inteligente_servico", "associacao_inteligente", ["servico_tcpo_id"])
    op.create_index(
        "ix_assoc_inteligente_cliente_texto",
        "associacao_inteligente",
        ["cliente_id", "texto_busca_normalizado"],
    )

    # ── auditoria_log ─────────────────────────────────────────────────────────
    op.create_table(
        "auditoria_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tabela", sa.String(100), nullable=False),
        sa.Column("registro_id", sa.String(36), nullable=False),
        sa.Column(
            "operacao",
            postgresql.ENUM("CREATE", "UPDATE", "DELETE", name="tipo_operacao_auditoria_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("campo_alterado", sa.String(100), nullable=True),
        sa.Column("dados_anteriores", postgresql.JSONB, nullable=True),
        sa.Column("dados_novos", postgresql.JSONB, nullable=True),
        sa.Column("usuario_origem", sa.String(255), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auditoria_log_tabela", "auditoria_log", ["tabela"])
    op.create_index("ix_auditoria_log_registro", "auditoria_log", ["registro_id"])
    op.create_index("ix_auditoria_log_criado_em", "auditoria_log", ["criado_em"])


def downgrade() -> None:
    op.drop_table("auditoria_log")
    op.drop_table("associacao_inteligente")

    # Recreate associacao_tcpo
    op.create_table(
        "associacao_tcpo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clientes.id"), nullable=False),
        sa.Column("texto_busca_original", sa.String(255), nullable=False),
        sa.Column("servico_tcpo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("servico_tcpo.id"), nullable=False),
        sa.Column("origem_associacao", sa.String(50), nullable=False),
        sa.Column("confiabilidade_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.drop_index("ix_servico_tcpo_status_hom", "servico_tcpo")
    op.drop_index("ix_servico_tcpo_cliente_id", "servico_tcpo")
    op.drop_column("servico_tcpo", "data_aprovacao")
    op.drop_column("servico_tcpo", "aprovado_por_id")
    op.drop_column("servico_tcpo", "status_homologacao")
    op.drop_column("servico_tcpo", "origem")
    op.drop_column("servico_tcpo", "cliente_id")

    op.drop_table("usuario_perfil")
    op.drop_index("ix_usuarios_external_id_ad", "usuarios")
    op.drop_column("usuarios", "external_id_ad")

    op.execute("DROP TYPE IF EXISTS status_validacao_associacao_enum")
    op.execute("DROP TYPE IF EXISTS status_homologacao_enum")
    op.execute("DROP TYPE IF EXISTS origem_item_enum")
    op.execute("DROP TYPE IF EXISTS tipo_operacao_auditoria_enum")
