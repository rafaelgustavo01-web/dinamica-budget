"""Rename usuario_perfil to permissao_operacional

Revision ID: 010
Revises: 009
Create Date: 2026-03-28

Changes:
  - Rename table usuario_perfil → permissao_operacional
  - Rename associated constraint names to match new table
"""

from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("usuario_perfil", "permissao_operacional")

    # Rename primary key constraint so it reflects the new table name
    op.execute(
        """
        ALTER TABLE permissao_operacional
        RENAME CONSTRAINT usuario_perfil_pkey TO permissao_operacional_pkey;
        """
    )

    # Rename FK constraints that reference the old table name pattern
    # FK on usuario_id
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE permissao_operacional
            RENAME CONSTRAINT usuario_perfil_usuario_id_fkey
            TO permissao_operacional_usuario_id_fkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
        """
    )
    # FK on cliente_id
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE permissao_operacional
            RENAME CONSTRAINT usuario_perfil_cliente_id_fkey
            TO permissao_operacional_cliente_id_fkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE permissao_operacional
            RENAME CONSTRAINT permissao_operacional_pkey TO usuario_perfil_pkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE permissao_operacional
            RENAME CONSTRAINT permissao_operacional_usuario_id_fkey
            TO usuario_perfil_usuario_id_fkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            ALTER TABLE permissao_operacional
            RENAME CONSTRAINT permissao_operacional_cliente_id_fkey
            TO usuario_perfil_cliente_id_fkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
        """
    )
    op.rename_table("permissao_operacional", "usuario_perfil")
