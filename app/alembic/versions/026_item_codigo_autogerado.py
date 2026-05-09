revision = "026"
down_revision = "025"

import sqlalchemy as sa
from alembic import op


def upgrade():
    """
    Adiciona sequência para geração automática de código de itens próprios.
    A planilha passa apenas a descrição; o banco gera o identificador único.
    """
    # Sequência para itens_proprios — gera códigos únicos por cliente
    op.execute("CREATE SEQUENCE IF NOT EXISTS operacional.item_proprio_seq START 1 INCREMENT 1 CACHE 10")

    # Altera codigo_origem para ter server_default baseado na sequência
    # Mantém NOT NULL mas permite que o DB gere o valor
    op.execute(
        "ALTER TABLE operacional.itens_proprios "
        "ALTER COLUMN codigo_origem SET DEFAULT "
        "'PROP-' || LPAD(nextval('operacional.item_proprio_seq')::text, 6, '0')"
    )

    # Sequência para base_tcpo (itens sem código na planilha)
    op.execute("CREATE SEQUENCE IF NOT EXISTS referencia.tcpo_seq START 100000 INCREMENT 1 CACHE 10")
    op.execute(
        "ALTER TABLE referencia.base_tcpo "
        "ALTER COLUMN codigo_origem SET DEFAULT "
        "'TCPO-' || LPAD(nextval('referencia.tcpo_seq')::text, 6, '0')"
    )


def downgrade():
    op.execute("ALTER TABLE operacional.itens_proprios ALTER COLUMN codigo_origem DROP DEFAULT")
    op.execute("ALTER TABLE referencia.base_tcpo ALTER COLUMN codigo_origem DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS operacional.item_proprio_seq")
    op.execute("DROP SEQUENCE IF EXISTS referencia.tcpo_seq")
