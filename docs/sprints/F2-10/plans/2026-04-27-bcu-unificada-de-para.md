# F2-10: BCU Unificada (Base de Custos Unitários) + De/Para — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidar a base global de custos. Substituir `pc_*` (schema `public`) por `bcu.*` (schema dedicado). Eliminar pipelines duplicados (Converter ETL + Carga inteligente PC + PC Tabelas upload), restando um único upload "BCU". Implementar mapeamento explícito **De/Para** entre `referencia.base_tcpo` (catálogo) e `bcu.*` (parâmetros de custo) gerenciado pelo usuário. Refatorar `cpu_custo_service` para resolver custos via De/Para em vez de heurística.

**Architecture:**
- Migration 023: drop schemas `public.pc_*` e `public.etl_carga`; drop FK `propostas.pc_cabecalho_id`; create schema `bcu` + 9 tabelas (cabecalho, mao_obra_item, equipamento_premissa, equipamento_item, encargo_item, epi_item, epi_distribuicao_funcao, ferramenta_item, mobilizacao_item, mobilizacao_quantidade_funcao) + de_para; recreate FK `propostas.bcu_cabecalho_id` nullable.
- **Banco pode ser resetado** (PO autorizou em 2026-04-27): drop direto sem migrar dados; `pc_*` é descartado, `bcu.*` nasce vazio.
- `bcu.de_para`: tabela polimórfica com `base_tcpo_id` (FK) + `bcu_table_type` (enum {MO, EQP, EPI, FER, MOB}) + `bcu_item_id` (UUID, sem FK por ser polimórfico — checked via service). UniqueConstraint em `base_tcpo_id` (1:1 mapping).
- Refatoração `etl_service.parse_converter_datacenter` removida; `pc_tabelas_service.importar_pc_tabelas` renomeado para `bcu_service.importar_bcu` e estendido para também atualizar `referencia.base_tcpo` durante a importação (cria/atualiza itens correspondentes com `codigo_origem` derivado, ex: `BCU-MO-001`, `BCU-EPI-001`).
- Frontend: `PcTabelasPage` → `BcuPage` (rota `/bcu`). `UploadTcpoPage` perde seções "Converter" e ganha apenas "BCU". `AdminPage` perde "Carga inteligente PC" (mantém TCPO via subprocess). Nova rota `/bcu/de-para`.
- `cpu_custo_service`: lookup do custo unitário muda de match heurístico para `SELECT bcu_*.custo FROM bcu_de_para WHERE base_tcpo_id = :insumo_id`. Fallback para custo do `BaseTcpo.custo_base` se não houver mapeamento (com warning no log).

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Pré-requisito de leitura (obrigatório antes de codar)

**Leia na ordem antes de começar:**

1. `docs/shared/governance/BACKLOG.md` — sprint F2-10 (escopo + critérios de aceite)
2. `docs/sprints/F2-09/technical-review/technical-review-2026-04-27-f2-09.md` — o que F2-09 entregou (versionamento)
3. `app/backend/models/pc_tabelas.py` — estrutura atual a ser substituída
4. `app/backend/services/pc_tabelas_service.py` — parser PC Tabelas (será reusado em `bcu_service`)
5. `app/backend/services/etl_service.py` — `parse_converter_datacenter` (será descontinuado)
6. `app/backend/services/cpu_custo_service.py` — lookup atual de custos (será refatorado)
7. `app/backend/api/v1/endpoints/pc_tabelas.py` — endpoints atuais (substituídos por `/bcu/*`)
8. `app/backend/api/v1/endpoints/admin.py` — `/admin/etl/upload-converter` e `/admin/import/*` (a remover)
9. `app/backend/models/base_tcpo.py` — alvo do De/Para
10. `app/alembic/versions/022_proposta_versionamento.py` — padrão de migration mais recente
11. `app/frontend/src/features/pc-tabelas/PcTabelasPage.tsx` — UI a renomear
12. `app/frontend/src/features/admin/UploadTcpoPage.tsx` — seções a unificar
13. `app/frontend/src/shared/services/api/pcTabelasApi.ts` — API client a renomear

