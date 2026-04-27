# F2-11: Histograma da Proposta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o **Histograma da Proposta** — snapshot editável e per-proposta da BCU, gerado a partir da sumarização das composições, com suporte a recursos extras alocáveis e detecção automática de divergência com a base global. Estabelece o fluxo PQ → Match → **Montar Histograma** → CPU como pipeline canônico, separando custos globais (BCU) de custos contratuais da proposta.

**Architecture:**
- Migration 024: tabelas `operacional.proposta_pc_*` (espelham `bcu.*` + `proposta_id` FK + `bcu_item_id` snapshot ref + `valor_bcu_snapshot` + `editado_manualmente`); `operacional.proposta_recurso_extra` (recursos livres); `operacional.proposta_recurso_alocacao` (junction recurso_extra ↔ composicao).
- `histograma_service.montar_histograma(proposta_id)`: explode `PropostaItemComposicao`, agrupa unique `(insumo_id, tipo_recurso)`, lookup via `bcu_de_para`, copia valores BCU para `proposta_pc_*` com `valor_bcu_snapshot` (snapshot congelado). Encargos e Mobilização vão **integralmente** (cópia completa do BCU ativo), sem filtro.
- Sincronização: query compara `proposta_pc_*.valor_bcu_snapshot` com `bcu.*.valor_atual` via JOIN por `bcu_item_id`; expõe lista de divergências no GET histograma.
- Recursos extras: itens livres (`descricao`, `unidade`, `custo_unitario`) que o usuário cria sem estar em BCU. Para impactar CPU, devem ser explicitamente alocados a uma `PropostaItemComposicao` via tabela `proposta_recurso_alocacao` (com `quantidade_consumo`).
- Trigger "CPU desatualizada": qualquer mutação em `proposta_pc_*`, `proposta_recurso_extra`, `proposta_recurso_alocacao` seta `proposta.cpu_desatualizada=TRUE`.
- Versionamento (F2-09): `nova_versao` clona histograma + recursos extras + alocações. Novo método em `proposta_versionamento_service`.
- `cpu_custo_service` (já refatorado em F2-10): adiciona resolução prioritária via `proposta_pc_*` (snapshot da proposta) com fallback para `bcu.*` (global). Soma adicional de recursos extras alocados.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Pré-requisito de leitura (obrigatório antes de codar)

**Leia na ordem antes de começar:**

1. `docs/shared/governance/BACKLOG.md` — sprint F2-11 (escopo + critérios de aceite)
2. `docs/sprints/F2-10/technical-review/technical-review-2026-04-XX-f2-10.md` — o que F2-10 entregou (BCU + De/Para)
3. `app/backend/models/bcu.py` — schema BCU global (referência para snapshot)
4. `app/backend/models/proposta.py` — `Proposta`, `PropostaItem`, `PropostaItemComposicao`, `bcu_cabecalho_id`
5. `app/backend/services/cpu_custo_service.py` — lookup atual via De/Para (a estender com proposta_pc_*)
6. `app/backend/services/cpu_geracao_service.py` — fluxo gerar_cpu_para_proposta (chamar histograma antes)
7. `app/backend/services/cpu_explosao_service.py` — explosão de composições
8. `app/backend/services/proposta_versionamento_service.py` — `nova_versao` (estender para clonar histograma)
9. `app/backend/services/bcu_de_para_service.py` — lookup BCU para BaseTcpo
10. `app/alembic/versions/023_bcu_unificada.py` — padrão de migration mais recente
11. `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` — onde entra botão "Montar Histograma"
12. `app/frontend/src/features/bcu/BcuPage.tsx` — referência visual para BcuHistogramaPage (mesmo layout de abas)

