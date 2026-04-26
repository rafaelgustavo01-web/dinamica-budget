# F2-04: CPU Detalhada — Breakdown de Insumos e BDI Dinâmico Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expor via API o breakdown completo de insumos por item de CPU (material, MO, equipamento) e permitir que o BDI seja salvo por proposta e recalculado dinamicamente sem regerar toda a CPU do zero.

**Architecture:** Três adições ao backend: (1) endpoint `GET /cpu/itens/{item_id}/composicoes` que retorna a lista de `PropostaItemComposicao` com custo por insumo; (2) coluna `percentual_bdi` na tabela `proposta_itens` + migration 019; (3) endpoint `POST /cpu/recalcular-bdi` que aplica novo BDI sobre os `PropostaItem` já gerados sem re-explodir composições. O frontend da CPU page existente é desbloqueado e passa a consumir os dados reais.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic, pytest-asyncio, React 18, TypeScript, MUI v6, TanStack Query v5

---

## Contexto do codebase

Antes de implementar, leia estes arquivos:

- `app/backend/models/proposta.py` — modelos `PropostaItem` e `PropostaItemComposicao`
- `app/backend/schemas/proposta.py` — `CpuItemResponse` existente (linhas 72-96)
- `app/backend/services/cpu_geracao_service.py` — `gerar_cpu_para_proposta`, `listar_cpu_itens`, `_agrupar_custos`
- `app/backend/api/v1/endpoints/cpu_geracao.py` — endpoints existentes `/gerar` e `/itens`
- `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` — página atual bloqueada com ContractNotice
- `app/frontend/src/features/proposals/components/CpuTable.tsx` — tabela de CPU atual (básica)
- `app/alembic/versions/018_pq_layout_cliente.py` — padrão de migration a seguir

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/backend/models/proposta.py` | Modificar | Adicionar `percentual_bdi` em `PropostaItem` |
| `app/alembic/versions/019_proposta_item_bdi.py` | Criar | Migration: coluna `percentual_bdi` em `proposta_itens` |
| `app/backend/schemas/proposta.py` | Modificar | Adicionar `ComposicaoDetalheResponse`, `RecalcularBdiRequest`, `RecalcularBdiResponse` |
| `app/backend/repositories/proposta_item_composicao_repository.py` | Modificar | Adicionar `list_by_proposta_item` |
| `app/backend/services/cpu_geracao_service.py` | Modificar | Adicionar `recalcular_bdi`, `listar_composicoes_item` |
| `app/backend/api/v1/endpoints/cpu_geracao.py` | Modificar | Adicionar 2 novos endpoints |
| `app/backend/tests/unit/test_cpu_bdi_breakdown.py` | Criar | Testes unitários |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | Adicionar `listCpuItens`, `getComposicoes`, `recalcularBdi` |
| `app/frontend/src/features/proposals/components/CpuTable.tsx` | Modificar | Adicionar coluna de breakdown + accordion de insumos |
| `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` | Modificar | Desbloquear, consumir API real, BDI dinâmico funcional |

---

## Task 1: Model — coluna percentual_bdi em PropostaItem + migration 019

**Files:**
- Modify: `app/backend/models/proposta.py`
- Create: `app/alembic/versions/019_proposta_item_bdi.py`

O modelo `PropostaItem` já tem `percentual_indireto` (linha 164) que armazena o BDI aplicado no momento da geração. Renomear seria breaking change. Vamos usar `percentual_bdi` como alias de escrita persistida separada, mas na prática `percentual_indireto` já serve. A migration vai garantir que a coluna existe com valor padrão 0.

Na verdade, lendo o model: `percentual_indireto: Mapped[Decimal | None]` — já existe e já é preenchida em `cpu_geracao_service.py` linha 70: `item.percentual_indireto = percentual_bdi`. Ou seja, a coluna já existe. A sprint só precisa persistir o BDI na `Proposta` para que o usuário não precise redigitá-lo.

- [ ] **Step 1: Escrever teste que falha**

Crie `app/backend/tests/unit/test_cpu_bdi_breakdown.py`:

```python
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.schemas.proposta import (
    ComposicaoDetalheResponse,
    RecalcularBdiRequest,
    RecalcularBdiResponse,
)


