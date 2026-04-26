# F2-07: Tabelas de Recursos + Motor 4 Camadas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Formalizar e documentar o motor de busca em **4 camadas** (histórico do cliente → código exato → fuzzy pg_trgm → semântico pgvector) hoje implícito no `BuscaService`/`PqMatchService`, e produzir agregação por recurso (`PropostaResumoRecurso`) gerada automaticamente ao chamar `gerar-cpu`. Entregável dual: clareza arquitetural (documento + early-exit explícito) + dado novo (resumo de recursos por proposta).

**Architecture:** (1) Refatorar `PqMatchService` para chamar 4 camadas em ordem com early-exit e logging estruturado por camada. (2) Criar tabela `operacional.proposta_resumo_recursos` (migration 020) com colunas `id, proposta_id, tipo_recurso, descricao_insumo, unidade_medida, quantidade_total, custo_total`. (3) `cpu_geracao_service.gerar_cpu_para_proposta` passa a popular o resumo após explosão. (4) Endpoint `GET /propostas/{id}/recursos` retorna agregado para frontend e Power Query consumir. Frontend ganha página leve `ProposalResourcesPage` listando o agregado.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, pg_trgm, pgvector, sentence-transformers, React 18, TypeScript, MUI v6, pytest-asyncio

---

## Pré-requisito de leitura (obrigatório antes de codar)

Esta sprint depende fortemente de análise documental. **Leia na ordem antes de começar:**

1. `docs/shared/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md` — entidades e fluxo end-to-end
2. `docs/shared/research/RESEARCH_CORE_FEATURES.md` — features core e contexto de negócio
3. `docs/shared/superpowers/plans/roadmap/ANALISE_RESEARCH_2026-04-23.md` — análise de gaps
4. `docs/shared/superpowers/plans/roadmap/ROADMAP.md` (Milestone 6, Fase 6.5) — escopo desta sprint
5. `app/backend/services/busca_service.py` — Fase 0/1/2/3 já implementadas no `BuscaService`
6. `app/backend/services/pq_match_service.py` — match atual em PQ
7. `app/backend/services/cpu_geracao_service.py` — onde entra o `gerar_resumo_recursos`
8. `app/backend/models/proposta.py` — `PropostaItemComposicao.tipo_recurso`
9. `app/backend/models/enums.py` — `TipoRecurso` (MO/INSUMO/FERRAMENTA/EQUIPAMENTO/SERVICO)
10. `app/backend/repositories/historico_repository.py` — para a Camada 1 (histórico do cliente)