**Decisões já tomadas (não rediscutir):**
- Trigger explícito: botão **"Montar Histograma"** no `ProposalDetailPage` (não automático após match)
- Snapshot **sincronizado com aviso** (não congelado): mantém vínculo via `bcu_item_id` + grava `valor_bcu_snapshot` no momento da geração; UI compara em tempo real e exibe badge quando há divergência
- **Item livre (recurso extra):** dois passos — (1) criar recurso extra na proposta (sem impacto na CPU); (2) alocar a uma composição específica com `quantidade_consumo` para que entre no cálculo
- **Versionamento clona** histograma + recursos extras + alocações na nova versão
- Edição em `proposta_pc_*` ou em recursos extras/alocações marca **`proposta.cpu_desatualizada=TRUE`** — usuário precisa clicar "Recalcular CPU" para refletir
- **Encargos e Mobilização** vão integralmente para o histograma (cópia completa do BCU ativo), não filtrados pela composição
- **MO/EQP/EPI/FER** são filtrados: só entram itens cujo TCPO está presente nas composições da proposta E está mapeado em De/Para (`bcu_de_para`)
- Itens TCPO sem mapeamento em De/Para entram com warning "Sem vínculo BCU" e usam `BaseTcpo.custo_base` como valor padrão; usuário pode editar manualmente
- Permissões: papel **EDITOR ou OWNER** monta/edita histograma; **VIEWER e APROVADOR** apenas leem

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/alembic/versions/024_proposta_histograma.py` | Criar | 8 tabelas `operacional.proposta_pc_*` + `proposta_recurso_extra` + `proposta_recurso_alocacao` + flag `propostas.cpu_desatualizada` |
| `app/backend/models/proposta_pc.py` | Criar | Models snapshot (espelham bcu.* + proposta_id + bcu_item_id + valor_bcu_snapshot + editado_manualmente) |
| `app/backend/models/proposta_recurso_extra.py` | Criar | Models recurso extra + alocação |
| `app/backend/models/proposta.py` | Modificar | Adicionar `cpu_desatualizada: bool` em `Proposta` |
| `app/backend/repositories/proposta_pc_repository.py` | Criar | CRUD per-proposta dos 8 tipos |
| `app/backend/repositories/proposta_recurso_extra_repository.py` | Criar | CRUD recurso extra + alocação |
| `app/backend/services/histograma_service.py` | Criar | `montar_histograma`, `get_histograma`, `editar_item`, `detectar_divergencias` |
| `app/backend/services/proposta_recurso_extra_service.py` | Criar | CRUD recurso extra + alocação + trigger cpu_desatualizada |
| `app/backend/services/cpu_custo_service.py` | Modificar | Lookup prioritário em `proposta_pc_*`; soma de alocações de recurso_extra |
| `app/backend/services/cpu_geracao_service.py` | Modificar | Setar `cpu_desatualizada=FALSE` ao final de `gerar_cpu_para_proposta` |
| `app/backend/services/proposta_versionamento_service.py` | Modificar | `nova_versao`: clonar histograma + recursos extras + alocações |
| `app/backend/api/v1/endpoints/propostas.py` | Modificar | 8 endpoints novos: `POST /montar-histograma`, `GET /histograma`, `PATCH /histograma/{tabela}/{id}`, `POST /aceitar-bcu/{tabela}/{id}`, `POST /recursos-extras`, `PATCH /recursos-extras/{id}`, `DELETE /recursos-extras/{id}`, `POST /composicoes/{id}/alocar-recurso` |
| `app/backend/schemas/proposta_pc.py` | Criar | Pydantic schemas para histograma + recursos extras + alocação |
| `app/backend/tests/unit/test_histograma_service.py` | Criar | 12+ testes do service |
| `app/backend/tests/unit/test_proposta_recurso_extra_service.py` | Criar | 8+ testes |
| `app/backend/tests/unit/test_histograma_endpoints.py` | Criar | 10+ testes endpoints |
| `app/backend/tests/unit/test_cpu_custo_service.py` | Modificar | Adicionar testes de prioridade proposta_pc > bcu + soma recursos extras |
| `app/backend/tests/unit/test_proposta_versionamento_service.py` | Modificar | Adicionar testes de clonagem de histograma |
| `app/frontend/src/shared/services/api/histogramaApi.ts` | Criar | API client histograma + recursos extras + alocação |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | Campo `cpu_desatualizada` em `PropostaResponse` |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificar | Botão "Montar Histograma" + badge CPU desatualizada |
| `app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx` | Criar | Tela principal: 7 abas (MO, EQP, ENC-Horista, ENC-Mens, EPI, FER, MOB) + aba Recursos Extras |
| `app/frontend/src/features/proposals/components/HistogramaTabMaoObra.tsx` | Criar | Aba MO com edição inline |
| `app/frontend/src/features/proposals/components/HistogramaTabGenerica.tsx` | Criar | Componente reutilizável para EQP/EPI/FER (tabela editável + sync badge) |
| `app/frontend/src/features/proposals/components/RecursosExtrasTab.tsx` | Criar | Aba recursos extras: criar/editar/deletar |
| `app/frontend/src/features/proposals/components/AlocacaoRecursoDialog.tsx` | Criar | Dialog para alocar recurso extra a composição |
| `app/frontend/src/features/proposals/components/CpuTable.tsx` | Modificar | Mostrar recursos extras alocados + botão "Alocar recurso extra" por composição |
| `app/frontend/src/features/proposals/routes.tsx` | Modificar | Rota `/propostas/:id/histograma` |

---

## Task 1: Backend — migration 024 + models

**Files:**
- Create: `app/alembic/versions/024_proposta_histograma.py`
- Create: `app/backend/models/proposta_pc.py`
- Create: `app/backend/models/proposta_recurso_extra.py`
- Modify: `app/backend/models/proposta.py`

### Step 1: Migration 024

```python
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
    # Padrão comum: id, proposta_id (FK + index), bcu_item_id (UUID, sem FK pois bcu pode ser deletado),
    # valor_bcu_snapshot (Numeric — valor congelado no momento da geração),
    # editado_manualmente (bool default FALSE), criado_em, atualizado_em.

    # ── proposta_pc_mao_obra (espelha bcu.mao_obra_item) ────────────────
    op.create_table(
        "proposta_pc_mao_obra",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposta_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=True),  # nullable: pode ser recurso extra promovido
        sa.Column("descricao_funcao", sa.String(255), nullable=False),
        sa.Column("codigo_origem", sa.String(40), nullable=True),
        # Espelho dos campos de bcu.mao_obra_item (todos editáveis):
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
        # Snapshot + edição:
        sa.Column("valor_bcu_snapshot", sa.Numeric(15, 4), nullable=True),  # custo_unitario_h no momento do snapshot
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
        sa.Column("valor_bcu_snapshot", sa.Numeric(15, 4), nullable=True),  # aluguel_r_h no snapshot
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
        sa.Column("valor_bcu_snapshot", sa.Numeric(10, 6), nullable=True),  # taxa_percent
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
                  sa.ForeignKey("operacional.proposta_item_composicao.id", ondelete="CASCADE"),
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
```

### Step 2: Models

`app/backend/models/proposta_pc.py`: 8 classes (`PropostaPcMaoObra`, `PropostaPcEquipamentoPremissa`, `PropostaPcEquipamento`, `PropostaPcEncargo`, `PropostaPcEpi`, `PropostaPcFerramenta`, `PropostaPcMobilizacao`, `PropostaPcMobilizacaoQuantidade`) — espelham `bcu.*` mas com `proposta_id`, `bcu_item_id` (sem FK física), `valor_bcu_snapshot`, `editado_manualmente`, `atualizado_em`.

`app/backend/models/proposta_recurso_extra.py`: 2 classes (`PropostaRecursoExtra`, `PropostaRecursoAlocacao`) com relationship `recurso_extra.alocacoes` e `composicao.recursos_extras`.

`app/backend/models/proposta.py`: adicionar `cpu_desatualizada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)` e `composicao.recursos_extras` (back_populates).

- [ ] **Step 1**: migration 024
- [ ] **Step 2**: models proposta_pc.py + proposta_recurso_extra.py
- [ ] **Step 3**: campo cpu_desatualizada em Proposta + relationship em PropostaItemComposicao
- [ ] **Step 4**: aplicar migration → confirmar 10 tabelas novas em `operacional.*`
- [ ] **Step 5**: commit `feat(f2-11): migration 024 + proposta_pc + recurso_extra models`

---

## Task 2: Backend — `histograma_service`

**Files:**
- Create: `app/backend/services/histograma_service.py`
- Create: `app/backend/repositories/proposta_pc_repository.py`
- Create: `app/backend/tests/unit/test_histograma_service.py`

### Service principal

```python
class HistogramaService:
    """
    Gera histograma per-proposta a partir da sumarização das composições + BCU ativa.
    Fluxo:
      1. Pega bcu_cabecalho_ativo (ou usa proposta.bcu_cabecalho_id se já fixado)
      2. Lista composições da proposta (PropostaItemComposicao via cpu_explosao_service)
      3. Agrupa unique (insumo_id, tipo_recurso) das composições
      4. Para cada (insumo_id, tipo_recurso):
         a. lookup_bcu_para_base_tcpo(insumo_id) via De/Para
         b. Se mapeado: copia bcu.X[bcu_item_id].* para proposta_pc_X com:
            - bcu_item_id (vínculo)
            - valor_bcu_snapshot = bcu.X.{campo de custo}
            - editado_manualmente = FALSE
         c. Se não mapeado: cria entrada com codigo_origem=insumo.codigo,
            descricao=insumo.descricao, custo=insumo.custo_base, bcu_item_id=NULL
      5. Encargos e Mobilização: copia integralmente bcu.encargo_item e bcu.mobilizacao_item
         da BCU ativa (não filtrado por composição)
      6. Fixa proposta.bcu_cabecalho_id = id do cabecalho usado (snapshot da versão BCU)
      7. Marca proposta.cpu_desatualizada = TRUE (precisa recalcular CPU)
    
    Idempotência: ao re-montar, faz UPSERT por (proposta_id, bcu_item_id);
    preserva campos com editado_manualmente=TRUE (não sobrescreve).
    """

    async def montar_histograma(self, proposta_id: UUID) -> dict:
        """Retorna dict com contadores: {mao_obra: 5, equipamentos: 3, ...}."""

    async def get_histograma(self, proposta_id: UUID) -> HistogramaCompletoResponse:
        """Retorna todas as 7 abas + lista de divergências."""

    async def detectar_divergencias(self, proposta_id: UUID) -> list[Divergencia]:
        """
        Para cada item proposta_pc_* com bcu_item_id != NULL:
          - Compara valor atual em bcu.* com valor_bcu_snapshot
          - Se diferente, adiciona à lista de divergências com:
            (tabela, item_id, valor_snapshot, valor_atual_bcu, valor_proposta)
        """

    async def aceitar_valor_bcu(self, tabela: str, item_id: UUID) -> None:
        """
        Sobrescreve campo de custo do item proposta_pc_* com valor atual de bcu.*
        Atualiza valor_bcu_snapshot. Marca cpu_desatualizada=TRUE.
        """

    async def editar_item(self, tabela: str, item_id: UUID, payload: dict) -> None:
        """
        Atualiza campos do item proposta_pc_* (validação por tipo de tabela).
        Marca editado_manualmente=TRUE e cpu_desatualizada=TRUE.
        """