def test_composicao_detalhe_response_schema():
    data = {
        "id": uuid4(),
        "proposta_item_id": uuid4(),
        "descricao_insumo": "Pedreiro",
        "unidade_medida": "h",
        "quantidade_consumo": Decimal("8.0"),
        "custo_unitario_insumo": Decimal("45.00"),
        "custo_total_insumo": Decimal("360.00"),
        "tipo_recurso": "MO",
        "nivel": 1,
        "e_composicao": False,
        "fonte_custo": "pc_tabela",
    }
    resp = ComposicaoDetalheResponse(**data)
    assert resp.descricao_insumo == "Pedreiro"
    assert resp.custo_total_insumo == Decimal("360.00")


def test_recalcular_bdi_request_schema():
    req = RecalcularBdiRequest(percentual_bdi=Decimal("28.5"))
    assert req.percentual_bdi == Decimal("28.5")


def test_recalcular_bdi_response_schema():
    resp = RecalcularBdiResponse(
        proposta_id=str(uuid4()),
        percentual_bdi=Decimal("28.5"),
        total_direto=Decimal("100000.00"),
        total_indireto=Decimal("28500.00"),
        total_geral=Decimal("128500.00"),
        itens_recalculados=15,
    )
    assert resp.itens_recalculados == 15
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py -v
```
Esperado: `ImportError` — schemas não existem ainda.

- [ ] **Step 3: Implementar os schemas**

Em `app/backend/schemas/proposta.py`, ao final do arquivo, adicionar:

```python
class ComposicaoDetalheResponse(BaseModel):
    id: UUID
    proposta_item_id: UUID
    descricao_insumo: str
    unidade_medida: str
    quantidade_consumo: Decimal
    custo_unitario_insumo: Decimal | None
    custo_total_insumo: Decimal | None
    tipo_recurso: str | None
    nivel: int
    e_composicao: bool
    fonte_custo: str | None

    model_config = ConfigDict(from_attributes=True)


class RecalcularBdiRequest(BaseModel):
    percentual_bdi: Decimal = Field(ge=0, le=100)


class RecalcularBdiResponse(BaseModel):
    proposta_id: str
    percentual_bdi: Decimal
    total_direto: Decimal
    total_indireto: Decimal
    total_geral: Decimal
    itens_recalculados: int
```

Verificar que `Field` já está importado de pydantic (linha 5 de `proposta.py` — já está).

- [ ] **Step 4: Rodar e confirmar PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py::test_composicao_detalhe_response_schema backend/tests/unit/test_cpu_bdi_breakdown.py::test_recalcular_bdi_request_schema backend/tests/unit/test_cpu_bdi_breakdown.py::test_recalcular_bdi_response_schema -v
```
Esperado: 3 PASS.

- [ ] **Step 5: Ler o modelo PropostaItemComposicao para confirmar campos**

```bash
cd app && python -c "
from backend.models.proposta import PropostaItemComposicao
for col in PropostaItemComposicao.__table__.columns:
    print(col.name, col.type)
"
```
Esperado: lista incluindo `descricao_insumo`, `custo_unitario_insumo`, `custo_total_insumo`, `tipo_recurso`, `nivel`, `e_composicao`.

- [ ] **Step 6: Commit**

```bash
git add app/backend/schemas/proposta.py app/backend/tests/unit/test_cpu_bdi_breakdown.py
git commit -m "feat(f2-04): add ComposicaoDetalheResponse, RecalcularBdiRequest/Response schemas"
```

---

## Task 2: Repository — list_by_proposta_item em PropostaItemComposicaoRepository

**Files:**
- Modify: `app/backend/repositories/proposta_item_composicao_repository.py`

- [ ] **Step 1: Ler o repositório existente**

```bash
cd app && cat backend/repositories/proposta_item_composicao_repository.py
```
Anote os métodos já existentes.

- [ ] **Step 2: Escrever teste**

Adicionar em `app/backend/tests/unit/test_cpu_bdi_breakdown.py`:

```python
@pytest.mark.asyncio
async def test_list_composicoes_by_proposta_item():
    from backend.repositories.proposta_item_composicao_repository import (
        PropostaItemComposicaoRepository,
    )
    from backend.models.proposta import PropostaItemComposicao

    comp = MagicMock(spec=PropostaItemComposicao)
    comp.proposta_item_id = uuid4()

    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [comp]
    db.execute = AsyncMock(return_value=mock_result)

    repo = PropostaItemComposicaoRepository(db)
    result = await repo.list_by_proposta_item(comp.proposta_item_id)
    assert len(result) == 1
```

