"""Add BCU schema and deprecate pc_tabelas

Revision ID: 023
Revises: 022
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGEnum

# revision identifiers, used by Alembic.
revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop FK propostas.pc_cabecalho_id (se existe) e remove a coluna
    op.execute("ALTER TABLE operacional.propostas DROP COLUMN IF EXISTS pc_cabecalho_id CASCADE")
    op.execute("ALTER TABLE operacional.proposta_itens DROP COLUMN IF EXISTS pc_cabecalho_id CASCADE")

    # 2. Drop tabelas pc_* + etl_carga (schema public)
    for tbl in [
        "pc_mobilizacao_quantidade_funcao",
        "pc_mobilizacao_item",
        "pc_ferramenta_item",
        "pc_epi_distribuicao_funcao",
        "pc_epi_item",
        "pc_encargo_item",
        "pc_equipamento_item",
        "pc_equipamento_premissa",
        "pc_mao_obra_item",
        "pc_cabecalho",
        "etl_carga",
    ]:
        op.execute(f"DROP TABLE IF EXISTS public.{tbl} CASCADE")

    # 3. Create schema bcu
    op.execute("CREATE SCHEMA IF NOT EXISTS bcu")

    # 4. Create enum bcu_table_type
    op.execute("CREATE TYPE bcu_table_type_enum AS ENUM ('MO', 'EQP', 'EPI', 'FER', 'MOB')")

    # 5. Create bcu.cabecalho
    op.create_table(
        "cabecalho",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("nome_arquivo", sa.String(260), nullable=False),
        sa.Column("data_referencia", sa.Date(), nullable=True),
        sa.Column("versao_layout", sa.String(50), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("is_ativo", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_por_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.usuarios.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="bcu",
    )
    op.create_index("ix_bcu_cabecalho_ativo", "cabecalho", ["is_ativo"], schema="bcu",
                    postgresql_where=sa.text("is_ativo = TRUE"), unique=True)

    # 6. Create bcu.mao_obra_item
    op.create_table(
        "mao_obra_item",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("descricao_funcao", sa.String(255), nullable=False),
        sa.Column("codigo_origem", sa.String(40), nullable=True, index=True),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        sa.Column("salario", sa.Numeric(15, 4), nullable=True),
        sa.Column("previsao_reajuste", sa.Numeric(15, 4), nullable=True),
        sa.Column("encargos_percent", sa.Numeric(15, 6), nullable=True),
        sa.Column("periculosidade_insalubridade", sa.Numeric(15, 4), nullable=True),
        sa.Column("refeicao", sa.Numeric(15, 4), nullable=True),
        sa.Column("agua_potavel", sa.Numeric(15, 4), nullable=True),
        sa.Column("vale_alimentacao", sa.Numeric(15, 4), nullable=True),
        sa.Column("plano_saude", sa.Numeric(15, 4), nullable=True),
        sa.Column("ferramentas_val", sa.Numeric(15, 4), nullable=True),
        sa.Column("seguro_vida", sa.Numeric(15, 4), nullable=True),
        sa.Column("abono_ferias", sa.Numeric(15, 4), nullable=True),
        sa.Column("uniforme_val", sa.Numeric(15, 4), nullable=True),
        sa.Column("epi_val", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_unitario_h", sa.Numeric(15, 4), nullable=True),
        sa.Column("custo_mensal", sa.Numeric(15, 4), nullable=True),
        sa.Column("mobilizacao", sa.Numeric(15, 4), nullable=True),
        schema="bcu",
    )

    # 7. Create bcu.equipamento_premissa
    op.create_table(
        "equipamento_premissa",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("horas_mes", sa.Numeric(10, 2), nullable=True),
        sa.Column("preco_gasolina_l", sa.Numeric(10, 4), nullable=True),
        sa.Column("preco_diesel_l", sa.Numeric(10, 4), nullable=True),
        schema="bcu",
    )

    # 8. Create bcu.equipamento_item
    op.create_table(
        "equipamento_item",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("codigo", sa.String(80), nullable=True),
        sa.Column("codigo_origem", sa.String(40), nullable=True, index=True),
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
        schema="bcu",
    )

    # 9. Create bcu.encargo_item
    op.create_table(
        "encargo_item",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("tipo_encargo", sa.String(20), nullable=False, index=True),
        sa.Column("grupo", sa.String(80), nullable=True),
        sa.Column("codigo_grupo", sa.String(255), nullable=True),
        sa.Column("discriminacao_encargo", sa.String(255), nullable=False),
        sa.Column("taxa_percent", sa.Numeric(10, 6), nullable=True),
        schema="bcu",
    )

    # 10. Create bcu.epi_item
    op.create_table(
        "epi_item",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("codigo_origem", sa.String(40), nullable=True, index=True),
        sa.Column("epi", sa.String(255), nullable=False),
        sa.Column("unidade", sa.String(30), nullable=True),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        sa.Column("vida_util_meses", sa.Numeric(12, 4), nullable=True),
        sa.Column("custo_epi_mes", sa.Numeric(15, 4), nullable=True),
        schema="bcu",
    )

    # 11. Create bcu.epi_distribuicao_funcao
    op.create_table(
        "epi_distribuicao_funcao",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("epi_item_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.epi_item.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("funcao", sa.String(80), nullable=False),
        sa.Column("aplica_flag", sa.String(20), nullable=True),
        schema="bcu",
    )

    # 12. Create bcu.ferramenta_item
    op.create_table(
        "ferramenta_item",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("codigo_origem", sa.String(40), nullable=True, index=True),
        sa.Column("item", sa.String(40), nullable=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("unidade", sa.String(30), nullable=True),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco_total", sa.Numeric(15, 4), nullable=True),
        schema="bcu",
    )

    # 13. Create bcu.mobilizacao_item + quantidade_funcao
    op.create_table(
        "mobilizacao_item",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cabecalho_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("funcao", sa.String(120), nullable=True),
        sa.Column("tipo_mao_obra", sa.String(20), nullable=True),
        schema="bcu",
    )
    op.create_table(
        "mobilizacao_quantidade_funcao",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("mobilizacao_item_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("bcu.mobilizacao_item.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("coluna_funcao", sa.String(50), nullable=False),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
        schema="bcu",
    )

    # 14. Create bcu.de_para (mapeamento polimórfico TCPO ↔ BCU)
    op.create_table(
        "de_para",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("base_tcpo_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("referencia.base_tcpo.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bcu_table_type", PGEnum("MO", "EQP", "EPI", "FER", "MOB",
                                          name="bcu_table_type_enum", create_type=False),
                  nullable=False),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=False),
        sa.Column("criado_por_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.usuarios.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("base_tcpo_id", name="uq_de_para_base_tcpo"),
        sa.Index("ix_de_para_base_tcpo", "base_tcpo_id"),
        sa.Index("ix_de_para_bcu_item", "bcu_table_type", "bcu_item_id"),
        schema="bcu",
    )

    # 15. Add bcu_cabecalho_id em propostas
    op.add_column(
        "propostas",
        sa.Column("bcu_cabecalho_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.create_foreign_key(
        "fk_proposta_bcu_cabecalho",
        "propostas", "cabecalho",
        ["bcu_cabecalho_id"], ["id"],
        source_schema="operacional", referent_schema="bcu",
    )

    # 16. Add bcu_cabecalho_id em proposta_itens
    op.add_column(
        "proposta_itens",
        sa.Column("bcu_cabecalho_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.create_foreign_key(
        "fk_proposta_item_bcu_cabecalho",
        "proposta_itens", "cabecalho",
        ["bcu_cabecalho_id"], ["id"],
        source_schema="operacional", referent_schema="bcu",
    )


def downgrade() -> None:
    op.execute("ALTER TABLE operacional.proposta_itens DROP COLUMN IF EXISTS bcu_cabecalho_id CASCADE")
    op.execute("ALTER TABLE operacional.propostas DROP COLUMN IF EXISTS bcu_cabecalho_id CASCADE")
    op.execute("DROP SCHEMA IF EXISTS bcu CASCADE")
    op.execute("DROP TYPE IF EXISTS bcu_table_type_enum")
    # Não recriamos pc_* (drop irreversível por design — sprint reset)