**Após a leitura, antes de codar, escreva mentalmente:**
- Qual o critério de early-exit em cada camada (threshold de confiança)?
- O `BuscaService` já tem 4 fases? O `PqMatchService` chama o `BuscaService`?
- Onde está hoje a lógica de match em PQ? Está duplicada com o `BuscaService`?

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/backend/models/proposta.py` | Modificar | Adicionar `PropostaResumoRecurso` |
| `app/alembic/versions/020_proposta_resumo_recursos.py` | Criar | Migration: tabela `operacional.proposta_resumo_recursos` |
| `app/backend/repositories/proposta_resumo_recurso_repository.py` | Criar | CRUD básico + `list_by_proposta`, `replace_for_proposta` |
| `app/backend/services/pq_match_service.py` | Refatorar | Tornar 4 camadas explícitas com early-exit e logging por camada |
| `app/backend/services/cpu_geracao_service.py` | Modificar | Após explosão, chamar `gerar_resumo_recursos(proposta_id)` |
| `app/backend/services/proposta_resumo_recurso_service.py` | Criar | `gerar_resumo_recursos`: agrega composições por (tipo_recurso, descricao_insumo, unidade) |
| `app/backend/schemas/proposta.py` | Modificar | `PropostaResumoRecursoResponse` |
| `app/backend/api/v1/endpoints/proposta_recursos.py` | Criar | `GET /propostas/{id}/recursos` |
| `app/backend/api/v1/router.py` | Modificar | Registrar router |
| `app/backend/tests/unit/test_pq_match_4_camadas.py` | Criar | Cobertura das 4 camadas com early-exit |
| `app/backend/tests/unit/test_proposta_resumo_recurso_service.py` | Criar | Agregação correta por (tipo, descricao, unidade) |
| `app/backend/tests/unit/test_proposta_recursos_endpoint.py` | Criar | Endpoint feliz + 404 |
| `docs/shared/analysis/MOTOR_BUSCA_4_CAMADAS.md` | Criar | Documento técnico oficializando as 4 camadas |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | `listResumoRecursos` |
| `app/frontend/src/features/proposals/pages/ProposalResourcesPage.tsx` | Criar | Tabela agregada por TipoRecurso (com totais por grupo) |
| `app/frontend/src/features/proposals/routes.tsx` | Modificar | Rota `/propostas/:id/recursos` |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificar | Botão "Ver Recursos" |

---

## Task 1: Documento técnico — formalizar as 4 camadas

**File:** `docs/shared/analysis/MOTOR_BUSCA_4_CAMADAS.md`

Conteúdo obrigatório:
1. **Camada 1 — Histórico Confirmado do Cliente:** lookup em `associacao_inteligente` com `cliente_id + texto_normalizado`. Status `CONSOLIDADA` → circuit-break (confiança 1.0). `VALIDADA/SUGERIDA` → retorna e fortalece. Threshold: presença direta basta.
2. **Camada 2 — Código Exato:** match de `codigo_original` em `base_tcpo.codigo` ou `itens_proprios.codigo`. Threshold: igualdade case-insensitive.
3. **Camada 3 — Fuzzy pg_trgm:** `similarity(descricao_normalizada, candidato) >= 0.65`. Ranking por `similarity DESC`.
4. **Camada 4 — Semântico pgvector:** `embedding <=> query_embedding` (cosine distance) com threshold `0.30`. Reranking por `1 - distance`.

Para cada camada documentar: pré-requisito (cliente_id obrigatório?), entrada normalizada, output (1 ou N candidatos), critério de early-exit, custo computacional, fallback.

Incluir diagrama em ASCII do fluxo + tabela de mapeamento camada → função em código.

- [ ] **Step 1: Escrever documento (~250 linhas)**
- [ ] **Step 2: Commit** `docs(f2-07): formalize 4-layer search engine architecture`

---

## Task 2: Backend — model + migration PropostaResumoRecurso

**Files:**
- Modify: `app/backend/models/proposta.py`
- Create: `app/alembic/versions/020_proposta_resumo_recursos.py`

Schema da tabela `operacional.proposta_resumo_recursos`:

| Coluna | Tipo | Notas |
|---|---|---|
| id | UUID PK | `default uuid4` |
| proposta_id | UUID FK → propostas | `ondelete=CASCADE`, indexado |
| tipo_recurso | enum | `tipo_recurso_enum` (reusar) |
| descricao_insumo | TEXT | |
| unidade_medida | VARCHAR(20) | |
| quantidade_total | NUMERIC(15,4) | |
| custo_unitario_medio | NUMERIC(15,4) NULL | média ponderada |
| custo_total | NUMERIC(15,4) | |
| created_at / updated_at | timestamp | TimestampMixin |

Constraint única: `(proposta_id, tipo_recurso, descricao_insumo, unidade_medida)`.

- [ ] **Step 1: Model**

```python
class PropostaResumoRecurso(Base, TimestampMixin):
    __tablename__ = "proposta_resumo_recursos"
    __table_args__ = (
        UniqueConstraint("proposta_id", "tipo_recurso", "descricao_insumo", "unidade_medida",
                         name="uq_resumo_recurso_proposta"),
        {"schema": "operacional"},
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tipo_recurso: Mapped[TipoRecurso] = mapped_column(
        SAEnum(TipoRecurso, name="tipo_recurso_enum", create_type=False), nullable=False,
    )
    descricao_insumo: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade_total: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    custo_unitario_medio: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_total: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
```

- [ ] **Step 2: Migration 020** — seguir o padrão de `019_recursao_composicao.py`. Não precisa criar enum (`tipo_recurso_enum` já existe).

- [ ] **Step 3: Aplicar migration localmente** (alembic upgrade head) — opcional se DB local existir; senão pular.

- [ ] **Step 4: Commit** `feat(f2-07): add PropostaResumoRecurso model and migration 020`

---

## Task 3: Backend — repository + service de resumo

**Files:**
- Create: `app/backend/repositories/proposta_resumo_recurso_repository.py`
- Create: `app/backend/services/proposta_resumo_recurso_service.py`
- Create: `app/backend/tests/unit/test_proposta_resumo_recurso_service.py`

Repository: `list_by_proposta(proposta_id) -> list[PropostaResumoRecurso]`, `replace_for_proposta(proposta_id, items: list[PropostaResumoRecurso])` (delete + insert em transação para garantir consistência ao re-gerar CPU).

Service `gerar_resumo_recursos(proposta_id)`:
1. Listar todos os `PropostaItem` da proposta.
2. Para cada `PropostaItem`, listar `PropostaItemComposicao`.
3. Agregar em dict com chave `(tipo_recurso, descricao_insumo, unidade_medida)`:
   - somar `quantidade_consumo * proposta_item.quantidade` em `quantidade_total`
   - somar `custo_total_insumo * proposta_item.quantidade` em `custo_total`
   - `custo_unitario_medio = custo_total / quantidade_total` se `quantidade_total > 0`
4. Materializar como lista de `PropostaResumoRecurso` e chamar `replace_for_proposta`.

- [ ] **Step 1: Testes** (3 testes mínimos: agregação simples, recursos diferentes, ignorar `tipo_recurso=None`).

- [ ] **Step 2: Implementar repo + service.**

- [ ] **Step 3: Pytest PASS + commit**

---

## Task 4: Backend — refatorar PqMatchService nas 4 camadas explícitas

**Files:**
- Modify: `app/backend/services/pq_match_service.py`
- Create: `app/backend/tests/unit/test_pq_match_4_camadas.py`

Objetivo: tornar as camadas **explícitas** no código (mesmo que algumas já existam), com:
- método privado `_camada_1_historico(item, cliente_id)`
- método privado `_camada_2_codigo_exato(item, cliente_id)`
- método privado `_camada_3_fuzzy(item)`
- método privado `_camada_4_semantico(item)`
- função orquestradora `_aplicar_4_camadas(item, cliente_id) -> tuple[match, camada_origem]`
- early-exit em cada camada quando confiança >= threshold
- logging estruturado: `logger.info("match_layer", layer=N, item_id=..., found=True/False, confidence=...)`

Threshold por camada (defaults — confirmar no código existente):
- Camada 1: presença → confiança = 1.0 se CONSOLIDADA, 0.95 se VALIDADA
- Camada 2: igualdade → confiança 0.99
- Camada 3: similarity >= 0.65
- Camada 4: 1 - distance >= 0.70

**Comportamento atual deve ser preservado** — esta é refatoração, não mudança funcional. Validar com regressão.

- [ ] **Step 1: Testes** com mocks isolando cada camada (5 testes: cada camada isolada + uma cascata completa).

- [ ] **Step 2: Refactor.**

- [ ] **Step 3: Rodar suite completa** — esperado mesmo número de testes anteriores ainda passando.

- [ ] **Step 4: Commit** `refactor(f2-07): explicit 4-layer engine in PqMatchService with early-exit`

---

## Task 5: Backend — integrar resumo em gerar_cpu + endpoint GET /recursos

**Files:**
- Modify: `app/backend/services/cpu_geracao_service.py`
- Modify: `app/backend/schemas/proposta.py`
- Create: `app/backend/api/v1/endpoints/proposta_recursos.py`
- Modify: `app/backend/api/v1/router.py`
- Create: `app/backend/tests/unit/test_proposta_recursos_endpoint.py`

- [ ] **Step 1**: ao final de `gerar_cpu_para_proposta`, antes do `db.commit()`, chamar `await PropostaResumoRecursoService(self.db).gerar_resumo_recursos(proposta_id)`.

- [ ] **Step 2**: Schema `PropostaResumoRecursoResponse` — espelha o model com `from_attributes=True`.

- [ ] **Step 3**: Endpoint:

```python
@router.get("/recursos", response_model=list[PropostaResumoRecursoResponse])
async def listar_recursos(
    proposta_id: UUID,
    tipo_recurso: TipoRecurso | None = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropostaResumoRecursoResponse]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)
    items = await PropostaResumoRecursoRepository(db).list_by_proposta(proposta_id, tipo_recurso=tipo_recurso)
    return [PropostaResumoRecursoResponse.model_validate(i) for i in items]