- [ ] **Step 3: Rodar e confirmar que falha**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py::test_list_composicoes_by_proposta_item -v
```
Esperado: `AttributeError` — método não existe.

- [ ] **Step 4: Implementar o método**

Em `app/backend/repositories/proposta_item_composicao_repository.py`, adicionar ao final da classe:

```python
async def list_by_proposta_item(self, proposta_item_id: UUID) -> list[PropostaItemComposicao]:
    from sqlalchemy import select
    from backend.models.proposta import PropostaItemComposicao
    result = await self.db.execute(
        select(PropostaItemComposicao)
        .where(PropostaItemComposicao.proposta_item_id == proposta_item_id)
        .order_by(PropostaItemComposicao.nivel.asc(), PropostaItemComposicao.created_at.asc())
    )
    return list(result.scalars().all())
```

O import de `UUID` já deve existir no arquivo. Verificar e adicionar se necessário.

- [ ] **Step 5: Rodar e confirmar PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py::test_list_composicoes_by_proposta_item -v
```
Esperado: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/backend/repositories/proposta_item_composicao_repository.py app/backend/tests/unit/test_cpu_bdi_breakdown.py
git commit -m "feat(f2-04): add list_by_proposta_item to PropostaItemComposicaoRepository"
```

---

## Task 3: Service — listar_composicoes_item + recalcular_bdi

**Files:**
- Modify: `app/backend/services/cpu_geracao_service.py`

- [ ] **Step 1: Escrever testes**

Adicionar em `app/backend/tests/unit/test_cpu_bdi_breakdown.py`:

```python
@pytest.mark.asyncio
async def test_recalcular_bdi_atualiza_totais():
    from backend.services.cpu_geracao_service import CpuGeracaoService
    from backend.models.proposta import Proposta, PropostaItem

    proposta = MagicMock(spec=Proposta)
    proposta.id = uuid4()
    proposta.cliente_id = uuid4()
    proposta.total_direto = Decimal("100000")
    proposta.total_indireto = Decimal("0")
    proposta.total_geral = Decimal("100000")

    item1 = MagicMock(spec=PropostaItem)
    item1.custo_direto_unitario = Decimal("500")
    item1.quantidade = Decimal("10")
    item1.percentual_indireto = Decimal("0")
    item1.custo_indireto_unitario = Decimal("0")
    item1.preco_unitario = Decimal("500")
    item1.preco_total = Decimal("5000")

    db = MagicMock()
    db.flush = AsyncMock()

    svc = CpuGeracaoService.__new__(CpuGeracaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.proposta_item_repo = MagicMock()
    svc.proposta_item_repo.list_by_proposta = AsyncMock(return_value=[item1])

    result = await svc.recalcular_bdi(proposta.id, Decimal("20"))

    assert item1.percentual_indireto == Decimal("20") / 100
    expected_indireto = Decimal("500") * (Decimal("20") / 100) * Decimal("10")
    assert result["total_indireto"] == float(expected_indireto)
    assert result["itens_recalculados"] == 1


@pytest.mark.asyncio
async def test_listar_composicoes_item_retorna_lista():
    from backend.services.cpu_geracao_service import CpuGeracaoService
    from backend.models.proposta import PropostaItem, PropostaItemComposicao

    item = MagicMock(spec=PropostaItem)
    item.id = uuid4()
    item.proposta_id = uuid4()

    comp = MagicMock(spec=PropostaItemComposicao)
    comp.proposta_item_id = item.id

    db = MagicMock()
    svc = CpuGeracaoService.__new__(CpuGeracaoService)
    svc.db = db
    svc.proposta_item_repo = MagicMock()
    svc.proposta_item_repo.get_by_id = AsyncMock(return_value=item)
    svc.comp_repo = MagicMock()
    svc.comp_repo.list_by_proposta_item = AsyncMock(return_value=[comp])

    result = await svc.listar_composicoes_item(item.id)
    assert len(result) == 1
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py::test_recalcular_bdi_atualiza_totais backend/tests/unit/test_cpu_bdi_breakdown.py::test_listar_composicoes_item_retorna_lista -v
```
Esperado: `AttributeError` — métodos não existem.

- [ ] **Step 3: Implementar recalcular_bdi e listar_composicoes_item**

Em `app/backend/services/cpu_geracao_service.py`, adicionar ao final da classe `CpuGeracaoService`:

```python
async def recalcular_bdi(
    self,
    proposta_id: UUID,
    percentual_bdi: Decimal,
) -> dict:
    proposta = await self.proposta_repo.get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))

    itens = await self.proposta_item_repo.list_by_proposta(proposta_id)
    bdi_frac = percentual_bdi / Decimal("100")

    total_direto = Decimal("0")
    total_indireto = Decimal("0")
    itens_recalculados = 0

    for item in itens:
        if item.custo_direto_unitario is None:
            continue
        custo_indireto = item.custo_direto_unitario * bdi_frac
        preco_unit = item.custo_direto_unitario + custo_indireto
        preco_total = preco_unit * item.quantidade

        item.percentual_indireto = bdi_frac
        item.custo_indireto_unitario = custo_indireto
        item.preco_unitario = preco_unit
        item.preco_total = preco_total

        total_direto += item.custo_direto_unitario * item.quantidade
        total_indireto += custo_indireto * item.quantidade
        itens_recalculados += 1

    proposta.total_direto = total_direto
    proposta.total_indireto = total_indireto
    proposta.total_geral = total_direto + total_indireto
    await self.db.flush()

    return {
        "proposta_id": str(proposta_id),
        "percentual_bdi": float(percentual_bdi),
        "total_direto": float(total_direto),
        "total_indireto": float(total_indireto),
        "total_geral": float(total_direto + total_indireto),
        "itens_recalculados": itens_recalculados,
    }