```

### Testes mínimos (12)

1. `montar_histograma` em proposta sem composições → retorna 0 itens
2. `montar_histograma` com composições + De/Para mapeado → cria entries em proposta_pc_*
3. `montar_histograma` com insumo sem De/Para → cria entry com bcu_item_id=NULL e custo de BaseTcpo.custo_base
4. `montar_histograma` copia integralmente Encargos e Mobilização (não filtrados)
5. `montar_histograma` re-execução preserva edições manuais (editado_manualmente=TRUE)
6. `montar_histograma` re-execução atualiza valor_bcu_snapshot para itens não-editados
7. `montar_histograma` fixa `proposta.bcu_cabecalho_id` e seta `cpu_desatualizada=TRUE`
8. `get_histograma` retorna 7 abas + divergências calculadas em tempo real
9. `detectar_divergencias`: muda valor em bcu.mao_obra → divergência aparece
10. `aceitar_valor_bcu`: sobrescreve custo + atualiza snapshot + cpu_desatualizada
11. `editar_item` válido: atualiza + flags
12. `editar_item` em campo inválido para a tabela → ValidationError

- [ ] **Step 1**: testes
- [ ] **Step 2**: HistogramaService + ProposalPcRepository
- [ ] **Step 3**: pytest PASS + commit `feat(f2-11): add HistogramaService for per-proposal cost snapshot`

---

## Task 3: Backend — `proposta_recurso_extra_service`

**Files:**
- Create: `app/backend/services/proposta_recurso_extra_service.py`
- Create: `app/backend/repositories/proposta_recurso_extra_repository.py`
- Create: `app/backend/tests/unit/test_proposta_recurso_extra_service.py`

### Service

```python
class PropostaRecursoExtraService:
    async def criar(self, proposta_id: UUID, body: RecursoExtraCreate) -> PropostaRecursoExtra:
        """
        Cria recurso extra. NÃO altera CPU diretamente — só após alocação.
        """

    async def atualizar(self, recurso_id: UUID, body: RecursoExtraUpdate) -> PropostaRecursoExtra:
        """
        Atualiza descricao, unidade, custo_unitario, observacao.
        Se já tem alocações, marca proposta.cpu_desatualizada=TRUE.
        """

    async def deletar(self, recurso_id: UUID) -> None:
        """
        CASCADE deleta alocações. Marca cpu_desatualizada=TRUE se havia alocações.
        """

    async def alocar(self, composicao_id: UUID, recurso_extra_id: UUID, quantidade_consumo: Decimal) -> PropostaRecursoAlocacao:
        """
        Vincula recurso_extra a uma composição com quantidade.
        Validação: composicao pertence à mesma proposta do recurso_extra.
        Marca cpu_desatualizada=TRUE.
        """

    async def desalocar(self, alocacao_id: UUID) -> None:
        """Remove alocação. Marca cpu_desatualizada=TRUE."""

    async def listar_por_proposta(self, proposta_id: UUID) -> list[dict]:
        """Lista com info de alocações (count + composições alvo)."""
