"""Create proposta entities for budgeting module

Revision ID: 017
Revises: 016
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

STATUS_PROPOSTA_ENUM = postgresql.ENUM(
    "RASCUNHO",
    "EM_ANALISE",
    "CPU_GERADA",
    "APROVADA",
    "REPROVADA",
    "ARQUIVADA",
    name="status_proposta_enum",
    create_type=False,
)
STATUS_IMPORTACAO_ENUM = postgresql.ENUM(
    "PROCESSANDO",
    "VALIDADO",
    "COM_ERROS",
    "CONCLUIDO",
    name="status_importacao_enum",
    create_type=False,
)
STATUS_MATCH_ENUM = postgresql.ENUM(
    "PENDENTE",
    "BUSCANDO",
    "SUGERIDO",
    "CONFIRMADO",
    "MANUAL",
    "SEM_MATCH",
    name="status_match_enum",
    create_type=False,
)
TIPO_SERVICO_MATCH_ENUM = postgresql.ENUM(
    "BASE_TCPO",
    "ITEM_PROPRIO",
    name="tipo_servico_match_enum",
    create_type=False,
)
TIPO_RECURSO_ENUM = postgresql.ENUM(
    "MO",
    "INSUMO",
    "FERRAMENTA",
    "EQUIPAMENTO",
    "SERVICO",
    name="tipo_recurso_enum",
    create_type=False,
)


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE status_proposta_enum AS ENUM (
                'RASCUNHO', 'EM_ANALISE', 'CPU_GERADA', 'APROVADA', 'REPROVADA', 'ARQUIVADA'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE status_importacao_enum AS ENUM (
                'PROCESSANDO', 'VALIDADO', 'COM_ERROS', 'CONCLUIDO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE status_match_enum AS ENUM (
                'PENDENTE', 'BUSCANDO', 'SUGERIDO', 'CONFIRMADO', 'MANUAL', 'SEM_MATCH'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tipo_servico_match_enum AS ENUM ('BASE_TCPO', 'ITEM_PROPRIO');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.create_table(
        "propostas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("criado_por_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column(
            "status",
            STATUS_PROPOSTA_ENUM,
            nullable=False,
            server_default="RASCUNHO",
        ),
        sa.Column("versao_cpu", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("total_direto", sa.Numeric(15, 4), nullable=True),
        sa.Column("total_indireto", sa.Numeric(15, 4), nullable=True),
        sa.Column("total_geral", sa.Numeric(15, 4), nullable=True),
        sa.Column("data_finalizacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cliente_id"], ["operacional.clientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["criado_por_id"], ["operacional.usuarios.id"]),
        sa.ForeignKeyConstraint(["pc_cabecalho_id"], ["pc_cabecalho.id"]),
        sa.UniqueConstraint("codigo", name="uq_propostas_codigo"),
        schema="operacional",
    )
    op.create_index("ix_propostas_cliente_id", "propostas", ["cliente_id"], schema="operacional")

    op.create_table(
        "pq_importacoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome_arquivo", sa.String(260), nullable=False),
        sa.Column("formato", sa.String(10), nullable=False),
        sa.Column("linhas_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("linhas_importadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("linhas_com_erro", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            STATUS_IMPORTACAO_ENUM,
            nullable=False,
            server_default="PROCESSANDO",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["proposta_id"], ["operacional.propostas.id"], ondelete="CASCADE"),
        schema="operacional",
    )
    op.create_index("ix_pq_importacoes_proposta_id", "pq_importacoes", ["proposta_id"], schema="operacional")

    op.create_table(
        "pq_itens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pq_importacao_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("codigo_original", sa.String(50), nullable=True),
        sa.Column("descricao_original", sa.Text(), nullable=False),
        sa.Column("unidade_medida_original", sa.String(20), nullable=True),
        sa.Column("quantidade_original", sa.Numeric(15, 4), nullable=True),
        sa.Column("descricao_tokens", sa.Text(), nullable=True),
        sa.Column(
            "match_status",
            STATUS_MATCH_ENUM,
            nullable=False,
            server_default="PENDENTE",
        ),
        sa.Column("match_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("servico_match_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "servico_match_tipo",
            TIPO_SERVICO_MATCH_ENUM,
            nullable=True,
        ),
        sa.Column("linha_planilha", sa.Integer(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["proposta_id"], ["operacional.propostas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pq_importacao_id"], ["operacional.pq_importacoes.id"], ondelete="SET NULL"),
        schema="operacional",
    )
    op.create_index("ix_pq_itens_proposta_id", "pq_itens", ["proposta_id"], schema="operacional")

    op.create_table(
        "proposta_itens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pq_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("servico_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "servico_tipo",
            TIPO_SERVICO_MATCH_ENUM,
            nullable=False,
        ),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=False, server_default="1"),
        sa.Column("custo_material_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_mao_obra_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_equipamento_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_direto_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("percentual_indireto", sa.Numeric(10, 6), nullable=True),
        sa.Column("custo_indireto_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco_total", sa.Numeric(15, 4), nullable=True),
        sa.Column("composicao_fonte", sa.String(50), nullable=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["proposta_id"], ["operacional.propostas.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pq_item_id"], ["operacional.pq_itens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["pc_cabecalho_id"], ["pc_cabecalho.id"]),
        schema="operacional",
    )
    op.create_index("ix_proposta_itens_proposta_id", "proposta_itens", ["proposta_id"], schema="operacional")

    op.create_table(
        "proposta_item_composicoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposta_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("insumo_base_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("insumo_proprio_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("descricao_insumo", sa.Text(), nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        sa.Column("quantidade_consumo", sa.Numeric(10, 4), nullable=False),
        sa.Column("custo_unitario_insumo", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_total_insumo", sa.Numeric(15, 4), nullable=True),
        sa.Column(
            "tipo_recurso",
            TIPO_RECURSO_ENUM,
            nullable=True,
        ),
        sa.Column("fonte_custo", sa.String(50), nullable=True),
        sa.CheckConstraint(
            "(insumo_base_id IS NOT NULL AND insumo_proprio_id IS NULL) OR "
            "(insumo_base_id IS NULL AND insumo_proprio_id IS NOT NULL)",
            name="ck_proposta_item_comp_exclusivo",
        ),
        sa.ForeignKeyConstraint(["proposta_item_id"], ["operacional.proposta_itens.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["insumo_base_id"], ["referencia.base_tcpo.id"]),
        sa.ForeignKeyConstraint(["insumo_proprio_id"], ["operacional.itens_proprios.id"]),
        schema="operacional",
    )
    op.create_index(
        "ix_proposta_item_comp_proposta_item_id",
        "proposta_item_composicoes",
        ["proposta_item_id"],
        schema="operacional",
    )


def downgrade() -> None:
    op.drop_index("ix_proposta_item_comp_proposta_item_id", table_name="proposta_item_composicoes", schema="operacional")
    op.drop_table("proposta_item_composicoes", schema="operacional")
    op.drop_index("ix_proposta_itens_proposta_id", table_name="proposta_itens", schema="operacional")
    op.drop_table("proposta_itens", schema="operacional")
    op.drop_index("ix_pq_itens_proposta_id", table_name="pq_itens", schema="operacional")
    op.drop_table("pq_itens", schema="operacional")
    op.drop_index("ix_pq_importacoes_proposta_id", table_name="pq_importacoes", schema="operacional")
    op.drop_table("pq_importacoes", schema="operacional")
    op.drop_index("ix_propostas_cliente_id", table_name="propostas", schema="operacional")
    op.drop_table("propostas", schema="operacional")

    op.execute("DROP TYPE IF EXISTS tipo_servico_match_enum")
    op.execute("DROP TYPE IF EXISTS status_match_enum")
    op.execute("DROP TYPE IF EXISTS status_importacao_enum")
    op.execute("DROP TYPE IF EXISTS status_proposta_enum")