async def listar_composicoes_item(self, proposta_item_id: UUID) -> list:
    item = await self.proposta_item_repo.get_by_id(proposta_item_id)
    if not item:
        raise NotFoundError("PropostaItem", str(proposta_item_id))
    return await self.comp_repo.list_by_proposta_item(proposta_item_id)
```

Verificar que `PropostaItemRepository` tem método `get_by_id` e `list_by_proposta`. Se `get_by_id` não existir, ler o arquivo e adicionar:

```python
async def get_by_id(self, id: UUID) -> PropostaItem | None:
    from sqlalchemy import select
    result = await self.db.execute(select(PropostaItem).where(PropostaItem.id == id))
    return result.scalar_one_or_none()
```

- [ ] **Step 4: Rodar testes**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py -v
```
Esperado: todos PASS.

- [ ] **Step 5: Regressão**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -5
```
Esperado: 112+ passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add app/backend/services/cpu_geracao_service.py app/backend/tests/unit/test_cpu_bdi_breakdown.py
git commit -m "feat(f2-04): add recalcular_bdi and listar_composicoes_item to CpuGeracaoService"
```

---

## Task 4: Endpoints — GET composicoes + POST recalcular-bdi

**Files:**
- Modify: `app/backend/api/v1/endpoints/cpu_geracao.py`

- [ ] **Step 1: Escrever testes dos endpoints**

Adicionar em `app/backend/tests/unit/test_cpu_bdi_breakdown.py`:

```python
@pytest.mark.asyncio
async def test_endpoint_composicoes_retorna_lista():
    from unittest.mock import patch
    from backend.api.v1.endpoints.cpu_geracao import listar_composicoes_proposta_item
    from backend.models.proposta import PropostaItemComposicao

    proposta = MagicMock()
    proposta.cliente_id = uuid4()
    composicao = MagicMock(spec=PropostaItemComposicao)
    composicao.id = uuid4()
    composicao.proposta_item_id = uuid4()
    composicao.descricao_insumo = "Pedreiro"
    composicao.unidade_medida = "h"
    composicao.quantidade_consumo = Decimal("8")
    composicao.custo_unitario_insumo = Decimal("45")
    composicao.custo_total_insumo = Decimal("360")
    composicao.tipo_recurso = MagicMock(value="MO")
    composicao.nivel = 1
    composicao.e_composicao = False
    composicao.fonte_custo = "pc_tabela"

    with (
        patch("backend.api.v1.endpoints.cpu_geracao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.cpu_geracao.CpuGeracaoService") as MockSvc,
        patch("backend.api.v1.endpoints.cpu_geracao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.listar_composicoes_item = AsyncMock(return_value=[composicao])
        db = MagicMock()
        user = MagicMock()
        result = await listar_composicoes_proposta_item(
            proposta_id=uuid4(),
            item_id=composicao.proposta_item_id,
            current_user=user,
            db=db,
        )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_endpoint_recalcular_bdi():
    from unittest.mock import patch
    from backend.api.v1.endpoints.cpu_geracao import recalcular_bdi_proposta
    from backend.schemas.proposta import RecalcularBdiRequest

    proposta = MagicMock()
    proposta.cliente_id = uuid4()
    proposta_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.cpu_geracao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.cpu_geracao.CpuGeracaoService") as MockSvc,
        patch("backend.api.v1.endpoints.cpu_geracao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.recalcular_bdi = AsyncMock(return_value={
            "proposta_id": str(proposta_id),
            "percentual_bdi": 25.0,
            "total_direto": 100000.0,
            "total_indireto": 25000.0,
            "total_geral": 125000.0,
            "itens_recalculados": 10,
        })
        db = MagicMock()
        db.commit = AsyncMock()
        user = MagicMock()
        req = RecalcularBdiRequest(percentual_bdi=Decimal("25"))
        result = await recalcular_bdi_proposta(
            proposta_id=proposta_id,
            body=req,
            current_user=user,
            db=db,
        )
    assert result.itens_recalculados == 10
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py::test_endpoint_composicoes_retorna_lista -v
```
Esperado: `ImportError` — endpoint não existe ainda.

