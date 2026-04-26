# F2-06: UX Complementar — Edição de PQ, Filtros, Duplicação Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar fluxos pós-importação que hoje exigem retrabalho manual: editar `PqItem` após upload, filtrar a lista de propostas por status/período/busca textual e duplicar uma proposta existente como base de uma nova. Foco majoritariamente frontend com 3 endpoints de apoio.

**Architecture:** Backend ganha 3 endpoints atômicos: `PATCH /pq/itens/{id}` (edição), `POST /propostas/{id}/duplicar` (clone) e parâmetros novos no `GET /propostas/` existente (status, periodo, q). Frontend ganha tabela editável inline em `ProposalImportPage`, barra de filtros em `ProposalsListPage` e modal de duplicação. Tudo em padrões já estabelecidos: TanStack Query + MUI + repos/services existentes.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Pydantic v2, React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Contexto do codebase

Antes de implementar, leia estes arquivos:

- `app/backend/api/v1/endpoints/pq_importacao.py` — onde entra o PATCH de PqItem
- `app/backend/api/v1/endpoints/propostas.py` — onde entra `duplicar` e os filtros
- `app/backend/repositories/pq_item_repository.py` — `get_by_id`, `update_status` (padrão)
- `app/backend/repositories/proposta_repository.py` — `list_by_cliente` (precisa receber filtros)
- `app/backend/services/proposta_service.py` — onde entra `duplicar_proposta`
- `app/backend/schemas/proposta.py` — adicionar `PqItemUpdateRequest`
- `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx` — barra de filtros entra aqui
- `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx` — tabela editável entra aqui após upload
- `app/frontend/src/features/proposals/components/ProposalsTable.tsx` — coluna de ação "Duplicar"
- `app/frontend/src/shared/services/api/proposalsApi.ts` — adicionar `updatePqItem`, `duplicarProposta`, params extras em `list`

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/backend/schemas/proposta.py` | Modificar | `PqItemUpdateRequest` (descricao_original, unidade, quantidade_original) |
| `app/backend/repositories/pq_item_repository.py` | Modificar | `update_dados` (descricao/unidade/qtd) |
| `app/backend/repositories/proposta_repository.py` | Modificar | `list_by_cliente` aceita `status`, `periodo`, `q` |
| `app/backend/services/proposta_service.py` | Modificar | `duplicar_proposta` (clona com novo codigo, status RASCUNHO) |
| `app/backend/api/v1/endpoints/pq_importacao.py` | Modificar | `PATCH /pq/itens/{item_id}` |
| `app/backend/api/v1/endpoints/propostas.py` | Modificar | filtros em GET / + `POST /{id}/duplicar` |
| `app/backend/tests/unit/test_pq_item_edit.py` | Criar | Testes do PATCH |
| `app/backend/tests/unit/test_proposta_duplicar.py` | Criar | Testes da duplicação |
| `app/backend/tests/unit/test_proposta_filtros.py` | Criar | Testes dos filtros |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | `updatePqItem`, `duplicarProposta`, params extras em `list` |
| `app/frontend/src/features/proposals/components/PqItensEditableTable.tsx` | Criar | Tabela editável inline (Material UI + TanStack Query) |
| `app/frontend/src/features/proposals/components/ProposalFiltersBar.tsx` | Criar | Barra com select status, date range, search input |
| `app/frontend/src/features/proposals/components/DuplicarPropostaDialog.tsx` | Criar | Modal de duplicação |
| `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx` | Modificar | Renderizar `PqItensEditableTable` após upload |
| `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx` | Modificar | Renderizar `ProposalFiltersBar` + passar filtros para `list` |
| `app/frontend/src/features/proposals/components/ProposalsTable.tsx` | Modificar | Botão "Duplicar" por linha |

---

## Task 1: Backend — schema PqItemUpdateRequest + repo.update_dados

**Files:**
- Modify: `app/backend/schemas/proposta.py`
- Modify: `app/backend/repositories/pq_item_repository.py`
- Create: `app/backend/tests/unit/test_pq_item_edit.py`

- [ ] **Step 1: Teste**

```python
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.schemas.proposta import PqItemUpdateRequest


def test_pq_item_update_request_aceita_campos_parciais():
    req = PqItemUpdateRequest(descricao_original="Nova descricao")
    assert req.descricao_original == "Nova descricao"
    assert req.quantidade_original is None


def test_pq_item_update_request_quantidade_negativa_falha():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PqItemUpdateRequest(quantidade_original=Decimal("-1"))