**Decisões já tomadas (não rediscutir):**
- Nome final: **BCU — Base de Custos Unitários** (pareia com CPU)
- Schema PostgreSQL: `bcu.*` (paralelo a `referencia.*` e `operacional.*`)
- Reset do banco autorizado (PO): drop direto de `pc_*`, sem backfill
- De/Para é **manual e gerenciado pelo usuário** (1:1, UniqueConstraint em `base_tcpo_id`); sugestões IA por similaridade são opcionais e ficam fora do escopo desta sprint
- BCU mantém conceito de **cabecalho** (múltiplas versões da BCU possíveis); `bcu.cabecalho.is_ativo` flag identifica a versão ativa em uso
- Encargos e Mobilização **não entram no De/Para** — são valores globais aplicados em fórmulas (encargos = % sobre folha; mobilização = exames per função). Apenas MO, EQP, EPI, FER são mapeáveis
- Importação BCU **também atualiza `referencia.base_tcpo`** com `codigo_origem` derivado (`BCU-MO-N`, `BCU-EPI-N`, etc.) — assim o item fica pesquisável no catálogo E disponível para De/Para
- `cpu_custo_service` usa De/Para com fallback para `BaseTcpo.custo_base` quando não mapeado (com warning estruturado)
- Sprint M7 (Compras + Negociação) movida para `on-hold` — F2-12..F2-15 marcadas como bloqueadas

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/alembic/versions/023_bcu_unificada.py` | Criar | Drop pc_*; create schema bcu + 10 tabelas + de_para; recreate FK propostas.bcu_cabecalho_id |
| `app/backend/models/pc_tabelas.py` | Deletar | Substituído por `bcu.py` |
| `app/backend/models/bcu.py` | Criar | Models do schema bcu (10 tabelas + DeParaTcpoBcu) |
| `app/backend/models/proposta.py` | Modificar | Renomear `pc_cabecalho_id` → `bcu_cabecalho_id` (FK para `bcu.cabecalho.id`) |
| `app/backend/repositories/bcu_repository.py` | Criar | CRUD para bcu.cabecalho + 9 tabelas filhas |
| `app/backend/repositories/bcu_de_para_repository.py` | Criar | CRUD do De/Para; lookup por `base_tcpo_id` |
| `app/backend/repositories/pc_tabelas_repository.py` | Deletar | Substituído |
| `app/backend/services/pc_tabelas_service.py` | Deletar | Substituído por `bcu_service` |
| `app/backend/services/bcu_service.py` | Criar | Importar BCU.xlsx → grava em bcu.* + referencia.base_tcpo (sync) |
| `app/backend/services/bcu_de_para_service.py` | Criar | CRUD De/Para + validação de tipo coerente (base_tcpo.tipo_recurso bate com bcu_table_type) |
| `app/backend/services/etl_service.py` | Modificar | Remover `parse_converter_datacenter` e seu cache |
| `app/backend/services/cpu_custo_service.py` | Modificar | Lookup via `bcu_de_para` → bcu.* tabela; fallback `BaseTcpo.custo_base` |
| `app/backend/services/import_preview_service.py` | Modificar | Remover branch `source_type=PC` (deprecated) |
| `app/backend/api/v1/endpoints/pc_tabelas.py` | Deletar | Substituído |
| `app/backend/api/v1/endpoints/bcu.py` | Criar | Endpoints `/bcu/cabecalhos`, `/bcu/{id}/{tabela}`, `/bcu/importar`, `/bcu/de-para` (CRUD) |
| `app/backend/api/v1/endpoints/admin.py` | Modificar | Remover `/etl/upload-converter`; `/import/execute` aceita só `source_type=TCPO` |
| `app/backend/api/v1/router.py` | Modificar | Substituir include `pc_tabelas.router` por `bcu.router` |
| `app/backend/schemas/pc_tabelas.py` | Deletar | Substituído |
| `app/backend/schemas/bcu.py` | Criar | Schemas Pydantic equivalentes + DeParaCreate/Update/Response |
| `app/backend/schemas/admin.py` | Modificar | `ImportSourceType` perde valor `PC` (só TCPO sobra) |
| `app/backend/tests/unit/test_pc_tabelas_*.py` | Renomear/Reescrever | Testes batizados para bcu_* |
| `app/backend/tests/unit/test_bcu_service.py` | Criar | Importação BCU + sync base_tcpo + atualização in-place |
| `app/backend/tests/unit/test_bcu_de_para_service.py` | Criar | CRUD De/Para + validação de tipo + UniqueConstraint |
| `app/backend/tests/unit/test_cpu_custo_service.py` | Modificar | Lookup via De/Para; fallback BaseTcpo |
| `app/frontend/src/shared/services/api/pcTabelasApi.ts` | Deletar | Substituído |
| `app/frontend/src/shared/services/api/bcuApi.ts` | Criar | API client + tipos |
| `app/frontend/src/shared/services/api/bcuDeParaApi.ts` | Criar | API client De/Para |
| `app/frontend/src/features/pc-tabelas/PcTabelasPage.tsx` | Deletar | Substituído |
| `app/frontend/src/features/bcu/BcuPage.tsx` | Criar | Rebrand de PcTabelasPage com 7 abas |
| `app/frontend/src/features/bcu/BcuDeParaPage.tsx` | Criar | Tela de mapeamento TCPO ↔ BCU |
| `app/frontend/src/features/admin/UploadTcpoPage.tsx` | Modificar | Remover seção Converter; renomear "PC Tabelas" → "BCU"; chama `bcuApi.importar` |
| `app/frontend/src/features/admin/AdminPage.tsx` | Modificar | Remover opção "PC" do dropdown "Carga inteligente" (só TCPO) |
| `app/frontend/src/app/router.tsx` | Modificar | Rota `/pc-tabelas` → `/bcu`; nova rota `/bcu/de-para` |
| `app/frontend/src/shared/components/layout/navigationConfig.tsx` | Modificar | Item "PC Tabelas" → "BCU"; novo item "Mapeamento De/Para" |

---

## Task 1: Backend — migration 023 + models BCU

**Files:**
- Create: `app/alembic/versions/023_bcu_unificada.py`
- Create: `app/backend/models/bcu.py`
- Modify: `app/backend/models/proposta.py`
- Delete: `app/backend/models/pc_tabelas.py` (após cópia para bcu.py)

### Step 1: Migration 023

```python
# app/alembic/versions/023_bcu_unificada.py
revision = "023"
down_revision = "022"

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGEnum


def upgrade():
    # 1. Drop FK propostas.pc_cabecalho_id (se existe) e remove a coluna
    op.execute("ALTER TABLE operacional.propostas DROP COLUMN IF EXISTS pc_cabecalho_id CASCADE")

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
        sa.Column("codigo_origem", sa.String(40), nullable=True, index=True),  # vínculo com BaseTcpo
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
        sa.Column("bcu_item_id", PGUUID(as_uuid=True), nullable=False),  # FK lógica via service
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


def downgrade():
    op.execute("ALTER TABLE operacional.propostas DROP COLUMN IF EXISTS bcu_cabecalho_id CASCADE")
    op.execute("DROP SCHEMA IF EXISTS bcu CASCADE")
    op.execute("DROP TYPE IF EXISTS bcu_table_type_enum")
    # Não recriamos pc_* (drop irreversível por design — sprint reset)
```

### Step 2: Models BCU (`app/backend/models/bcu.py`)

Espelha `pc_tabelas.py` mas com `__table_args__ = {"schema": "bcu"}` em todas as classes, prefixos removidos do `__tablename__` (`cabecalho` em vez de `pc_cabecalho`), classes renomeadas (`BcuCabecalho`, `BcuMaoObraItem`, etc.). Adicionar:

- `BcuCabecalho.is_ativo: bool` (default False)
- `BcuCabecalho.criado_por_id: UUID | None` (FK `operacional.usuarios.id`)
- `BcuMaoObraItem.codigo_origem: str | None`, índice (vínculo lógico com `BaseTcpo`)
- Idem para `BcuEquipamentoItem`, `BcuEpiItem`, `BcuFerramentaItem`
- Nova classe `DeParaTcpoBcu`:

```python
class BcuTableType(str, enum.Enum):
    MO = "MO"
    EQP = "EQP"
    EPI = "EPI"
    FER = "FER"
    MOB = "MOB"


class DeParaTcpoBcu(Base):
    __tablename__ = "de_para"
    __table_args__ = (
        UniqueConstraint("base_tcpo_id", name="uq_de_para_base_tcpo"),
        {"schema": "bcu"},
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_tcpo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id", ondelete="CASCADE"),
        nullable=False,
    )
    bcu_table_type: Mapped[BcuTableType] = mapped_column(
        PGEnum(BcuTableType, name="bcu_table_type_enum", create_type=False),
        nullable=False,
    )
    bcu_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    criado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operacional.usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