- [ ] **Step 3: Implementar os 2 novos endpoints**

Em `app/backend/api/v1/endpoints/cpu_geracao.py`, adicionar imports:

```python
from backend.schemas.proposta import (
    ComposicaoDetalheResponse,
    CpuGeracaoResponse,
    CpuItemResponse,
    RecalcularBdiRequest,
    RecalcularBdiResponse,
)
```

E ao final do arquivo, adicionar os dois endpoints:

```python
@router.get("/itens/{item_id}/composicoes", response_model=list[ComposicaoDetalheResponse])
async def listar_composicoes_proposta_item(
    proposta_id: UUID,
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComposicaoDetalheResponse]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = CpuGeracaoService(db)
    composicoes = await svc.listar_composicoes_item(item_id)
    return [ComposicaoDetalheResponse.model_validate(c) for c in composicoes]


@router.post("/recalcular-bdi", response_model=RecalcularBdiResponse)
async def recalcular_bdi_proposta(
    proposta_id: UUID,
    body: RecalcularBdiRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecalcularBdiResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = CpuGeracaoService(db)
    resultado = await svc.recalcular_bdi(proposta_id, body.percentual_bdi)
    await db.commit()
    return RecalcularBdiResponse.model_validate(resultado)
```

- [ ] **Step 4: Rodar todos os testes do arquivo**

```bash
cd app && python -m pytest backend/tests/unit/test_cpu_bdi_breakdown.py -v
```
Esperado: todos PASS.

- [ ] **Step 5: Regressão completa**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -5
```
Esperado: 115+ passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add app/backend/api/v1/endpoints/cpu_geracao.py app/backend/tests/unit/test_cpu_bdi_breakdown.py
git commit -m "feat(f2-04): add GET /cpu/itens/{id}/composicoes and POST /cpu/recalcular-bdi endpoints"
```

---

## Task 5: Frontend — API client (listCpuItens, getComposicoes, recalcularBdi)

**Files:**
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts`

- [ ] **Step 1: Adicionar tipos TypeScript para CPU detalhada**

Após `PqMatchConfirmarRequest` em `proposalsApi.ts` (ou ao final das interfaces), adicionar:

```typescript
export interface ComposicaoDetalhe {
  id: string;
  proposta_item_id: string;
  descricao_insumo: string;
  unidade_medida: string;
  quantidade_consumo: string;
  custo_unitario_insumo: string | null;
  custo_total_insumo: string | null;
  tipo_recurso: string | null;
  nivel: number;
  e_composicao: boolean;
  fonte_custo: string | null;
}

export interface CpuItemDetalhado {
  id: string;
  proposta_id: string;
  pq_item_id: string | null;
  servico_id: string;
  codigo: string;
  descricao: string;
  unidade_medida: string;
  quantidade: string;
  custo_material_unitario: string | null;
  custo_mao_obra_unitario: string | null;
  custo_equipamento_unitario: string | null;
  custo_direto_unitario: string | null;
  percentual_indireto: string | null;
  custo_indireto_unitario: string | null;
  preco_unitario: string | null;
  preco_total: string | null;
  composicao_fonte: string | null;
  ordem: number;
}

export interface RecalcularBdiRequest {
  percentual_bdi: number;
}