@pytest.mark.asyncio
async def test_repo_update_dados_persiste_alteracoes():
    from backend.repositories.pq_item_repository import PqItemRepository
    db = MagicMock()
    db.flush = AsyncMock()
    repo = PqItemRepository(db)
    item = MagicMock()
    item.descricao_original = "antes"
    item.unidade_medida_original = "m"
    item.quantidade_original = Decimal("1")
    await repo.update_dados(item, descricao_original="depois", quantidade_original=Decimal("2.5"))
    assert item.descricao_original == "depois"
    assert item.quantidade_original == Decimal("2.5")
    assert item.unidade_medida_original == "m"
```

- [ ] **Step 2: Schema**

```python
class PqItemUpdateRequest(BaseModel):
    descricao_original: str | None = Field(default=None, min_length=1, max_length=2000)
    unidade_medida_original: str | None = Field(default=None, max_length=20)
    quantidade_original: Decimal | None = Field(default=None, ge=0)
    observacao: str | None = None
```

- [ ] **Step 3: Repo**

```python
async def update_dados(
    self,
    pq_item: PqItem,
    *,
    descricao_original: str | None = None,
    unidade_medida_original: str | None = None,
    quantidade_original: Decimal | None = None,
    observacao: str | None = None,
) -> None:
    if descricao_original is not None:
        pq_item.descricao_original = descricao_original
    if unidade_medida_original is not None:
        pq_item.unidade_medida_original = unidade_medida_original
    if quantidade_original is not None:
        pq_item.quantidade_original = quantidade_original
    if observacao is not None:
        pq_item.observacao = observacao
    await self.db.flush()