```

### Step 3: Renomear `Proposta.pc_cabecalho_id` → `bcu_cabecalho_id`

```python
# em app/backend/models/proposta.py
bcu_cabecalho_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("bcu.cabecalho.id"),
    nullable=True,
)
```

Buscar todos os usos de `pc_cabecalho_id` no código (services, schemas, repos, frontend) e renomear para `bcu_cabecalho_id`. Lista esperada de arquivos a tocar (ripgrep):
- `app/backend/services/cpu_geracao_service.py`
- `app/backend/repositories/proposta_repository.py`
- `app/backend/schemas/proposta.py`
- `app/frontend/src/shared/services/api/proposalsApi.ts` (campo na interface)

- [ ] **Step 1**: migration 023 (drop pc_*, create bcu.*)
- [ ] **Step 2**: criar `app/backend/models/bcu.py` (copiar de pc_tabelas.py com renomeações + de_para + codigo_origem)
- [ ] **Step 3**: renomear `pc_cabecalho_id` → `bcu_cabecalho_id` em todo o backend + frontend
- [ ] **Step 4**: deletar `app/backend/models/pc_tabelas.py`
- [ ] **Step 5**: aplicar migration → confirmar `\dt bcu.*` retorna 10 tabelas + de_para
- [ ] **Step 6**: commit `feat(f2-10): migration 023 + BCU models replacing pc_tabelas`

---

## Task 2: Backend — `bcu_service` (importação unificada)

**Files:**
- Create: `app/backend/services/bcu_service.py`
- Create: `app/backend/repositories/bcu_repository.py`
- Create: `app/backend/tests/unit/test_bcu_service.py`
- Delete: `app/backend/services/pc_tabelas_service.py`
- Delete: `app/backend/repositories/pc_tabelas_repository.py`

### Service principal

```python
# app/backend/services/bcu_service.py
class BcuService:
    """
    Importa o arquivo BCU.xlsx (planilha mestra de custos) com 7 abas:
    Mão de Obra, Equipamentos, Encargos Horista, Encargos Mensalista,
    EPI/Uniforme, Ferramentas, Mobilização.
    
    Ao importar:
      1. Cria bcu.cabecalho (is_ativo=False inicialmente)
      2. Popula 9 tabelas filhas (espelha pc_tabelas_service.importar_pc_tabelas)
      3. Sincroniza referencia.base_tcpo:
         - Para cada item de MO/EQP/EPI/FER, cria/atualiza um BaseTcpo correspondente
         - codigo_origem = "BCU-{tipo}-{N}" (ex: BCU-MO-001, BCU-EPI-042)
         - tipo_recurso mapeado: MO → MO, EQP → EQUIPAMENTO, EPI → INSUMO, FER → FERRAMENTA
         - custo_base = custo_unitario_h (MO) | aluguel_r_h (EQP) | custo_unitario (EPI) | preco (FER)
         - Grava o codigo_origem também na linha bcu.* para vínculo
      4. Encargos e Mobilização NÃO são sincronizados com base_tcpo (não são itens de catálogo)
    
    Após importar:
      - Endpoint separado POST /bcu/cabecalhos/{id}/ativar promove para is_ativo=TRUE
      - Apenas UMA linha pode ter is_ativo=TRUE (índice parcial garante)
    """
    async def importar_bcu(
        self, file_bytes: bytes, nome_arquivo: str, criador_id: UUID
    ) -> BcuCabecalho:
        ...

    async def ativar_cabecalho(self, cabecalho_id: UUID) -> BcuCabecalho:
        # Desativa todos os outros, ativa este
        ...

    async def get_cabecalho_ativo(self) -> BcuCabecalho | None:
        ...
```

### Endpoints derivados (subset; full list em Task 4)

- `POST /bcu/importar` — substitui `POST /pc-tabelas/importar`
- `POST /bcu/cabecalhos/{id}/ativar` — novo
- `GET /bcu/cabecalhos` — lista todas
- `GET /bcu/{cabecalho_id}/mao-obra` — espelha PC

### Testes mínimos (10)

1. `importar_bcu` válido com 7 abas → cria cabecalho + N rows em cada tabela bcu.*
2. `importar_bcu` cria BaseTcpo correspondentes para MO/EQP/EPI/FER (não para Encargos/Mob)
3. `importar_bcu` re-importação atualiza linhas existentes via `codigo_origem` (idempotente)
4. `ativar_cabecalho` desativa anteriores e ativa o solicitado
5. `ativar_cabecalho` idempotente (ativar o já ativo é no-op)
6. `get_cabecalho_ativo` retorna o ativo (ou None)
7. Importação com aba faltante → erro 422 claro
8. Importação com arquivo vazio → ValidationError
9. Sync `BaseTcpo`: ao re-importar, `custo_base` é atualizado (não duplica registro)
10. UniqueConstraint `is_ativo` parcial: 2 ativos viola (cobre via service, não DB)

- [ ] **Step 1**: testes
- [ ] **Step 2**: BcuService + BcuRepository (reutiliza lógica de parser de `pc_tabelas_service`)
- [ ] **Step 3**: deletar `pc_tabelas_service.py` + `pc_tabelas_repository.py`
- [ ] **Step 4**: pytest PASS + commit `feat(f2-10): add BcuService with BCU.xlsx import + base_tcpo sync`

---

## Task 3: Backend — `bcu_de_para_service`

**Files:**
- Create: `app/backend/services/bcu_de_para_service.py`
- Create: `app/backend/repositories/bcu_de_para_repository.py`
- Create: `app/backend/tests/unit/test_bcu_de_para_service.py`

### Service

```python
class BcuDeParaService:
    """
    Gerencia mapeamento explícito 1:1 entre referencia.base_tcpo e bcu.*.
    UniqueConstraint em base_tcpo_id garante 1:1 (cada item TCPO mapeia para exatamente 1 BCU).
    """
    # Tipos polimórficos válidos
    VALID_TYPES = {BcuTableType.MO, BcuTableType.EQP, BcuTableType.EPI, BcuTableType.FER, BcuTableType.MOB}

    async def listar(self, search: str | None = None, only_unmapped: bool = False) -> list[dict]:
        """
        Retorna todas as entradas com join em base_tcpo (descricao + tipo_recurso).
        Se only_unmapped=True, retorna BaseTcpo sem mapeamento.
        """

    async def criar(
        self, base_tcpo_id: UUID, bcu_table_type: BcuTableType, bcu_item_id: UUID, criador_id: UUID
    ) -> DeParaTcpoBcu:
        """
        Validações:
          - base_tcpo_id existe em referencia.base_tcpo
          - bcu_item_id existe na tabela bcu correspondente ao bcu_table_type
          - tipo_recurso de BaseTcpo é coerente com bcu_table_type:
              MO TCPO → MO BCU; EQUIPAMENTO TCPO → EQP BCU;
              INSUMO TCPO → EPI ou FER BCU; FERRAMENTA TCPO → FER BCU
        """

    async def atualizar(
        self, de_para_id: UUID, bcu_table_type: BcuTableType, bcu_item_id: UUID
    ) -> DeParaTcpoBcu:
        ...

    async def deletar(self, de_para_id: UUID) -> None:
        ...

    async def lookup_bcu_para_base_tcpo(self, base_tcpo_id: UUID) -> tuple[BcuTableType, UUID] | None:
        """Usado por cpu_custo_service para resolver custos via De/Para."""