export interface RecalcularBdiResponse {
  proposta_id: string;
  percentual_bdi: number;
  total_direto: number;
  total_indireto: number;
  total_geral: number;
  itens_recalculados: number;
}
```

- [ ] **Step 2: Adicionar métodos ao objeto proposalsApi**

Após o método `confirmarMatch`, adicionar:

```typescript
  async listCpuItens(propostaId: string): Promise<CpuItemDetalhado[]> {
    const response = await apiClient.get<CpuItemDetalhado[]>(
      `/propostas/${propostaId}/cpu/itens`,
    );
    return response.data;
  },

  async getComposicoes(propostaId: string, itemId: string): Promise<ComposicaoDetalhe[]> {
    const response = await apiClient.get<ComposicaoDetalhe[]>(
      `/propostas/${propostaId}/cpu/itens/${itemId}/composicoes`,
    );
    return response.data;
  },

  async recalcularBdi(
    propostaId: string,
    payload: RecalcularBdiRequest,
  ): Promise<RecalcularBdiResponse> {
    const response = await apiClient.post<RecalcularBdiResponse>(
      `/propostas/${propostaId}/cpu/recalcular-bdi`,
      payload,
    );
    return response.data;
  },

  async gerarCpu(
    propostaId: string,
    percentualBdi: number,
    pcCabecalhoId?: string,
  ): Promise<{ proposta_id: string; total_direto: number; total_indireto: number; total_geral: number; detalhe: { processados: number; erros: number } }> {
    const params: Record<string, string | number> = { percentual_bdi: percentualBdi };
    if (pcCabecalhoId) params.pc_cabecalho_id = pcCabecalhoId;
    const response = await apiClient.post(
      `/propostas/${propostaId}/cpu/gerar`,
      null,
      { params },
    );
    return response.data;
  },