```

- [ ] **Step 4: Pytest PASS + commit**

---

## Task 2: Backend — endpoint PATCH /pq/itens/{item_id}

**Files:**
- Modify: `app/backend/api/v1/endpoints/pq_importacao.py`
- Modify: `app/backend/tests/unit/test_pq_item_edit.py`

- [ ] **Step 1: Teste de endpoint**

```python
@pytest.mark.asyncio
async def test_patch_pq_item_atualiza_descricao():
    from unittest.mock import patch
    from backend.api.v1.endpoints.pq_importacao import editar_pq_item
    from backend.schemas.proposta import PqItemUpdateRequest

    proposta = MagicMock()
    proposta.id = uuid4()
    proposta.cliente_id = uuid4()
    item = MagicMock()
    item.proposta_id = proposta.id

    with (
        patch("backend.api.v1.endpoints.pq_importacao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.pq_importacao.PqItemRepository") as MockIR,
        patch("backend.api.v1.endpoints.pq_importacao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockIR.return_value.get_by_id = AsyncMock(return_value=item)
        MockIR.return_value.update_dados = AsyncMock()
        db = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        body = PqItemUpdateRequest(descricao_original="Nova", quantidade_original=Decimal("3"))
        result = await editar_pq_item(
            proposta_id=proposta.id, item_id=uuid4(), body=body,
            current_user=MagicMock(), db=db,
        )
        assert result is not None
```

- [ ] **Step 2: Endpoint**

```python
@router.patch("/itens/{item_id}", response_model=PqItemResponse)
async def editar_pq_item(
    proposta_id: UUID,
    item_id: UUID,
    body: PqItemUpdateRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqItemResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    repo = PqItemRepository(db)
    item = await repo.get_by_id(item_id)
    if item is None or item.proposta_id != proposta_id:
        raise NotFoundError("PqItem", str(item_id))

    await repo.update_dados(
        item,
        descricao_original=body.descricao_original,
        unidade_medida_original=body.unidade_medida_original,
        quantidade_original=body.quantidade_original,
        observacao=body.observacao,
    )
    await db.commit()
    await db.refresh(item)
    return PqItemResponse.model_validate(item)
```

Importar `PqItemUpdateRequest` no topo. Pytest PASS. Commit.

---

## Task 3: Backend — duplicar_proposta service + endpoint

**Files:**
- Modify: `app/backend/services/proposta_service.py`
- Modify: `app/backend/api/v1/endpoints/propostas.py`
- Create: `app/backend/tests/unit/test_proposta_duplicar.py`

Estratégia: clonar `Proposta` (novo codigo gerado pelo padrão existente, status RASCUNHO, totais zerados) e clonar `PqItens` resetando `match_status=PENDENTE` e limpando `servico_match_id/tipo`. **Não** clonar `PropostaItem` (CPU) nem composições — usuário regera via match → CPU.

- [ ] **Step 1: Teste**

```python
@pytest.mark.asyncio
async def test_duplicar_proposta_clona_pq_itens_resetando_match():
    from backend.services.proposta_service import PropostaService
    from backend.models.enums import StatusMatch

    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    original = MagicMock()
    original.id = uuid4()
    original.cliente_id = uuid4()
    original.codigo = "PROP-2026-0001"
    original.titulo = "Original"
    original.descricao = "..."
    pq_item = MagicMock()
    pq_item.descricao_original = "x"
    pq_item.unidade_medida_original = "m"
    pq_item.quantidade_original = Decimal("1")
    pq_item.codigo_original = "001"
    pq_item.linha_planilha = 1
    pq_item.observacao = None

    svc = PropostaService(db)
    svc.proposta_repo.get_by_id = AsyncMock(return_value=original)
    svc.proposta_repo.count_by_code_prefix = AsyncMock(return_value=1)
    svc.pq_item_repo.list_by_proposta = AsyncMock(return_value=[pq_item])
    svc.pq_item_repo.create_batch = AsyncMock(side_effect=lambda items: items)

    nova = await svc.duplicar_proposta(original.id, criado_por_id=uuid4())
    assert nova.codigo != original.codigo
    assert nova.cliente_id == original.cliente_id
```

- [ ] **Step 2: Service** — adicionar método `duplicar_proposta(proposta_id, criado_por_id) -> Proposta`. Reutilizar lógica de geração de código. PqItens resetam `match_status=PENDENTE`.

- [ ] **Step 3: Endpoint** em `propostas.py`:

```python
@router.post("/{proposta_id}/duplicar", response_model=PropostaResponse, status_code=201)
async def duplicar_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    original = await PropostaRepository(db).get_by_id(proposta_id)
    if not original:
        raise NotFoundError("Proposta", str(proposta_id))
    await require_cliente_access(original.cliente_id, current_user, db)

    nova = await PropostaService(db).duplicar_proposta(proposta_id, criado_por_id=current_user.id)
    return PropostaResponse.model_validate(nova)
```

- [ ] **Step 4: Pytest PASS + commit**

---

## Task 4: Backend — filtros em GET /propostas

**Files:**
- Modify: `app/backend/repositories/proposta_repository.py`
- Modify: `app/backend/api/v1/endpoints/propostas.py`
- Create: `app/backend/tests/unit/test_proposta_filtros.py`

- [ ] **Step 1: Teste** com mock — `list_by_cliente` aceita `status: StatusProposta | None`, `data_inicial: datetime | None`, `data_final: datetime | None`, `q: str | None` (busca em codigo/titulo, ILIKE).

- [ ] **Step 2: Repo** — adicionar filtros condicionais:

```python
async def list_by_cliente(
    self,
    cliente_id: UUID,
    *,
    offset: int = 0,
    limit: int = 100,
    status: StatusProposta | None = None,
    data_inicial: datetime | None = None,
    data_final: datetime | None = None,
    q: str | None = None,
) -> tuple[list[Proposta], int]:
    filters = [
        Proposta.cliente_id == cliente_id,
        Proposta.deleted_at.is_(None),
    ]
    if status is not None:
        filters.append(Proposta.status == status)
    if data_inicial is not None:
        filters.append(Proposta.created_at >= data_inicial)
    if data_final is not None:
        filters.append(Proposta.created_at <= data_final)
    if q:
        like = f"%{q}%"
        filters.append(or_(Proposta.codigo.ilike(like), Proposta.titulo.ilike(like)))
    ...
```

- [ ] **Step 3: Endpoint** — aceitar query params `status`, `data_inicial`, `data_final`, `q`.

- [ ] **Step 4: Pytest PASS + commit**

---

## Task 5: Frontend — proposalsApi (3 métodos)

**Files:**
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts`

- [ ] **Step 1**: adicionar tipos e métodos.

```typescript
export interface PqItemUpdateRequest {
  descricao_original?: string;
  unidade_medida_original?: string;
  quantidade_original?: string;
  observacao?: string;
}

export interface PropostaListFilters {
  status?: StatusProposta;
  data_inicial?: string;
  data_final?: string;
  q?: string;
}

// Sobrescrever list:
async list(clienteId: string, page = 1, pageSize = 20, filters: PropostaListFilters = {}) {
  const params: Record<string, string | number> = { cliente_id: clienteId, page, page_size: pageSize };
  if (filters.status) params.status = filters.status;
  if (filters.data_inicial) params.data_inicial = filters.data_inicial;
  if (filters.data_final) params.data_final = filters.data_final;
  if (filters.q) params.q = filters.q;
  const response = await apiClient.get<PaginatedResponse<PropostaResponse>>('/propostas/', { params });
  return response.data;
},

async updatePqItem(propostaId: string, itemId: string, payload: PqItemUpdateRequest): Promise<PqItemResponse> {
  const response = await apiClient.patch<PqItemResponse>(`/propostas/${propostaId}/pq/itens/${itemId}`, payload);
  return response.data;
},

async duplicarProposta(propostaId: string): Promise<PropostaResponse> {
  const response = await apiClient.post<PropostaResponse>(`/propostas/${propostaId}/duplicar`);
  return response.data;
},
```

- [ ] **Step 2**: tsc --noEmit OK + commit.

---

## Task 6: Frontend — PqItensEditableTable (inline edit)

**Files:**
- Create: `app/frontend/src/features/proposals/components/PqItensEditableTable.tsx`

Padrão: linha em modo de leitura padrão; ao clicar no botão de edição, troca para inputs (TextField), com botões salvar/cancelar. Mutate via `proposalsApi.updatePqItem`. Invalidar query `['pq-itens', propostaId]`.

Colunas: Linha, Código, Descrição, Unidade, Qtd, Status, Ações (editar/salvar/cancelar).

Controle de estado: `editingId: string | null`; ao salvar, mantém otimismo via TanStack `useMutation` e invalida.

- [ ] **Step 1**: criar componente (~180 linhas TypeScript).

- [ ] **Step 2**: tsc OK + commit.

---

## Task 7: Frontend — ProposalFiltersBar + integração ProposalsListPage

**Files:**
- Create: `app/frontend/src/features/proposals/components/ProposalFiltersBar.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx`

Componentes MUI: `Select` para status (com opção "Todos"), 2 `DatePicker` (período), `TextField` debounced (300ms) para busca textual. Emite `onChange(filters: PropostaListFilters)`.

ProposalsListPage:
- Adicionar estado `filters` no nível da página.
- Renderizar `<ProposalFiltersBar value={filters} onChange={setFilters} />` acima da `<ProposalsTable />`.
- Passar `filters` ao `proposalsApi.list` via queryKey.
- Resetar `page` para 1 quando filtros mudam.

- [ ] **Step 1**: criar `ProposalFiltersBar` (~120 linhas).
- [ ] **Step 2**: integrar em `ProposalsListPage`.
- [ ] **Step 3**: tsc OK + commit.

---

## Task 8: Frontend — DuplicarPropostaDialog + botão "Duplicar"

**Files:**
- Create: `app/frontend/src/features/proposals/components/DuplicarPropostaDialog.tsx`
- Modify: `app/frontend/src/features/proposals/components/ProposalsTable.tsx`

Modal MUI `Dialog`: confirmação "Duplicar a proposta {codigo}?" com checkbox opcional "Manter mesmo titulo" (default off). Ao confirmar: `useMutation(duplicarProposta)`, navegar para `/propostas/{novaId}` ao sucesso, invalidar `['propostas', clienteId]`.

ProposalsTable: nova coluna "Ações" com IconButton `<ContentCopyOutlinedIcon />` que abre o dialog.

- [ ] **Step 1**: criar `DuplicarPropostaDialog`.
- [ ] **Step 2**: adicionar coluna em `ProposalsTable`.
- [ ] **Step 3**: tsc OK + commit.

---

## Task 9: Frontend — wire PqItensEditableTable em ProposalImportPage

**Files:**
- Modify: `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx`

Após o bloco de upload bem-sucedido, mostrar `<PqItensEditableTable propostaId={id!} />` que carrega via `useQuery(['pq-itens', id], () => proposalsApi.listPqItens(id!))`.

- [ ] **Step 1**: adicionar import e Paper com a tabela.
- [ ] **Step 2**: tsc OK + commit final.

---

## Task 10: Validação final

- [ ] `cd app && python -m pytest backend/tests/ --tb=short` — esperado **130+ PASS, 0 FAIL**
- [ ] `cd app/frontend && npx tsc --noEmit` — esperado **0 erros**
- [ ] Manual smoke (se possível): upload PQ → editar item → duplicar proposta → verificar status RASCUNHO em nova proposta

---

## Self-Review

**Spec coverage:**
- ✅ Edição de PQ pós-importação — `PATCH /pq/itens/{id}` + `PqItensEditableTable`
- ✅ Filtros de proposta (status/período/busca) — query params + `ProposalFiltersBar`
- ✅ Duplicação de proposta — `POST /propostas/{id}/duplicar` + dialog

**Não-objetivos:** sem reordenação drag-and-drop de PqItens, sem bulk-edit, sem auditoria de alterações (fica em F2-XX futura).

**Critérios de aceite:**
- 130+ pytest PASS, 0 FAIL
- 0 erros tsc
- Edição persiste descricao/qtd/unidade
- Filtros combináveis (status + período + busca)
- Duplicação cria nova proposta em RASCUNHO sem CPU
