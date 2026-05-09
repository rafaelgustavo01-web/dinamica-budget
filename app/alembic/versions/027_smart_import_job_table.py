"""
smart_import_job_table

Revision ID: 027
Revises: 026
Create Date: 2026-05-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '027'
down_revision = '026'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create ENUM for SmartImportStatus
    smart_import_status_enum = postgresql.ENUM('PENDING', 'PROCESSING', 'REVIEW_REQUIRED', 'COMPLETED', 'FAILED', name='smart_import_status_enum')
    smart_import_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('smart_import_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('arquivo_origem', sa.String(length=260), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'REVIEW_REQUIRED', 'COMPLETED', 'FAILED', name='smart_import_status_enum', create_type=False), nullable=False),
        sa.Column('mapping_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('payload_staging', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['operacional.clientes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='operacional'
    )
    op.create_index(op.f('ix_operacional_smart_import_jobs_cliente_id'), 'smart_import_jobs', ['cliente_id'], unique=False, schema='operacional')


def downgrade() -> None:
    op.drop_index(op.f('ix_operacional_smart_import_jobs_cliente_id'), table_name='smart_import_jobs', schema='operacional')
    op.drop_table('smart_import_jobs', schema='operacional')
    
    smart_import_status_enum = postgresql.ENUM('PENDING', 'PROCESSING', 'REVIEW_REQUIRED', 'COMPLETED', 'FAILED', name='smart_import_status_enum')
    smart_import_status_enum.drop(op.get_bind(), checkfirst=True)
