"""Create versao_composicao and add versao_id/unidade_medida to composicao_tcpo

Revision ID: 009
Revises: 008
Create Date: 2026-03-28

Changes:
  - CREATE TABLE versao_composicao (id, servico_id, numero_versao, origem,
      cliente_id, is_ativa, criado_por_id, criado_em)
  - composicao_tcpo: add versao_id (FK → versao_composicao.id) NOT NULL
  - composicao_tcpo: add unidade_medida VARCHAR(20) NOT NULL
  - Data migration: populate versao_composicao from existing composicao_tcpo
      rows, then set versao_id and unidade_medida
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create versao_composicao table
    op.create_table(
        "versao_composicao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "servico_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("servico_tcpo.id"),
            nullable=False,
        ),
        sa.Column("numero_versao", sa.Integer, nullable=False),
        sa.Column(
            "origem",
            postgresql.ENUM(
                "TCPO", "PROPRIA",
                name="origem_item_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clientes.id"),
            nullable=True,
        ),
        sa.Column("is_ativa", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "criado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "servico_id", "numero_versao",
            name="uq_versao_composicao_servico_numero",
        ),
    )
    op.create_index(
        "ix_versao_composicao_servico_id", "versao_composicao", ["servico_id"]
    )
    op.create_index(
        "ix_versao_composicao_cliente_id", "versao_composicao", ["cliente_id"]
    )

    # 2. Add versao_id (nullable for now — set NOT NULL after data migration)
    op.add_column(
        "composicao_tcpo",
        sa.Column(
            "versao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("versao_composicao.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_composicao_tcpo_versao_id", "composicao_tcpo", ["versao_id"]
    )

    # 3. Add unidade_medida (nullable for now)
    op.add_column(
        "composicao_tcpo",
        sa.Column("unidade_medida", sa.String(20), nullable=True),
    )

    # 4. Data migration — create one versao_composicao per distinct servico_pai_id
    op.execute(
        """
        INSERT INTO versao_composicao
            (id, servico_id, numero_versao, origem, cliente_id, is_ativa, criado_em)
        SELECT
            gen_random_uuid(),
            c.servico_pai_id,
            1,
            s.origem,
            s.cliente_id,
            TRUE,
            now()
        FROM (
            SELECT DISTINCT servico_pai_id FROM composicao_tcpo
        ) c
        JOIN servico_tcpo s ON s.id = c.servico_pai_id;
        """
    )

    # 5. Set versao_id on composicao_tcpo rows
    op.execute(
        """
        UPDATE composicao_tcpo c
        SET versao_id = v.id
        FROM versao_composicao v
        WHERE v.servico_id = c.servico_pai_id;
        """
    )

    # 6. Set unidade_medida from the insumo_filho's unidade_medida
    op.execute(
        """
        UPDATE composicao_tcpo c
        SET unidade_medida = s.unidade_medida
        FROM servico_tcpo s
        WHERE s.id = c.insumo_filho_id;
        """
    )

    # 7. Now make versao_id and unidade_medida NOT NULL
    op.alter_column("composicao_tcpo", "versao_id", nullable=False)
    op.alter_column("composicao_tcpo", "unidade_medida", nullable=False)


def downgrade() -> None:
    op.alter_column("composicao_tcpo", "unidade_medida", nullable=True)
    op.alter_column("composicao_tcpo", "versao_id", nullable=True)

    op.execute("UPDATE composicao_tcpo SET versao_id = NULL;")
    op.execute("UPDATE composicao_tcpo SET unidade_medida = NULL;")

    op.drop_index("ix_composicao_tcpo_versao_id", "composicao_tcpo")
    op.drop_column("composicao_tcpo", "unidade_medida")
    op.drop_column("composicao_tcpo", "versao_id")

    op.drop_index("ix_versao_composicao_cliente_id", "versao_composicao")
    op.drop_index("ix_versao_composicao_servico_id", "versao_composicao")
    op.drop_table("versao_composicao")