```

- [ ] **Step 4: Pytest PASS + commit**

---

## Task 6: Frontend — proposalsApi + ProposalResourcesPage

**Files:**
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts`
- Create: `app/frontend/src/features/proposals/pages/ProposalResourcesPage.tsx`
- Modify: `app/frontend/src/features/proposals/routes.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`

- [ ] **Step 1**: tipo + método em `proposalsApi`:

```typescript
export type TipoRecurso = 'MO' | 'INSUMO' | 'FERRAMENTA' | 'EQUIPAMENTO' | 'SERVICO';

export interface PropostaResumoRecursoResponse {
  id: string;
  proposta_id: string;
  tipo_recurso: TipoRecurso;
  descricao_insumo: string;
  unidade_medida: string;
  quantidade_total: string;
  custo_unitario_medio: string | null;
  custo_total: string;
  created_at: string;
  updated_at: string;
}

async listResumoRecursos(propostaId: string, tipoRecurso?: TipoRecurso) {
  const params = tipoRecurso ? { tipo_recurso: tipoRecurso } : undefined;
  const response = await apiClient.get<PropostaResumoRecursoResponse[]>(
    `/propostas/${propostaId}/recursos`, { params },
  );
  return response.data;
},
```

- [ ] **Step 2**: `ProposalResourcesPage.tsx` — agrupa por `tipo_recurso`, exibe Accordion por grupo com tabela interna (descricao, unidade, qtd, custo unitário, custo total). Subtotal por grupo no header do Accordion.

