"""Add optional cliente fields for Folha PC."""

from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "029"
down_revision: Union[str, None] = "028"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


_TABLE = "clientes"
_SCHEMA = "operacional"
_COLUMNS = (
    sa.Column("razao_social", sa.String(length=255), nullable=True),
    sa.Column("inscricao_estadual", sa.String(length=30), nullable=True),
    sa.Column("inscricao_municipal", sa.String(length=30), nullable=True),
    sa.Column("endereco_logradouro", sa.String(length=255), nullable=True),
    sa.Column("endereco_numero", sa.String(length=30), nullable=True),
    sa.Column("endereco_complemento", sa.String(length=120), nullable=True),
    sa.Column("endereco_bairro", sa.String(length=120), nullable=True),
    sa.Column("endereco_municipio", sa.String(length=120), nullable=True),
    sa.Column("endereco_uf", sa.String(length=2), nullable=True),
    sa.Column("endereco_cep", sa.String(length=8), nullable=True),
    sa.Column("contato_nome", sa.String(length=120), nullable=True),
    sa.Column("contato_email", sa.String(length=255), nullable=True),
    sa.Column("contato_telefone", sa.String(length=30), nullable=True),
)


def upgrade() -> None:
    for column in _COLUMNS:
        op.add_column(_TABLE, column.copy(), schema=_SCHEMA)


def downgrade() -> None:
    for column in reversed(_COLUMNS):
        op.drop_column(_TABLE, column.name, schema=_SCHEMA)