```

### Testes mínimos (8)

1. Criar mapeamento válido MO TCPO → MO BCU → 201
2. Criar mapeamento com tipo incoerente (MO TCPO → EQP BCU) → ValidationError
3. Criar duplicado (mesmo base_tcpo_id) → IntegrityError (UniqueConstraint)
4. Atualizar mapeamento existente → muda bcu_item_id
5. Deletar mapeamento → DELETE no DB
6. `listar` retorna join completo com BaseTcpo
7. `listar(only_unmapped=True)` retorna BaseTcpo sem entrada em de_para
8. `lookup_bcu_para_base_tcpo` retorna tipo + bcu_item_id quando existe; None quando não

- [ ] **Step 1**: testes
- [ ] **Step 2**: BcuDeParaService + Repository
- [ ] **Step 3**: pytest PASS + commit `feat(f2-10): add BcuDeParaService for explicit TCPO↔BCU mapping`

---

## Task 4: Backend — endpoints `/bcu` + `/bcu/de-para`

**Files:**
- Create: `app/backend/api/v1/endpoints/bcu.py`
- Create: `app/backend/schemas/bcu.py`
- Modify: `app/backend/api/v1/router.py` (substituir include)
- Delete: `app/backend/api/v1/endpoints/pc_tabelas.py`
- Delete: `app/backend/schemas/pc_tabelas.py`
- Modify: `app/backend/api/v1/endpoints/admin.py` (remover Converter + PC import)
- Modify: `app/backend/schemas/admin.py` (`ImportSourceType` perde valor `PC`)
- Create: `app/backend/tests/unit/test_bcu_endpoints.py`

### Endpoints

```python
# app/backend/api/v1/endpoints/bcu.py
router = APIRouter(prefix="/bcu", tags=["bcu"])


@router.get("/cabecalhos", response_model=list[BcuCabecalhoOut])
async def listar_cabecalhos(...): ...

@router.get("/cabecalho-ativo", response_model=BcuCabecalhoOut | None)
async def get_cabecalho_ativo(...): ...

@router.post("/importar", response_model=BcuCabecalhoOut)
async def importar_bcu(file: UploadFile, _=Depends(get_current_admin_user), ...): ...

@router.post("/cabecalhos/{cabecalho_id}/ativar", response_model=BcuCabecalhoOut)
async def ativar_cabecalho(...): ...

@router.get("/{cabecalho_id}/mao-obra", response_model=list[BcuMaoObraItemOut])
async def listar_mao_obra(...): ...

# (idem para equipamentos, encargos, epi, ferramentas, mobilizacao)

# ── De/Para ────────────────────────────────────────────────────────────
@router.get("/de-para", response_model=list[DeParaListItemOut])
async def listar_de_para(
    only_unmapped: bool = False,
    search: str | None = None,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
): ...

@router.post("/de-para", response_model=DeParaOut, status_code=201)
async def criar_de_para(body: DeParaCreate, current_user=Depends(get_current_admin_user), ...): ...

@router.patch("/de-para/{id}", response_model=DeParaOut)
async def atualizar_de_para(...): ...

@router.delete("/de-para/{id}", status_code=204)
async def deletar_de_para(...): ...
```

### Mudanças em `admin.py`

- Remover `POST /admin/etl/upload-converter` (e o cache `_CONVERTER_PARSE_CACHE` no etl_service)
- Em `POST /admin/import/execute`, manter só `source_type=TCPO`. Se receber `PC`, retornar 410 Gone com mensagem "Use POST /bcu/importar"

### Mudanças em `admin.py` schema

```python
class ImportSourceType(str, enum.Enum):
    TCPO = "TCPO"
    # PC removido (deprecated em F2-10)
