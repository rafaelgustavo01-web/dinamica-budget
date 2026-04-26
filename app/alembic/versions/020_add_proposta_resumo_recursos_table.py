"""Add proposta_resumo_recursos table

Revision ID: 020
Revises: 019
Create Date: 2026-04-26 11:12:33.701045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '020'
down_revision: Union[str, None] = '019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get current type_recurso enum values or use a generic string for now if not using PG Enum in migration
    # The models use TipoRecurso defined in backend.models.enums
    
    op.create_table(
        'proposta_resumo_recursos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('proposta_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo_recurso', sa.String(50), nullable=False),
        sa.Column('total_direto', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0'),
        sa.Column('total_indireto', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0'),
        sa.Column('total_geral', sa.Numeric(precision=15, scale=4), nullable=False, server_default='0'),
        sa.Column('data_atualizacao', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['proposta_id'], ['operacional.propostas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('proposta_id', 'tipo_recurso', name='uq_proposta_recurso'),
        schema='operacional'
    )
    op.create_index(op.f('ix_operacional_proposta_resumo_recursos_proposta_id'), 'proposta_resumo_recursos', ['proposta_id'], unique=False, schema='operacional')


def downgrade() -> None:
    op.drop_index(op.f('ix_operacional_proposta_resumo_recursos_proposta_id'), table_name='proposta_resumo_recursos', schema='operacional')
    op.drop_table('proposta_resumo_recursos', schema='operacional')