- [ ] **Step 3**: rota `/propostas/:id/recursos` em `routes.tsx`.

- [ ] **Step 4**: botão "Ver Recursos" em `ProposalDetailPage` (desabilitado em RASCUNHO).

- [ ] **Step 5**: tsc OK + commit.

---

## Task 7: Validação final

- [ ] `cd app && python -m pytest backend/tests/ --tb=short` → **140+ PASS, 0 FAIL**
- [ ] `cd app/frontend && npx tsc --noEmit` → **0 erros**
- [ ] Verificar que regressão de match (sprints anteriores) ainda passa após refator.
- [ ] Documento `MOTOR_BUSCA_4_CAMADAS.md` revisado e claro.

---

## Self-Review

**Spec coverage:**
- ✅ 4 camadas explícitas com early-exit e logging — `PqMatchService` refatorado
- ✅ Documento oficial — `MOTOR_BUSCA_4_CAMADAS.md`
- ✅ `PropostaResumoRecurso` populado em `gerar-cpu`
- ✅ Endpoint `GET /propostas/{id}/recursos` (com filtro opcional por tipo)
- ✅ Frontend: página de recursos agrupada por tipo

**Decisões arquiteturais:**
- Resumo é regerado a cada `gerar-cpu` (replace estratégia, não merge) → garante consistência sem lock complexo.
- Threshold da Camada 4 (semântico) configurável por env var não está no escopo (default 0.70 hardcoded).
- Não exposição da Camada 1 ao orçamentista — é silenciosa, fortalece histórico automaticamente.

**Critérios de aceite finais:**
- 140+ pytest PASS, 0 FAIL
- 0 erros tsc
- Migration 020 aplicada sem erro
- Resumo gerado automaticamente após cada gerar-cpu
- Documento das 4 camadas existe e é referenciado no `ROADMAP.md`