```

### Testes de endpoint (12 mínimo)

1. POST `/bcu/importar` como admin → 200
2. POST `/bcu/importar` como user comum → 403
3. POST `/bcu/cabecalhos/{id}/ativar` → 200, anterior desativado
4. GET `/bcu/cabecalho-ativo` → retorna ativo
5. GET `/bcu/{cabecalho_id}/mao-obra` → lista
6. POST `/bcu/de-para` válido → 201
7. POST `/bcu/de-para` duplicado → 409
8. POST `/bcu/de-para` com tipo incoerente → 422
9. PATCH `/bcu/de-para/{id}` → 200
10. DELETE `/bcu/de-para/{id}` → 204
11. GET `/bcu/de-para?only_unmapped=true` → lista BaseTcpo sem mapeamento
12. POST `/admin/import/execute` com source_type=PC → 410 Gone

- [ ] **Step 1**: schemas
- [ ] **Step 2**: endpoints `/bcu` (espelha pc_tabelas + adiciona ativar/cabecalho-ativo + de_para)
- [ ] **Step 3**: remover endpoints obsoletos em admin.py + etl_service.parse_converter_datacenter
- [ ] **Step 4**: substituir `pc_tabelas.router` por `bcu.router` em router.py
- [ ] **Step 5**: deletar `pc_tabelas.py` e `pc_tabelas` schema
- [ ] **Step 6**: testes
- [ ] **Step 7**: pytest PASS + commit `feat(f2-10): add /bcu and /bcu/de-para endpoints; deprecate Converter ETL`

---

## Task 5: Backend — refatorar `cpu_custo_service`

**Files:**
- Modify: `app/backend/services/cpu_custo_service.py`
- Modify: `app/backend/tests/unit/test_cpu_custo_service.py`

### Lógica nova

Hoje `CpuCustoService` recebe um `pc_cabecalho_id` e busca custo por matching heurístico. Substituir por:

```python
class CpuCustoService:
    def __init__(self, db: AsyncSession, bcu_cabecalho_id: UUID | None = None):
        self.db = db
        self.bcu_cabecalho_id = bcu_cabecalho_id
        self.de_para_repo = BcuDeParaRepository(db)
        self.bcu_repo = BcuRepository(db)

    async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
        """
        Para cada composicao com insumo_id (FK para BaseTcpo):
          1. lookup De/Para → (bcu_table_type, bcu_item_id)
          2. Se mapeado, buscar custo unitário na bcu.* tabela correspondente
             - MO  → bcu.mao_obra_item.custo_unitario_h
             - EQP → bcu.equipamento_item.aluguel_r_h
             - EPI → bcu.epi_item.custo_unitario
             - FER → bcu.ferramenta_item.preco
          3. Se não mapeado, fallback para BaseTcpo.custo_base + log warning estruturado
          4. Aplicar quantidade_consumo → custo_total_insumo
        """
