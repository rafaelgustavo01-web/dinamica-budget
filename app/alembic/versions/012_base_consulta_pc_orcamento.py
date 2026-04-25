"""Add consulta/PC/orcamento tables and ETL control

Revision ID: 012a
Revises: 012
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "012a"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "etl_carga",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fonte_arquivo", sa.String(260), nullable=False),
        sa.Column("tipo_fonte", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="EM_PROCESSAMENTO"),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finalizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("linhas_lidas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("linhas_carregadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mensagem", sa.Text(), nullable=True),
    )
    op.create_index("ix_etl_carga_tipo_fonte", "etl_carga", ["tipo_fonte"])
    op.create_index("ix_etl_carga_status", "etl_carga", ["status"])

    op.create_table(
        "pc_cabecalho",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("etl_carga_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("etl_carga.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nome_arquivo", sa.String(260), nullable=False),
        sa.Column("data_referencia", sa.Date(), nullable=True),
        sa.Column("versao_layout", sa.String(50), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_pc_cabecalho_criado_em", "pc_cabecalho", ["criado_em"])

    op.create_table(
        "pc_mao_obra_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("descricao_funcao", sa.String(255), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        sa.Column("salario", sa.Numeric(15, 4), nullable=True),
        sa.Column("previsao_reajuste", sa.Numeric(15, 4), nullable=True),
        sa.Column("encargos_percent", sa.Numeric(10, 6), nullable=True),
        sa.Column("custo_unitario_h", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_mensal", sa.Numeric(15, 4), nullable=True),
        sa.Column("mobilizacao", sa.Numeric(15, 4), nullable=True),
    )
    op.create_index("ix_pc_mao_obra_item_pc", "pc_mao_obra_item", ["pc_cabecalho_id"])

    op.create_table(
        "pc_equipamento_premissa",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("horas_mes", sa.Numeric(10, 2), nullable=True),
        sa.Column("preco_gasolina_l", sa.Numeric(10, 4), nullable=True),
        sa.Column("preco_diesel_l", sa.Numeric(10, 4), nullable=True),
    )
    op.create_index("ix_pc_equipamento_premissa_pc", "pc_equipamento_premissa", ["pc_cabecalho_id"])

    op.create_table(
        "pc_equipamento_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("codigo", sa.String(80), nullable=True),
        sa.Column("equipamento", sa.String(255), nullable=False),
        sa.Column("combustivel_utilizado", sa.String(60), nullable=True),
        sa.Column("consumo_l_h", sa.Numeric(15, 6), nullable=True),
        sa.Column("aluguel_r_h", sa.Numeric(15, 4), nullable=True),
        sa.Column("combustivel_r_h", sa.Numeric(15, 4), nullable=True),
        sa.Column("mao_obra_r_h", sa.Numeric(15, 4), nullable=True),
        sa.Column("hora_produtiva", sa.Numeric(15, 4), nullable=True),
        sa.Column("hora_improdutiva", sa.Numeric(15, 4), nullable=True),
        sa.Column("mes", sa.Numeric(15, 4), nullable=True),
        sa.Column("aluguel_mensal", sa.Numeric(15, 4), nullable=True),
    )
    op.create_index("ix_pc_equipamento_item_pc", "pc_equipamento_item", ["pc_cabecalho_id"])

    op.create_table(
        "pc_encargo_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo_encargo", sa.String(20), nullable=False),
        sa.Column("grupo", sa.String(20), nullable=True),
        sa.Column("codigo_grupo", sa.String(20), nullable=True),
        sa.Column("discriminacao_encargo", sa.String(255), nullable=False),
        sa.Column("taxa_percent", sa.Numeric(10, 6), nullable=True),
    )
    op.create_index("ix_pc_encargo_item_pc", "pc_encargo_item", ["pc_cabecalho_id"])
    op.create_index("ix_pc_encargo_item_tipo", "pc_encargo_item", ["tipo_encargo"])

    op.create_table(
        "pc_epi_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("epi", sa.String(255), nullable=False),
        sa.Column("unidade", sa.String(30), nullable=True),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        sa.Column("vida_util_meses", sa.Numeric(12, 4), nullable=True),
        sa.Column("custo_epi_mes", sa.Numeric(15, 4), nullable=True),
    )
    op.create_index("ix_pc_epi_item_pc", "pc_epi_item", ["pc_cabecalho_id"])

    op.create_table(
        "pc_epi_distribuicao_funcao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_epi_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_epi_item.id", ondelete="CASCADE"), nullable=False),
        sa.Column("funcao", sa.String(80), nullable=False),
        sa.Column("aplica_flag", sa.String(20), nullable=True),
    )
    op.create_index("ix_pc_epi_distribuicao_item", "pc_epi_distribuicao_funcao", ["pc_epi_item_id"])

    op.create_table(
        "pc_ferramenta_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item", sa.String(40), nullable=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("unidade", sa.String(30), nullable=True),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco_total", sa.Numeric(15, 4), nullable=True),
    )
    op.create_index("ix_pc_ferramenta_item_pc", "pc_ferramenta_item", ["pc_cabecalho_id"])

    op.create_table(
        "pc_mobilizacao_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("funcao", sa.String(120), nullable=True),
        sa.Column("tipo_mao_obra", sa.String(20), nullable=True),
    )
    op.create_index("ix_pc_mobilizacao_item_pc", "pc_mobilizacao_item", ["pc_cabecalho_id"])

    op.create_table(
        "pc_mobilizacao_quantidade_funcao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_mobilizacao_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_mobilizacao_item.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coluna_funcao", sa.String(50), nullable=False),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
    )
    op.create_index(
        "ix_pc_mobilizacao_quantidade_item",
        "pc_mobilizacao_quantidade_funcao",
        ["pc_mobilizacao_item_id"],
    )

    op.create_table(
        "pc_item_vinculo_tcpo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pc_cabecalho_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False),
        sa.Column("origem_tabela", sa.String(60), nullable=False),
        sa.Column("origem_registro_ref", sa.String(80), nullable=False),
        sa.Column(
            "servico_tcpo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo_vinculo", sa.String(30), nullable=False, server_default="AUTO"),
        sa.Column("confianca", sa.Numeric(5, 4), nullable=False, server_default="1"),
    )
    op.create_index("ix_pc_item_vinculo_pc", "pc_item_vinculo_tcpo", ["pc_cabecalho_id"])
    op.create_index("ix_pc_item_vinculo_tcpo", "pc_item_vinculo_tcpo", ["servico_tcpo_id"])
    op.create_unique_constraint(
        "uq_pc_item_vinculo_origem",
        "pc_item_vinculo_tcpo",
        ["pc_cabecalho_id", "origem_tabela", "origem_registro_ref"],
    )

    op.create_table(
        "orcamento",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.clientes.id"),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="EM_ELABORACAO"),
        sa.Column("base_pc_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pc_cabecalho.id", ondelete="SET NULL"), nullable=True),
        sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_orcamento_cliente_id", "orcamento", ["cliente_id"])
    op.create_index("ix_orcamento_status", "orcamento", ["status"])
    op.create_unique_constraint("uq_orcamento_cliente_codigo", "orcamento", ["cliente_id", "codigo"])

    op.create_table(
        "orcamento_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("orcamento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orcamento.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "servico_tcpo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("codigo_origem", sa.String(80), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=True),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=False, server_default="1"),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("custo_total", sa.Numeric(15, 4), nullable=False, server_default="0"),
        sa.Column("origem_item", sa.String(30), nullable=False, server_default="TCPO"),
    )
    op.create_index("ix_orcamento_item_orcamento", "orcamento_item", ["orcamento_id"])
    op.create_index("ix_orcamento_item_servico", "orcamento_item", ["servico_tcpo_id"])

    op.create_table(
        "orcamento_item_composicao",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("orcamento_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orcamento_item.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "servico_pai_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "insumo_filho_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("descricao_insumo", sa.Text(), nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=True),
        sa.Column("quantidade_consumo", sa.Numeric(15, 6), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_total", sa.Numeric(15, 4), nullable=True),
        sa.Column("fonte", sa.String(30), nullable=False, server_default="SNAPSHOT"),
    )
    op.create_index("ix_orc_item_comp_orc_item", "orcamento_item_composicao", ["orcamento_item_id"])


def downgrade() -> None:
    op.drop_index("ix_orc_item_comp_orc_item", table_name="orcamento_item_composicao")
    op.drop_table("orcamento_item_composicao")

    op.drop_index("ix_orcamento_item_servico", table_name="orcamento_item")
    op.drop_index("ix_orcamento_item_orcamento", table_name="orcamento_item")
    op.drop_table("orcamento_item")

    op.drop_constraint("uq_orcamento_cliente_codigo", "orcamento", type_="unique")
    op.drop_index("ix_orcamento_status", table_name="orcamento")
    op.drop_index("ix_orcamento_cliente_id", table_name="orcamento")
    op.drop_table("orcamento")

    op.drop_constraint("uq_pc_item_vinculo_origem", "pc_item_vinculo_tcpo", type_="unique")
    op.drop_index("ix_pc_item_vinculo_tcpo", table_name="pc_item_vinculo_tcpo")
    op.drop_index("ix_pc_item_vinculo_pc", table_name="pc_item_vinculo_tcpo")
    op.drop_table("pc_item_vinculo_tcpo")

    op.drop_index("ix_pc_mobilizacao_quantidade_item", table_name="pc_mobilizacao_quantidade_funcao")
    op.drop_table("pc_mobilizacao_quantidade_funcao")

    op.drop_index("ix_pc_mobilizacao_item_pc", table_name="pc_mobilizacao_item")
    op.drop_table("pc_mobilizacao_item")

    op.drop_index("ix_pc_ferramenta_item_pc", table_name="pc_ferramenta_item")
    op.drop_table("pc_ferramenta_item")

    op.drop_index("ix_pc_epi_distribuicao_item", table_name="pc_epi_distribuicao_funcao")
    op.drop_table("pc_epi_distribuicao_funcao")

    op.drop_index("ix_pc_epi_item_pc", table_name="pc_epi_item")
    op.drop_table("pc_epi_item")

    op.drop_index("ix_pc_encargo_item_tipo", table_name="pc_encargo_item")
    op.drop_index("ix_pc_encargo_item_pc", table_name="pc_encargo_item")
    op.drop_table("pc_encargo_item")

    op.drop_index("ix_pc_equipamento_item_pc", table_name="pc_equipamento_item")
    op.drop_table("pc_equipamento_item")

    op.drop_index("ix_pc_equipamento_premissa_pc", table_name="pc_equipamento_premissa")
    op.drop_table("pc_equipamento_premissa")

    op.drop_index("ix_pc_mao_obra_item_pc", table_name="pc_mao_obra_item")
    op.drop_table("pc_mao_obra_item")

    op.drop_index("ix_pc_cabecalho_criado_em", table_name="pc_cabecalho")
    op.drop_table("pc_cabecalho")

    op.drop_index("ix_etl_carga_status", table_name="etl_carga")
    op.drop_index("ix_etl_carga_tipo_fonte", table_name="etl_carga")
    op.drop_table("etl_carga")