```

### Testes mínimos (8)

1. Criar recurso extra → 201, sem impacto em CPU (cpu_desatualizada não muda)
2. Atualizar recurso sem alocações → não muda cpu_desatualizada
3. Atualizar recurso COM alocações → cpu_desatualizada=TRUE
4. Deletar recurso com alocações → CASCADE + cpu_desatualizada=TRUE
5. Alocar válida → 201 + cpu_desatualizada=TRUE
6. Alocar com composicao de outra proposta → 400
7. Alocar duplicada (mesmo recurso/composicao) → 409 (UniqueConstraint)
8. Desalocar → 204 + cpu_desatualizada=TRUE

- [ ] **Step 1**: testes
- [ ] **Step 2**: Service + Repository
- [ ] **Step 3**: pytest PASS + commit `feat(f2-11): add PropostaRecursoExtraService with allocation`

---

## Task 4: Backend — endpoints histograma + recursos extras

**Files:**
- Modify: `app/backend/api/v1/endpoints/propostas.py` (adicionar 8 endpoints)
- Create: `app/backend/schemas/proposta_pc.py`
- Create: `app/backend/tests/unit/test_histograma_endpoints.py`

### Endpoints

Atenção à ordem (rotas estáticas antes de `/{proposta_id}` parametrizada):

```python
# Histograma
@router.post("/{proposta_id}/montar-histograma", response_model=MontarHistogramaResponse)
async def montar_histograma(...):
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    counts = await svc.montar_histograma(proposta_id)
    await db.commit()
    return MontarHistogramaResponse(**counts)

@router.get("/{proposta_id}/histograma", response_model=HistogramaCompletoResponse)
async def get_histograma(...):
    await require_proposta_role(proposta_id, None, current_user, db)  # VIEWER pode ler
    ...

@router.patch("/{proposta_id}/histograma/{tabela}/{item_id}", response_model=...)
async def editar_item_histograma(tabela: str, item_id: UUID, body: dict, ...):
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    # tabela ∈ {mao-obra, equipamento, equipamento-premissa, encargo, epi, ferramenta, mobilizacao}
    ...

@router.post("/{proposta_id}/histograma/{tabela}/{item_id}/aceitar-bcu", response_model=...)
async def aceitar_valor_bcu(tabela: str, item_id: UUID, ...):
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    ...

# Recursos extras
@router.post("/{proposta_id}/recursos-extras", response_model=RecursoExtraOut, status_code=201)
async def criar_recurso_extra(body: RecursoExtraCreate, ...):
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    ...

@router.get("/{proposta_id}/recursos-extras", response_model=list[RecursoExtraOut])
async def listar_recursos_extras(...):
    await require_proposta_role(proposta_id, None, current_user, db)
    ...

@router.patch("/{proposta_id}/recursos-extras/{recurso_id}", ...)
async def atualizar_recurso_extra(...): ...

@router.delete("/{proposta_id}/recursos-extras/{recurso_id}", status_code=204)
async def deletar_recurso_extra(...): ...