```

### Testes (5+)

1. Composição com insumo mapeado em De/Para → custo vem do bcu.*
2. Composição com insumo não mapeado → fallback para BaseTcpo.custo_base + warning logado
3. De/Para tipo MO → busca em mao_obra_item.custo_unitario_h
4. De/Para tipo EPI → busca em epi_item.custo_unitario
5. Sem `bcu_cabecalho_id` (None) → todos fallback para BaseTcpo.custo_base

- [ ] **Step 1**: refatorar service (manter assinatura externa idêntica)
- [ ] **Step 2**: ajustar testes existentes que usavam pc_cabecalho_id
- [ ] **Step 3**: pytest PASS + commit `refactor(f2-10): cpu_custo_service resolves costs via bcu_de_para`

---

## Task 6: Frontend — API client + tipos

**Files:**
- Create: `app/frontend/src/shared/services/api/bcuApi.ts`
- Create: `app/frontend/src/shared/services/api/bcuDeParaApi.ts`
- Delete: `app/frontend/src/shared/services/api/pcTabelasApi.ts`

### bcuApi.ts

Espelha `pcTabelasApi.ts` mas:
- Tipos: `BcuCabecalho`, `BcuMaoObraItem`, etc. (sem prefixo Pc)
- Endpoints: `/bcu/*` em vez de `/pc-tabelas/*`
- Adicionar: `ativarCabecalho(id)`, `getCabecalhoAtivo()`, `importar(file)`

### bcuDeParaApi.ts

```typescript
export interface DeParaListItem {
  id: string | null;  // null se BaseTcpo ainda sem mapeamento
  base_tcpo_id: string;
  base_tcpo_codigo: string;
  base_tcpo_descricao: string;
  base_tcpo_tipo_recurso: string;
  bcu_table_type: 'MO' | 'EQP' | 'EPI' | 'FER' | 'MOB' | null;
  bcu_item_id: string | null;
  bcu_item_descricao: string | null;
}

export interface DeParaCreate {
  base_tcpo_id: string;
  bcu_table_type: 'MO' | 'EQP' | 'EPI' | 'FER' | 'MOB';
  bcu_item_id: string;
}

export const bcuDeParaApi = {
  async listar(params?: { only_unmapped?: boolean; search?: string }) { ... },
  async criar(body: DeParaCreate) { ... },
  async atualizar(id: string, body: Omit<DeParaCreate, 'base_tcpo_id'>) { ... },
  async deletar(id: string) { ... },
};
```

- [ ] **Step 1**: bcuApi.ts (rebrand de pcTabelasApi.ts)
- [ ] **Step 2**: bcuDeParaApi.ts (novo)
- [ ] **Step 3**: deletar pcTabelasApi.ts; refatorar `proposalsApi` para `bcu_cabecalho_id` (campo)
- [ ] **Step 4**: tsc OK + commit `feat(f2-10): add bcu and bcuDeParaApi clients`

---

## Task 7: Frontend — UI

**Files:**
- Create: `app/frontend/src/features/bcu/BcuPage.tsx` (rebrand de PcTabelasPage)
- Create: `app/frontend/src/features/bcu/BcuDeParaPage.tsx` (novo)
- Modify: `app/frontend/src/features/admin/UploadTcpoPage.tsx` (remover Converter; renomear PC Tabelas → BCU)
- Modify: `app/frontend/src/features/admin/AdminPage.tsx` (remover opção PC do dropdown)
- Modify: `app/frontend/src/app/router.tsx` (rota `/pc-tabelas` → `/bcu`; nova `/bcu/de-para`)
- Modify: `app/frontend/src/shared/components/layout/navigationConfig.tsx` (label + novo item)
- Delete: `app/frontend/src/features/pc-tabelas/PcTabelasPage.tsx`

### BcuPage

Cópia integral de `PcTabelasPage.tsx` com:
- Imports atualizados (`bcuApi`, tipos `Bcu*`)
- Page title: "BCU — Base de Custos Unitários"
- Adicionar: badge "Ativo" no cabecalho ativo + botão "Ativar" para os inativos
- Adicionar header dropdown se houver múltiplos cabecalhos (default = ativo)
- Empty state: "Nenhuma BCU importada. Acesse Governança → Upload."

### BcuDeParaPage

Layout:
```
┌─────────────────────────────────────────────────────────────┐
│ Filtros: [Buscar] [☐ Apenas não mapeados] [Tipo: ▾]        │
├─────────────────────────────────────────────────────────────┤
│ TCPO (origem)                  │ BCU (destino)              │
├────────────────────────────────┼────────────────────────────┤
│ MO-001  Eletricista Sênior     │ [MO ▾] [Eletricista Nv.3 ▾]│
│ MO-002  Pedreiro               │ [MO ▾] [Pedreiro          ▾]│
│ EQP-001 Britador de Mão        │ [EQP ▾] [Britadeira       ▾]│
│ FER-001 Carriola               │ [FER ▾] [Carrinho de Mão  ▾]│
│ INS-001 Cimento CP-32          │ ⚠️ Sem mapeamento  [+]     │
└────────────────────────────────┴────────────────────────────┘
```

Detalhes:
- Tabela paginada (DataTable)
- Coluna BCU contém 2 selects encadeados: tipo (MO/EQP/EPI/FER/MOB) → item (carregado conforme tipo)
- Salvar inline (debounce 600ms) via `bcuDeParaApi.criar` ou `.atualizar`
- Botão delete (lixeira) por linha mapeada
- Indicador visual: linhas sem mapeamento com fundo amarelo claro
- Header com contador: "147 itens TCPO  |  82 mapeados (56%)  |  65 pendentes"

### UploadTcpoPage — alterações

Remover toda a seção `<Paper>` "Converter em Data Center" (linhas 262-322). Renomear seção "PC Tabelas" para "BCU":
- Título: "Carga da BCU (Base de Custos Unitários)"
- Chip "7 abas" (mantém)
- Botão: `bcuApi.importar(file)` em vez de `pcTabelasApi.importarPlanilha`
- Após sucesso: showMessage com link "Ativar agora" → POST ativar

### AdminPage — alterações

No `<Select>` "Tipo da base", remover `<MenuItem value="PC">`. Manter só TCPO.

### router.tsx

```typescript
const BcuPage = lazy(() => import('../features/bcu/BcuPage').then(m => ({ default: m.BcuPage })));
const BcuDeParaPage = lazy(() => import('../features/bcu/BcuDeParaPage').then(m => ({ default: m.BcuDeParaPage })));

// substituir <Route path="/pc-tabelas" ... />
<Route path="/bcu" element={<BcuPage />} />
<Route path="/bcu/de-para" element={<BcuDeParaPage />} />
```

### navigationConfig.tsx

Renomear item "PC Tabelas" → "BCU" (path `/bcu`). Adicionar item novo "Mapeamento De/Para" (path `/bcu/de-para`, status `active`, visible apenas para admins).

- [ ] **Step 1**: BcuPage (rebrand) + deletar PcTabelasPage
- [ ] **Step 2**: BcuDeParaPage (novo)
- [ ] **Step 3**: UploadTcpoPage: remover Converter, renomear PC → BCU
- [ ] **Step 4**: AdminPage: remover opção PC do dropdown
- [ ] **Step 5**: router + nav config
- [ ] **Step 6**: tsc OK + commit `feat(f2-10): add BcuPage, BcuDeParaPage, unify uploads`

---

## Task 8: Validação final

- [ ] `cd app && python -m pytest backend/tests/ --tb=short` → **200+ PASS, 0 FAIL** (~25 testes novos sobre 179 base de F2-09)
- [ ] `cd app/frontend && npx tsc --noEmit` → **0 erros**
- [ ] Migration 023:
  - `alembic upgrade head` sem erro
  - `\dt public.pc_*` retorna 0 tabelas
  - `\dt bcu.*` retorna 10 tabelas + de_para
  - `SELECT count(*) FROM operacional.propostas WHERE bcu_cabecalho_id IS NOT NULL` = 0 (sem dados ainda)
- [ ] Smoke teste manual:
  - POST `/bcu/importar` com `BCU.xlsx` → 200, cabecalho criado
  - POST `/bcu/cabecalhos/{id}/ativar` → 200, is_ativo=TRUE
  - GET `/bcu/cabecalho-ativo` → retorna o ativo
  - POST `/bcu/de-para` válido → 201
  - GET `/bcu/de-para?only_unmapped=true` → lista BaseTcpo sem entrada
  - GET `/admin/import/execute?source_type=PC` → 410 Gone
- [ ] Frontend smoke:
  - Acessar `/bcu` → vê tabs com dados do cabecalho ativo
  - Acessar `/bcu/de-para` → vê tabela editável
  - Upload em `/upload` (admin) → seção "BCU" funciona; seção "Converter" não existe mais
  - Em `AdminPage`, dropdown "Carga inteligente" só mostra "TCPO"
- [ ] Atualizar `docs/shared/governance/BACKLOG.md` (F2-10 → TESTED)
- [ ] Criar `docs/sprints/F2-10/technical-review/technical-review-2026-04-XX-f2-10.md`
- [ ] Criar `docs/sprints/F2-10/walkthrough/done/walkthrough-F2-10.md`

---

## Self-Review

**Spec coverage:**
- ✅ Schema `bcu` criado, `pc_*` removido
- ✅ De/Para 1:1 manual, com validação de tipo coerente
- ✅ Importação BCU sincroniza `referencia.base_tcpo` (sync bidirecional)
- ✅ Múltiplos cabecalhos suportados; flag `is_ativo` (índice parcial garante 1 ativo)
- ✅ `cpu_custo_service` resolve via De/Para com fallback BaseTcpo
- ✅ UI: BcuPage + BcuDeParaPage + uploads unificados

**Decisões arquiteturais:**
- De/Para é polimórfico (`bcu_table_type` + `bcu_item_id`) sem FK física pois aponta para 5 tabelas distintas. A integridade é garantida no service.
- `codigo_origem` em `bcu.mao_obra_item`/`equipamento_item`/etc. permite re-importação idempotente (UPSERT por codigo) e habilita o sync com `BaseTcpo`.
- Encargos e Mobilização não vão para o De/Para — são valores globais usados em fórmulas (entrarão direto no histograma da proposta em F2-11 como cópia integral).
- Reset autorizado pelo PO (2026-04-27): `pc_*` e dados `etl_carga` são descartados, `bcu.*` nasce vazio. Propostas existentes têm `bcu_cabecalho_id=NULL` e fallback para `BaseTcpo.custo_base`.
- Sprint M7 (Compras/Negociação) congelada em `on-hold`: F2-12..F2-15 não tocam código nesta sprint.

**Critérios de aceite:**
- 200+ pytest PASS, 0 FAIL
- 0 erros tsc
- Migration 023 idempotente (drop pc_*, create bcu.*)
- Schema `bcu` populado via importação BCU.xlsx
- De/Para CRUD funcional com validação de tipo
- CPU resolve custos via De/Para com fallback explícito (warning estruturado)