```

- [ ] **Step 3: Checar TypeScript**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -20
```
Esperado: sem erros.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/shared/services/api/proposalsApi.ts
git commit -m "feat(f2-04): add CPU detail types and listCpuItens/getComposicoes/recalcularBdi to proposalsApi"
```

---

## Task 6: Frontend — CpuTable com accordion de insumos

**Files:**
- Modify: `app/frontend/src/features/proposals/components/CpuTable.tsx`

A tabela atual (`CpuTable`) é básica e usa `CpuItem` do types.ts que tem poucos campos. Vamos substituí-la para usar `CpuItemDetalhado` com accordion que expande para mostrar insumos.

- [ ] **Step 1: Reescrever CpuTable.tsx**

```tsx
import { useState } from 'react';
import {
  Box,
  Chip,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { useQuery } from '@tanstack/react-query';
import { formatCurrency } from '../../../shared/utils/format';
import type { CpuItemDetalhado } from '../../../shared/services/api/proposalsApi';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';

interface ComposicaoRowsProps {
  propostaId: string;
  itemId: string;
}

function ComposicaoRows({ propostaId, itemId }: ComposicaoRowsProps) {
  const { data: composicoes = [], isLoading } = useQuery({
    queryKey: ['composicoes', propostaId, itemId],
    queryFn: () => proposalsApi.getComposicoes(propostaId, itemId),
  });

  if (isLoading) {
    return (
      <TableRow>
        <TableCell colSpan={5}>
          <Typography variant="caption">Carregando insumos...</Typography>
        </TableCell>
      </TableRow>
    );
  }

  return (
    <>
      {composicoes.map((c) => (
        <TableRow key={c.id} sx={{ bgcolor: 'action.hover' }}>
          <TableCell sx={{ pl: 6 }}>
            <Chip
              label={c.tipo_recurso ?? 'MAT'}
              size="small"
              color={
                c.tipo_recurso === 'MO' ? 'info'
                : c.tipo_recurso === 'EQUIPAMENTO' ? 'warning'
                : 'default'
              }
              sx={{ mr: 1 }}
            />
            {c.descricao_insumo}
          </TableCell>
          <TableCell>{c.unidade_medida}</TableCell>
          <TableCell>{parseFloat(c.quantidade_consumo).toFixed(4)}</TableCell>
          <TableCell>{c.custo_unitario_insumo ? formatCurrency(parseFloat(c.custo_unitario_insumo)) : '—'}</TableCell>
          <TableCell>{c.custo_total_insumo ? formatCurrency(parseFloat(c.custo_total_insumo)) : '—'}</TableCell>
        </TableRow>
      ))}
      {composicoes.length === 0 && (
        <TableRow sx={{ bgcolor: 'action.hover' }}>
          <TableCell colSpan={5} sx={{ pl: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Sem insumos registrados para este item.
            </Typography>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

interface CpuItemRowProps {
  item: CpuItemDetalhado;
  propostaId: string;
}

function CpuItemRow({ item, propostaId }: CpuItemRowProps) {
  const [open, setOpen] = useState(false);
  const bdi = item.percentual_indireto
    ? `${(parseFloat(item.percentual_indireto) * 100).toFixed(1)}%`
    : '0%';

  return (
    <>
      <TableRow hover>
        <TableCell sx={{ width: 40 }}>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Typography variant="caption" color="text.secondary">{item.codigo}</Typography>
        </TableCell>
        <TableCell>
          <Tooltip title={item.descricao}>
            <Typography variant="body2" noWrap sx={{ maxWidth: 280 }}>{item.descricao}</Typography>
          </Tooltip>
        </TableCell>
        <TableCell>{item.unidade_medida}</TableCell>
        <TableCell align="right">{parseFloat(item.quantidade).toFixed(2)}</TableCell>
        <TableCell align="right">{item.custo_material_unitario ? formatCurrency(parseFloat(item.custo_material_unitario)) : '—'}</TableCell>
        <TableCell align="right">{item.custo_mao_obra_unitario ? formatCurrency(parseFloat(item.custo_mao_obra_unitario)) : '—'}</TableCell>
        <TableCell align="right">{item.custo_equipamento_unitario ? formatCurrency(parseFloat(item.custo_equipamento_unitario)) : '—'}</TableCell>
        <TableCell align="right">{item.custo_direto_unitario ? formatCurrency(parseFloat(item.custo_direto_unitario)) : '—'}</TableCell>
        <TableCell align="right">
          <Chip label={bdi} size="small" variant="outlined" />
        </TableCell>
        <TableCell align="right" sx={{ fontWeight: 'bold' }}>
          {item.preco_total ? formatCurrency(parseFloat(item.preco_total)) : '—'}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={11} sx={{ py: 0, border: 0 }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ m: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ ml: 5 }}>
                Insumos
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
                    <TableCell sx={{ pl: 6 }}>Insumo</TableCell>
                    <TableCell>Und</TableCell>
                    <TableCell>Qtd</TableCell>
                    <TableCell>Custo Unit.</TableCell>
                    <TableCell>Custo Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <ComposicaoRows propostaId={propostaId} itemId={item.id} />
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

interface CpuTableProps {
  itens: CpuItemDetalhado[];
  propostaId: string;
}

export function CpuTable({ itens, propostaId }: CpuTableProps) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell />
          <TableCell>Código</TableCell>
          <TableCell>Descrição</TableCell>
          <TableCell>Und</TableCell>
          <TableCell align="right">Qtd</TableCell>
          <TableCell align="right">Mat. Unit.</TableCell>
          <TableCell align="right">MO Unit.</TableCell>
          <TableCell align="right">Equip. Unit.</TableCell>
          <TableCell align="right">Dir. Unit.</TableCell>
          <TableCell align="right">BDI</TableCell>
          <TableCell align="right">Total</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {itens.map((item) => (
          <CpuItemRow key={item.id} item={item} propostaId={propostaId} />
        ))}
        {itens.length === 0 && (
          <TableRow>
            <TableCell colSpan={11} align="center" sx={{ py: 4 }}>
              <Typography color="text.secondary">
                Nenhum item de CPU gerado ainda.
              </Typography>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
```

- [ ] **Step 2: Checar TypeScript**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -20
```
Esperado: sem erros em `CpuTable.tsx`.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/proposals/components/CpuTable.tsx
git commit -m "feat(f2-04): rewrite CpuTable with breakdown accordion and insumos per item"
```

---

## Task 7: Frontend — ProposalCpuPage desbloqueada com BDI dinâmico

**Files:**
- Modify: `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx`

- [ ] **Step 1: Reescrever ProposalCpuPage.tsx**

```tsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Chip,
  InputAdornment,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined';
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { formatCurrency } from '../../../shared/utils/format';
import { CpuTable } from '../components/CpuTable';

export function ProposalCpuPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [bdi, setBdi] = useState('25');

  const { data: proposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const { data: itens = [], isLoading: loadingItens } = useQuery({
    queryKey: ['cpu-itens', id],
    queryFn: () => proposalsApi.listCpuItens(id!),
    enabled: Boolean(id),
  });

  const gerarMutation = useMutation({
    mutationFn: () =>
      proposalsApi.gerarCpu(id!, parseFloat(bdi) || 0),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens', id] });
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const recalcularMutation = useMutation({
    mutationFn: () =>
      proposalsApi.recalcularBdi(id!, { percentual_bdi: parseFloat(bdi) || 0 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens', id] });
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const jaTemItens = itens.length > 0;

  return (
    <>
      <PageHeader
        title="Visualização de CPU"
        description={`Proposta ${proposta?.codigo ?? ''} — ${itens.length} itens`}
        actions={
          <Button
            variant="outlined"
            startIcon={<ArrowBackOutlinedIcon />}
            onClick={() => navigate(`/propostas/${id}`)}
          >
            Voltar
          </Button>
        }
      />

      <Stack spacing={3}>
        {(gerarMutation.isError || recalcularMutation.isError) && (
          <Alert severity="error">
            {extractApiErrorMessage(gerarMutation.error ?? recalcularMutation.error)}
          </Alert>
        )}

        <Paper sx={{ p: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              label="BDI (%)"
              type="number"
              value={bdi}
              onChange={(e) => setBdi(e.target.value)}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              inputProps={{ min: 0, max: 100, step: 0.5 }}
              sx={{ width: 150 }}
            />
            {!jaTemItens ? (
              <Button
                variant="contained"
                startIcon={<PlayArrowOutlinedIcon />}
                onClick={() => gerarMutation.mutate()}
                disabled={gerarMutation.isPending}
              >
                {gerarMutation.isPending ? 'Gerando CPU...' : 'Gerar CPU'}
              </Button>
            ) : (
              <Button
                variant="outlined"
                startIcon={<CalculateOutlinedIcon />}
                onClick={() => recalcularMutation.mutate()}
                disabled={recalcularMutation.isPending}
              >
                {recalcularMutation.isPending ? 'Recalculando...' : 'Recalcular BDI'}
              </Button>
            )}

            {proposta && (
              <Stack direction="row" spacing={2} sx={{ ml: 'auto' }}>
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">Total Direto</Typography>
                  <Typography variant="h6">{formatCurrency(proposta.total_direto ?? 0)}</Typography>
                </Box>
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">Total Indireto (BDI)</Typography>
                  <Typography variant="h6">{formatCurrency(proposta.total_indireto ?? 0)}</Typography>
                </Box>
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">Total Geral</Typography>
                  <Typography variant="h6" color="primary.main" fontWeight="bold">
                    {formatCurrency(proposta.total_geral ?? 0)}
                  </Typography>
                </Box>
              </Stack>
            )}
          </Stack>

          {gerarMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              CPU gerada com sucesso: {gerarMutation.data.detalhe.processados} itens processados,{' '}
              {gerarMutation.data.detalhe.erros} erros.
            </Alert>
          )}
          {recalcularMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              BDI recalculado: {recalcularMutation.data.itens_recalculados} itens atualizados.
            </Alert>
          )}
        </Paper>

        <Paper>
          {loadingItens ? (
            <Box sx={{ p: 3 }}>
              <Typography>Carregando itens...</Typography>
            </Box>
          ) : (
            <CpuTable itens={itens} propostaId={id!} />
          )}
        </Paper>
      </Stack>
    </>
  );
}
```

- [ ] **Step 2: Checar TypeScript completo**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -30
```
Esperado: 0 erros.

- [ ] **Step 3: Regressão backend final**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -5
```
Esperado: 115+ passed, 0 failed.

- [ ] **Step 4: Commit final**

```bash
git add app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx
git commit -m "feat(f2-04): unlock CPU page — real data, generate + recalculate BDI, totals display"
```

---

## Self-Review

**Spec coverage:**
- ✅ Breakdown de insumos por item — `GET /cpu/itens/{id}/composicoes` + `CpuTable` accordion
- ✅ BDI dinâmico por proposta — `POST /cpu/recalcular-bdi` + botão na CPU page
- ✅ Gerar CPU funcional — `gerarCpu` na API + botão "Gerar CPU" (primeiro uso)
- ✅ Totais visíveis — total direto, indireto, geral exibidos no header da CPU page
- ✅ Transparência material/MO/equipamento — colunas separadas em `CpuTable`
- ✅ Erro detalhado — `detalhe.erros` exibido após geração

**Placeholder scan:** sem "TBD", sem "implement later". Todos os code blocks completos.

**Type consistency:** `CpuItemDetalhado` definido em `proposalsApi.ts` e usado em `CpuTable` e `ProposalCpuPage`. `ComposicaoDetalhe` definido uma vez e usado em `ComposicaoRows`. `RecalcularBdiResponse` no backend e `RecalcularBdiResponse` no frontend — campos `itens_recalculados` consistentes.

**Gap known:** exportação Excel/PDF não está nesta sprint — está prevista para F2-05.