# Alocação
@router.post("/{proposta_id}/composicoes/{composicao_id}/alocar-recurso", response_model=AlocacaoOut, status_code=201)
async def alocar_recurso(composicao_id: UUID, body: AlocarRecursoRequest, ...):
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    ...

@router.delete("/{proposta_id}/alocacoes/{alocacao_id}", status_code=204)
async def desalocar_recurso(...): ...
```

### Schemas

```python
class HistogramaCompletoResponse(BaseModel):
    proposta_id: UUID
    bcu_cabecalho_id: UUID | None
    mao_obra: list[PropostaPcMaoObraOut]
    equipamento_premissa: PropostaPcEquipamentoPremissaOut | None
    equipamentos: list[PropostaPcEquipamentoOut]
    encargos_horista: list[PropostaPcEncargoOut]
    encargos_mensalista: list[PropostaPcEncargoOut]
    epis: list[PropostaPcEpiOut]
    ferramentas: list[PropostaPcFerramentaOut]
    mobilizacao: list[PropostaPcMobilizacaoOut]
    recursos_extras: list[RecursoExtraOut]
    divergencias: list[DivergenciaOut]
    cpu_desatualizada: bool

class RecursoExtraCreate(BaseModel):
    tipo_recurso: str  # MO | EQP | EPI | FER | INSUMO | SERVICO
    descricao: str
    unidade_medida: str | None = None
    custo_unitario: Decimal
    observacao: str | None = None

class AlocarRecursoRequest(BaseModel):
    recurso_extra_id: UUID
    quantidade_consumo: Decimal = Decimal("1")
```

### Testes endpoint (10)

1. POST `/montar-histograma` como VIEWER → 403
2. POST `/montar-histograma` como EDITOR → 200, retorna counts
3. GET `/histograma` como VIEWER → 200, lista 7 abas
4. PATCH `/histograma/mao-obra/{id}` como EDITOR → 200, valor atualizado, cpu_desatualizada=TRUE
5. POST `/histograma/equipamento/{id}/aceitar-bcu` → 200
6. POST `/recursos-extras` como EDITOR → 201
7. POST `/recursos-extras/{id}/alocar-recurso` como EDITOR → 201
8. POST alocar recurso de outra proposta → 400
9. DELETE `/alocacoes/{id}` → 204
10. PATCH em tabela inválida (`/histograma/foo/{id}`) → 400

- [ ] **Step 1**: schemas
- [ ] **Step 2**: endpoints (atenção à ordem)
- [ ] **Step 3**: testes
- [ ] **Step 4**: pytest PASS + commit `feat(f2-11): add histograma and recurso-extra endpoints`

---

## Task 5: Backend — `cpu_custo_service` + integração

**Files:**
- Modify: `app/backend/services/cpu_custo_service.py`
- Modify: `app/backend/services/cpu_geracao_service.py`
- Modify: `app/backend/tests/unit/test_cpu_custo_service.py`

### Mudança em `CpuCustoService.calcular_custos`

Hierarquia de resolução de custo (do mais específico para o mais genérico):

```
1. Se proposta tem histograma (proposta_pc_*) com bcu_item_id correspondente:
   → usa o custo de proposta_pc_* (pode estar editado pelo usuário)
2. Senão, lookup De/Para → bcu.* (BCU global)
3. Senão, fallback BaseTcpo.custo_base + warning
```

```python
async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
    proposta_id = composicoes[0].proposta_item.proposta_id if composicoes else None
    if proposta_id is None:
        return

    # Pré-carrega histograma da proposta (uma única query por tipo)
    pc_repo = ProposalPcRepository(self.db)
    pc_mo = await pc_repo.list_mao_obra(proposta_id)
    pc_eqp = await pc_repo.list_equipamentos(proposta_id)
    pc_epi = await pc_repo.list_epi(proposta_id)
    pc_fer = await pc_repo.list_ferramentas(proposta_id)
    
    # Indexa por bcu_item_id
    pc_mo_by_bcu = {x.bcu_item_id: x for x in pc_mo if x.bcu_item_id}
    pc_eqp_by_bcu = {x.bcu_item_id: x for x in pc_eqp if x.bcu_item_id}
    pc_epi_by_bcu = {x.bcu_item_id: x for x in pc_epi if x.bcu_item_id}
    pc_fer_by_bcu = {x.bcu_item_id: x for x in pc_fer if x.bcu_item_id}

    for comp in composicoes:
        de_para = await self.de_para_repo.lookup(comp.insumo_id)
        if de_para is None:
            comp.custo_unitario_insumo = comp.custo_base_fallback or Decimal("0")
            comp.fonte_custo = "base_tcpo_fallback"
            continue
        
        # Tenta proposta_pc_* primeiro
        custo = None
        if de_para.bcu_table_type == BcuTableType.MO:
            pc_item = pc_mo_by_bcu.get(de_para.bcu_item_id)
            if pc_item:
                custo = pc_item.custo_unitario_h
                comp.fonte_custo = "proposta_pc_mao_obra"
        elif de_para.bcu_table_type == BcuTableType.EQP:
            pc_item = pc_eqp_by_bcu.get(de_para.bcu_item_id)
            if pc_item:
                custo = pc_item.aluguel_r_h
                comp.fonte_custo = "proposta_pc_equipamento"
        # ... (idem para EPI, FER)

        # Fallback para bcu.*
        if custo is None:
            custo = await self._lookup_bcu_global(de_para)
            comp.fonte_custo = "bcu_global"

        # Fallback final
        if custo is None:
            custo = comp.custo_base_fallback or Decimal("0")
            comp.fonte_custo = "base_tcpo_fallback"

        comp.custo_unitario_insumo = custo
        comp.custo_total_insumo = custo * comp.quantidade_consumo

    # Soma recursos extras alocados
    aloc_repo = PropostaRecursoExtraRepository(self.db)
    for comp in composicoes:
        alocacoes = await aloc_repo.list_by_composicao(comp.id)
        custo_extras = sum(
            (a.recurso_extra.custo_unitario * a.quantidade_consumo) for a in alocacoes
        )
        comp.custo_total_insumo += custo_extras
