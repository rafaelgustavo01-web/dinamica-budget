revision = "024"
down_revision = "023"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID


def upgrade():
    # 1. Adicionar flag cpu_desatualizada em propostas
    op.add_column(
        "propostas",
        sa.Column("cpu_desatualizada", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        schema="operacional",
    )

    # 2. Tabelas espelho de bcu.* (8 tabelas) — schema operacional
    # ── proposta_pc_mao_obra ────────────────
    op.create_table(
        "proposta_pc_mao_obra",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("descricao_funcao", sa.String(255), nullable=False),
        sa.Column("codigo_origem", sa.String(40), nullable=True),
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
        sa.Column("valor_bcu_snapshot", sa.Numeric(15, 4), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_mao_obra"),
        schema="operacional",
    )

    # ── proposta_pc_equipamento_premissa ────────────────────────────────
    op.create_table(
        "proposta_pc_equipamento_premissa",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("horas_mes", sa.Numeric(10, 2), nullable=True),
        sa.Column("preco_gasolina_l", sa.Numeric(10, 4), nullable=True),
        sa.Column("preco_diesel_l", sa.Numeric(10, 4), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="operacional",
    )

    # ── proposta_pc_equipamento ─────────────────────────────────────────
    op.create_table(
        "proposta_pc_equipamento",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("codigo", sa.String(80), nullable=True),
        sa.Column("codigo_origem", sa.String(40), nullable=True),
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
        sa.Column("valor_bcu_snapshot", sa.Numeric(15, 4), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_equipamento"),
        schema="operacional",
    )

    # ── proposta_pc_encargo (cópia integral, não filtrado) ──────────────
    op.create_table(
        "proposta_pc_encargo",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("tipo_encargo", sa.String(20), nullable=False, index=True),
        sa.Column("grupo", sa.String(80), nullable=True),
        sa.Column("codigo_grupo", sa.String(255), nullable=True),
        sa.Column("discriminacao_encargo", sa.String(255), nullable=False),
        sa.Column("taxa_percent", sa.Numeric(10, 6), nullable=True),
        sa.Column("valor_bcu_snapshot", sa.Numeric(10, 6), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="operacional",
    )

    # ── proposta_pc_epi ──────────────────────────────────────────────────
    op.create_table(
        "proposta_pc_epi",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("codigo_origem", sa.String(40), nullable=True),
        sa.Column("epi", sa.String(255), nullable=False),
        sa.Column("unidade", sa.String(30), nullable=True),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=True),
        sa.Column("quantidade", sa.Numeric(12, 4), nullable=True),
        sa.Column("vida_util_meses", sa.Numeric(12, 4), nullable=True),
        sa.Column("custo_epi_mes", sa.Numeric(15, 4), nullable=True),
        sa.Column("valor_bcu_snapshot", sa.Numeric(15, 4), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_epi"),
        schema="operacional",
    )

    # ── proposta_pc_ferramenta ──────────────────────────────────────────
    op.create_table(
        "proposta_pc_ferramenta",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("codigo_origem", sa.String(40), nullable=True),
        sa.Column("item", sa.String(40), nullable=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("unidade", sa.String(30), nullable=True),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco", sa.Numeric(15, 4), nullable=True),
        sa.Column("preco_total", sa.Numeric(15, 4), nullable=True),
        sa.Column("valor_bcu_snapshot", sa.Numeric(15, 4), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_ferramenta"),
        schema="operacional",
    )

    # ── proposta_pc_mobilizacao (cópia integral) ────────────────────────
    op.create_table(
        "proposta_pc_mobilizacao",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("funcao", sa.String(120), nullable=True),
        sa.Column("tipo_mao_obra", sa.String(20), nullable=True),
        sa.Column("editado_manualmente", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="operacional",
    )
    op.create_table(
        "proposta_pc_mobilizacao_quantidade",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("mobilizacao_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.proposta_pc_mobilizacao.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("coluna_funcao", sa.String(50), nullable=False),
        sa.Column("quantidade", sa.Numeric(15, 4), nullable=True),
        schema="operacional",
    )

    # 3. Recursos extras (não-BCU)
    op.create_table(
        "proposta_recurso_extra",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("tipo_recurso", sa.String(20), nullable=False),  # MO, EQP, EPI, FER, INSUMO, SERVICO
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("unidade_medida", sa.String(30), nullable=True),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("criado_por_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.usuarios.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="operacional",
    )

    # 4. Alocação recurso extra ↔ composicao (junction)
    op.create_table(
        "proposta_recurso_alocacao",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("recurso_extra_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.proposta_recurso_extra.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("composicao_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.proposta_item_composicoes.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("quantidade_consumo", sa.Numeric(15, 6), nullable=False, server_default=sa.text("1")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("recurso_extra_id", "composicao_id", name="uq_recurso_alocacao"),
        schema="operacional",
    )


def downgrade():
    for tbl in [
        "proposta_recurso_alocacao",
        "proposta_recurso_extra",
        "proposta_pc_mobilizacao_quantidade",
        "proposta_pc_mobilizacao",
        "proposta_pc_ferramenta",
        "proposta_pc_epi",
        "proposta_pc_encargo",
        "proposta_pc_equipamento",
        "proposta_pc_equipamento_premissa",
        "proposta_pc_mao_obra",
    ]:
        op.execute(f"DROP TABLE IF EXISTS operacional.{tbl} CASCADE")
    op.drop_column("propostas", "cpu_desatualizada", schema="operacional")