```

### Mudança em `CpuGeracaoService.gerar_cpu_para_proposta`

Ao final, setar `proposta.cpu_desatualizada = False`. Não chamar `montar_histograma` automaticamente — usuário decide com botão "Montar Histograma".

### Testes (5+ novos)

1. Composição com proposta_pc_mao_obra editado → custo vem do snapshot editado
2. Composição com proposta_pc sem entrada (não montou histograma ainda) → fallback para bcu.*
3. Composição sem De/Para nem proposta_pc → fallback BaseTcpo.custo_base
4. Soma de recursos extras alocados na composição
5. `gerar_cpu_para_proposta` reseta cpu_desatualizada=FALSE

- [ ] **Step 1**: testes
- [ ] **Step 2**: refatorar cpu_custo_service (lookup hierárquico + soma extras)
- [ ] **Step 3**: cpu_geracao_service: setar cpu_desatualizada=FALSE
- [ ] **Step 4**: pytest PASS + commit `feat(f2-11): cpu_custo_service uses proposta_pc_* with bcu fallback + extras allocation`

---

## Task 6: Backend — clonagem na nova versão

**Files:**
- Modify: `app/backend/services/proposta_versionamento_service.py`
- Modify: `app/backend/tests/unit/test_proposta_versionamento_service.py`

### Mudança em `nova_versao`

```python
async def nova_versao(self, proposta_id: UUID, criador_id: UUID, motivo_revisao: str | None = None):
    # ... lógica existente que cria nova proposta ...
    
    # NOVO: clonar histograma + recursos extras + alocações
    await self._clonar_histograma(atual.id, nova.id)
    await self._clonar_recursos_extras(atual.id, nova.id)
    # Alocações: precisam mapear composicoes antigas→novas. Como CPU/composições começam zeradas
    # na nova versão (RASCUNHO), as alocações ficam em recursos_extras sem alocação inicialmente.
    # Usuário re-aloca após gerar a nova CPU.
    
    return nova

async def _clonar_histograma(self, origem_id: UUID, destino_id: UUID) -> None:
    """Copia todas as 8 tabelas proposta_pc_* preservando edições."""
    # SQL bulk: INSERT ... SELECT com proposta_id substituído

async def _clonar_recursos_extras(self, origem_id: UUID, destino_id: UUID) -> None:
    """Copia proposta_recurso_extra. Alocações NÃO são copiadas (composições mudaram)."""
```

### Testes (3 novos)

1. `nova_versao` com histograma populado → v2 tem cópia de proposta_pc_*
2. `nova_versao` com recursos extras → v2 tem cópia (sem alocações)
3. `nova_versao` preserva campo `editado_manualmente=TRUE` no clone

- [ ] **Step 1**: testes
- [ ] **Step 2**: implementar clonagem
- [ ] **Step 3**: pytest PASS + commit `feat(f2-11): proposta_versionamento clones histograma and recursos extras`

---

## Task 7: Frontend — API client

**Files:**
- Create: `app/frontend/src/shared/services/api/histogramaApi.ts`
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts` (campo `cpu_desatualizada`)

### histogramaApi.ts

```typescript
export interface HistogramaCompleto {
  proposta_id: string;
  bcu_cabecalho_id: string | null;
  mao_obra: PcMaoObraItem[];
  equipamento_premissa: PcEquipamentoPremissa | null;
  equipamentos: PcEquipamentoItem[];
  encargos_horista: PcEncargoItem[];
  encargos_mensalista: PcEncargoItem[];
  epis: PcEpiItem[];
  ferramentas: PcFerramentaItem[];
  mobilizacao: PcMobilizacaoItem[];
  recursos_extras: RecursoExtra[];
  divergencias: Divergencia[];
  cpu_desatualizada: boolean;
}

export interface Divergencia {
  tabela: 'mao-obra' | 'equipamento' | 'epi' | 'ferramenta' | 'encargo';
  item_id: string;
  campo: string;
  valor_snapshot: number | null;
  valor_atual_bcu: number | null;
  valor_proposta: number | null;
}

export interface RecursoExtra {
  id: string;
  proposta_id: string;
  tipo_recurso: 'MO' | 'EQP' | 'EPI' | 'FER' | 'INSUMO' | 'SERVICO';
  descricao: string;
  unidade_medida: string | null;
  custo_unitario: number;
  observacao: string | null;
  alocacoes_count: number;
}

export const histogramaApi = {
  async montar(propostaId: string) { ... },
  async get(propostaId: string) { ... },
  async editarItem(propostaId: string, tabela: string, itemId: string, body: object) { ... },
  async aceitarBcu(propostaId: string, tabela: string, itemId: string) { ... },
  async listarRecursosExtras(propostaId: string) { ... },
  async criarRecursoExtra(propostaId: string, body: RecursoExtraCreate) { ... },
  async atualizarRecursoExtra(propostaId: string, id: string, body: RecursoExtraUpdate) { ... },
  async deletarRecursoExtra(propostaId: string, id: string) { ... },
  async alocarRecurso(propostaId: string, composicaoId: string, body: AlocarRecursoRequest) { ... },
  async desalocarRecurso(propostaId: string, alocacaoId: string) { ... },
};
```

### proposalsApi.ts

Adicionar `cpu_desatualizada?: boolean` em `PropostaResponse`.

- [ ] **Step 1**: histogramaApi.ts (todos os métodos)
- [ ] **Step 2**: campo em proposalsApi.ts
- [ ] **Step 3**: tsc OK + commit `feat(f2-11): add histogramaApi client`

---

## Task 8: Frontend — UI principal

**Files:**
- Create: `app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx`
- Create: `app/frontend/src/features/proposals/components/HistogramaTabMaoObra.tsx`
- Create: `app/frontend/src/features/proposals/components/HistogramaTabGenerica.tsx`
- Create: `app/frontend/src/features/proposals/components/RecursosExtrasTab.tsx`
- Create: `app/frontend/src/features/proposals/components/AlocacaoRecursoDialog.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- Modify: `app/frontend/src/features/proposals/components/CpuTable.tsx`
- Modify: `app/frontend/src/features/proposals/routes.tsx`

### ProposalDetailPage — alterações

**Botão "Montar Histograma"** — visível quando:
- `proposta.status in ['CPU_GERADA', 'AGUARDANDO_APROVACAO']` OU já tem composições
- Papel >= EDITOR
- Posicionado próximo a "Gerar CPU" / "Recalcular BDI"

**Badge "CPU desatualizada"** — visível quando:
- `proposta.cpu_desatualizada === true`
- Tooltip: "O histograma foi alterado. Clique em 'Recalcular CPU' para atualizar os valores."
- Cor: warning (amber)

**Card "Histograma"** logo abaixo do card CPU:
- Resumo: "X itens MO | Y itens Equip | Z recursos extras"
- Link "Abrir Histograma" → navega para `/propostas/{id}/histograma`

### ProposalHistogramaPage

Layout principal (replica visual de `BcuPage` mas com edição):

```
┌──────────────────────────────────────────────────────────┐
│ ← Voltar para Proposta  |  Proposta ORC-001 v2          │
│                                                          │
│ ⚠️  3 divergências com BCU global  [Ver detalhes]       │
│ ⚠️  CPU desatualizada — recalcular para refletir         │
├──────────────────────────────────────────────────────────┤
│ [MO] [Equip] [Enc.Hor] [Enc.Mens] [EPI] [Fer] [Mob] [Extras] │
├──────────────────────────────────────────────────────────┤
│ <Tabela editável da aba ativa>                          │
└──────────────────────────────────────────────────────────┘
```

Header: query `histogramaApi.get(propostaId)`. Se vazio, mostra empty state com botão "Montar Histograma".

### HistogramaTabMaoObra (especializado)

Replica `MaoObraTab` de BcuPage mas:
- Cada célula numérica é editável (component `EditableCell` com debounce 800ms)
- Indicador `editado_manualmente`: borda azul à esquerda da linha
- Indicador divergência BCU: chip "BCU R$ X" com botão "Aceitar"
- Coluna extra "Origem": chip "Snapshot" (cinza), "Editado" (azul), "Sem BCU" (amarelo)

### HistogramaTabGenerica

Componente reutilizável para Equipamentos / EPI / Ferramentas / Encargos. Recebe:
```typescript
interface Props<T> {
  rows: T[];
  columns: ColumnDef<T>[];
  onEdit: (id: string, field: string, value: number) => void;
  onAceitarBcu: (id: string) => void;
  divergencias: Divergencia[];
}
```

### RecursosExtrasTab

```
┌─────────────────────────────────────────────────────────────┐
│ + Adicionar recurso extra                                  │
├─────────────────────────────────────────────────────────────┤
│ Tipo  Descrição          Unid  Custo Unit.  Alocações  Ações│
│ MO    Engenheiro PJ      h     180,00       2          [👁][✏][🗑]│
│ EPI   Capacete Premium   un    35,00        0          [👁][✏][🗑]│
└─────────────────────────────────────────────────────────────┘
```

- "Adicionar recurso extra" abre Dialog com form (tipo + descricao + unidade + custo + observação)
- 👁 abre lista de composições onde está alocado
- ✏ edita inline ou via Dialog
- 🗑 confirma + deleta (warning se tem alocações)

### CpuTable — alterações

Em cada linha da composição (insumo), adicionar coluna "Recursos Extras":
- Lista alocações: chip "Eng PJ x 2.5h"
- Botão "+ Alocar recurso extra" → abre `AlocacaoRecursoDialog`

### AlocacaoRecursoDialog

```
┌─────────────────────────────────────┐
│ Alocar Recurso Extra à Composição  │
├─────────────────────────────────────┤
│ Composição: Eletricista (MO-001)   │
│                                     │
│ Recurso extra: [Engenheiro PJ ▾]   │
│ Quantidade: [____2.5_____]          │
│ Custo unit. (snapshot): R$ 180,00  │
│ Custo total: R$ 450,00             │
│                                     │
│           [Cancelar]  [Alocar]     │
└─────────────────────────────────────┘
```

### routes.tsx

```tsx
const ProposalHistogramaPage = lazy(() => import('./pages/ProposalHistogramaPage'));

// dentro do bloco propostas, ANTES de :id:
<Route path=":id/histograma" element={<ProposalHistogramaPage />} />
```

- [ ] **Step 1**: ProposalHistogramaPage + abas
- [ ] **Step 2**: HistogramaTabMaoObra + HistogramaTabGenerica
- [ ] **Step 3**: RecursosExtrasTab + Dialog de criação/edição
- [ ] **Step 4**: AlocacaoRecursoDialog
- [ ] **Step 5**: CpuTable: coluna recursos extras + botão alocar
- [ ] **Step 6**: ProposalDetailPage: botão "Montar Histograma" + badge cpu_desatualizada
- [ ] **Step 7**: routes
- [ ] **Step 8**: tsc OK + commit `feat(f2-11): add ProposalHistogramaPage with editable tabs and recursos extras`

---

## Task 9: Validação final

- [ ] `cd app && python -m pytest backend/tests/ --tb=short` → **245+ PASS, 0 FAIL** (~40 testes novos sobre 200+ base de F2-10)
- [ ] `cd app/frontend && npx tsc --noEmit` → **0 erros**
- [ ] Migration 024:
  - `alembic upgrade head` sem erro
  - 10 tabelas novas em `operacional.*`
  - `propostas.cpu_desatualizada` coluna existe (default FALSE)
- [ ] Smoke teste manual end-to-end:
  - Pré: BCU importada e ativada (F2-10), De/Para mapeado para alguns TCPO
  - Criar proposta → upload PQ → match → confirmar
  - POST `/montar-histograma` → 200, retorna counts
  - GET `/histograma` → vê 7 abas + recursos extras vazio
  - PATCH custo MO → cpu_desatualizada=TRUE
  - POST `/recursos-extras` → criado
  - POST `/alocar-recurso` → vinculado a composição
  - POST `/recalcular-bdi` ou `/gerar-cpu` → cpu_desatualizada=FALSE
- [ ] Versionamento: nova versão clona histograma + recursos extras (sem alocações)
- [ ] Frontend smoke:
  - Acessar `/propostas/{id}` → vê botão "Montar Histograma" pós-match
  - Após clicar → navega ou abre histograma populado
  - Editar célula MO → debounce salva, badge "Editado" aparece, badge "CPU desatualizada" aparece
  - Aba "Recursos Extras" → criar e editar funciona
  - Em CpuTable: alocar recurso extra a composição funciona
- [ ] Atualizar `docs/shared/governance/BACKLOG.md` (F2-11 → TESTED)
- [ ] Criar `docs/sprints/F2-11/technical-review/technical-review-2026-04-XX-f2-11.md`
- [ ] Criar `docs/sprints/F2-11/walkthrough/done/walkthrough-F2-11.md`

---

## Self-Review

**Spec coverage:**
- ✅ Trigger explícito "Montar Histograma" (botão, não automático)
- ✅ Snapshot sincronizado: `valor_bcu_snapshot` + comparação em runtime
- ✅ Edição editável com `editado_manualmente` flag (preservado em re-execução)
- ✅ Encargos e Mobilização cópia integral (não filtrados)
- ✅ MO/EQP/EPI/FER filtrados via De/Para a partir das composições
- ✅ Recursos extras criáveis sem impacto + alocação explícita para entrar no CPU
- ✅ `proposta.cpu_desatualizada` flag + badge frontend + reset em gerar-cpu
- ✅ Versionamento: clone de histograma + recursos extras (sem alocações)
- ✅ `cpu_custo_service` hierarquia: proposta_pc_* > bcu.* > BaseTcpo

**Decisões arquiteturais:**
- `bcu_item_id` em `proposta_pc_*` é UUID **sem FK física** (BCU pode ser deletado, snapshot persiste). Validação no service.
- `valor_bcu_snapshot` armazena UM valor de custo de referência (custo_unitario_h para MO, aluguel_r_h para EQP, etc.) — divergência é detectada por comparação simples desse valor com o atual em bcu.*.
- Encargos e Mobilização não têm `valor_bcu_snapshot` (são parametrizações compostas). Detecção de divergência para esses tipos é fora do escopo desta sprint (futuro).
- Recursos extras alocados são somados como custo adicional na composição — não se misturam com explosão TCPO.
- `cpu_desatualizada` é trigger explícito (não automático no banco) — services o setam após mutação.
- Clonagem de versão: alocações são "esquecidas" (composições da v2 são novas após CPU regenerar). Trade-off: usuário re-aloca após gerar CPU da v2.

**Critérios de aceite:**
- 245+ pytest PASS, 0 FAIL
- 0 erros tsc
- Migration 024 idempotente
- Fluxo PQ → Match → Histograma → CPU funcional ponta a ponta
- Edição per-proposta isolada (BCU global não afetada)
- Recursos extras alocáveis com impacto correto no CPU
- Versionamento clona histograma preservando edições
