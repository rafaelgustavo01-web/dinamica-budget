# Geração da CPU — Composição de Preços Unitários — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explodir a composição de cada PropostaItem em insumos, calcular custos unitários via lookup em PcTabelas satélites, aplicar BDI, e gerar a CPU final com rastreabilidade completa.

**Architecture:** Service `CpuGenerationService` orquestra: (1) leitura de PropostaItems com match confirmado, (2) explosão de composição REUSANDO `servico_catalog_service.explode_composicao`, (3) lookup de custos em PcTabelas satélites, (4) aplicação de BDI, (5) persistência em `PropostaItem` + `PropostaItemComposicao`.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest.

**Important — Already Exists (DO NOT recreate):**
- `TipoRecurso` enum → `app/models/enums.py:49`
- `PropostaItem` model → `app/models/proposta.py:135`
- `PropostaItemComposicao` model → `app/models/proposta.py:181`
- `explode_composicao` logic → `app/services/servico_catalog_service.py:97`
- PcTabelas models → `app/models/pc_tabelas.py`

---

## Task 1: Repositories

**Files:**
- Create: `app/repositories/proposta_item_repository.py`
- Create: `app/repositories/proposta_item_composicao_repository.py`

### Step 1: PropostaItemRepository

```python
# app/repositories/proposta_item_repository.py
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposta import PropostaItem
from app.repositories.base_repository import BaseRepository

class PropostaItemRepository(BaseRepository[PropostaItem]):
    model = PropostaItem

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_id(self, id: UUID) -> PropostaItem | None:  # type: ignore[override]
        result = await self.db.execute(
            select(PropostaItem).where(PropostaItem.id == id)
        )
        return result.scalar_one_or_none()

    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaItem]:
        result = await self.db.execute(
            select(PropostaItem)
            .where(PropostaItem.proposta_id == proposta_id)
            .order_by(PropostaItem.ordem.asc())
        )
        return list(result.scalars().all())

    async def create_batch(self, items: list[PropostaItem]) -> list[PropostaItem]:
        self.db.add_all(items)
        await self.db.flush()
        return items

    async def delete_by_proposta(self, proposta_id: UUID) -> None:
        from sqlalchemy import delete
        await self.db.execute(
            delete(PropostaItem).where(PropostaItem.proposta_id == proposta_id)
        )
```

### Step 2: PropostaItemComposicaoRepository

```python
# app/repositories/proposta_item_composicao_repository.py
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposta import PropostaItemComposicao
from app.repositories.base_repository import BaseRepository

class PropostaItemComposicaoRepository(BaseRepository[PropostaItemComposicao]):
    model = PropostaItemComposicao

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def list_by_proposta_item(self, proposta_item_id: UUID) -> list[PropostaItemComposicao]:
        result = await self.db.execute(
            select(PropostaItemComposicao)
            .where(PropostaItemComposicao.proposta_item_id == proposta_item_id)
        )
        return list(result.scalars().all())

    async def create_batch(self, items: list[PropostaItemComposicao]) -> list[PropostaItemComposicao]:
        self.db.add_all(items)
        await self.db.flush()
        return items

    async def delete_by_proposta_item(self, proposta_item_id: UUID) -> None:
        await self.db.execute(
            delete(PropostaItemComposicao)
            .where(PropostaItemComposicao.proposta_item_id == proposta_item_id)
        )
```

### Step 3: Commit

```bash
git add app/repositories/proposta_item_repository.py app/repositories/proposta_item_composicao_repository.py
git commit -m "feat(cpu): add PropostaItem and PropostaItemComposicao repositories"
```

---

## Task 2: Serviço de Lookup de Custos (PcTabelas)

**Files:**
- Create: `app/services/cpu_custo_service.py`

### Step 1: Implementar lookup de custos em PcTabelas

```python
# app/services/cpu_custo_service.py
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TipoRecurso
from app.models.proposta import PropostaItemComposicao
from app.models.pc_tabelas import PcMaoObraItem, PcEquipamentoItem

class CpuCustoService:
    def __init__(self, db: AsyncSession, pc_cabecalho_id: UUID | None = None):
        self.db = db
        self.pc_cabecalho_id = pc_cabecalho_id

    async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
        for comp in composicoes:
            if comp.tipo_recurso == TipoRecurso.MO and comp.insumo_base_id:
                custo = await self._lookup_mao_obra(comp.insumo_base_id)
                comp.custo_unitario_insumo = custo
                comp.fonte_custo = "pc_mao_obra" if custo is not None else "custo_base"
            elif comp.tipo_recurso == TipoRecurso.EQUIPAMENTO and comp.insumo_base_id:
                custo = await self._lookup_equipamento(comp.insumo_base_id)
                comp.custo_unitario_insumo = custo
                comp.fonte_custo = "pc_equipamento" if custo is not None else "custo_base"
            else:
                # Fallback: usar custo_base do BaseTcpo (já populado na explosão)
                comp.fonte_custo = comp.fonte_custo or "custo_base"

            if comp.custo_unitario_insumo is not None and comp.quantidade_consumo is not None:
                comp.custo_total_insumo = comp.custo_unitario_insumo * comp.quantidade_consumo

    async def _lookup_mao_obra(self, base_id: UUID) -> Decimal | None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(PcMaoObraItem.custo_hora)
            .where(
                PcMaoObraItem.base_id == base_id,
                PcMaoObraItem.pc_cabecalho_id == self.pc_cabecalho_id,
            )
        )
        return result.scalar_one_or_none()

    async def _lookup_equipamento(self, base_id: UUID) -> Decimal | None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(PcEquipamentoItem.custo_hora)
            .where(
                PcEquipamentoItem.base_id == base_id,
                PcEquipamentoItem.pc_cabecalho_id == self.pc_cabecalho_id,
            )
        )
        return result.scalar_one_or_none()
```

### Step 2: Commit

```bash
git add app/services/cpu_custo_service.py
git commit -m "feat(cpu): add CpuCustoService with PcTabelas lookup"
```

---

## Task 3: Serviço de Explosão para PropostaItem

**Files:**
- Create: `app/services/cpu_explosao_service.py`

### Step 1: Reutilizar explode_composicao existente

```python
# app/services/cpu_explosao_service.py
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TipoRecurso, TipoServicoMatch
from app.models.proposta import PropostaItem, PropostaItemComposicao
from app.services.servico_catalog_service import servico_catalog_service

class CpuExplosaoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def explodir_proposta_item(self, proposta_item: PropostaItem) -> list[PropostaItemComposicao]:
        """Explode a composição do serviço vinculado ao PropostaItem.

        REUSA servico_catalog_service.explode_composicao — não reinventa a DFS.
        """
        from app.schemas.servico import ExplodeComposicaoResponse

        resultado: ExplodeComposicaoResponse = await servico_catalog_service.explode_composicao(
            servico_id=proposta_item.servico_id,
            db=self.db,
        )

        composicoes: list[PropostaItemComposicao] = []
        for item in resultado.itens:
            pic = PropostaItemComposicao(
                proposta_item_id=proposta_item.id,
                insumo_base_id=item.insumo_filho_id,
                descricao_insumo=item.descricao_filho,
                unidade_medida=item.unidade_medida,
                quantidade_consumo=item.quantidade_consumo,
                custo_unitario_insumo=item.custo_unitario,
                custo_total_insumo=item.custo_total,
                tipo_recurso=await self._inferir_tipo_recurso(item.insumo_filho_id),
                fonte_custo="explosao_composicao",
            )
            composicoes.append(pic)

        return composicoes

    async def _inferir_tipo_recurso(self, insumo_id: UUID) -> TipoRecurso | None:
        from sqlalchemy import select
        from app.models.servico import BaseTcpo
        result = await self.db.execute(
            select(BaseTcpo.tipo_recurso).where(BaseTcpo.id == insumo_id)
        )
        return result.scalar_one_or_none()
```

### Step 2: Commit

```bash
git add app/services/cpu_explosao_service.py
git commit -m "feat(cpu): add CpuExplosaoService reusing existing explode_composicao"
```

---

## Task 4: Serviço de Geração da CPU (Orquestrador)

**Files:**
- Create: `app/services/cpu_geracao_service.py`

### Step 1: Implementar orquestração

```python
# app/services/cpu_geracao_service.py
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StatusProposta
from app.models.proposta import PropostaItem
from app.repositories.proposta_item_repository import PropostaItemRepository
from app.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
from app.repositories.proposta_repository import PropostaRepository
from app.services.cpu_explosao_service import CpuExplosaoService
from app.services.cpu_custo_service import CpuCustoService
from app.core.exceptions import NotFoundError

class CpuGeracaoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.explosao_svc = CpuExplosaoService(db)
        self.item_repo = PropostaItemRepository(db)
        self.comp_repo = PropostaItemComposicaoRepository(db)
        self.proposta_repo = PropostaRepository(db)

    async def gerar_cpu_para_proposta(
        self,
        proposta_id: UUID,
        pc_cabecalho_id: UUID | None = None,
        percentual_bdi: Decimal = Decimal("0"),
    ) -> dict:
        """Gera CPU completa para todos os PropostaItems de uma proposta."""
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        items = await self.item_repo.list_by_proposta(proposta_id)
        custo_svc = CpuCustoService(self.db, pc_cabecalho_id)

        total_direto = Decimal("0")
        resultados = {"processados": 0, "erros": 0}

        for item in items:
            try:
                # 1. Limpar composição anterior
                await self.comp_repo.delete_by_proposta_item(item.id)

                # 2. Explodir (reusa servico_catalog_service)
                composicoes = await self.explosao_svc.explodir_proposta_item(item)

                if composicoes:
                    # 3. Lookup PcTabelas para custos reais
                    await custo_svc.calcular_custos(composicoes)
                    await self.comp_repo.create_batch(composicoes)

                    # 4. Totais do item
                    custo_direto = sum((c.custo_total_insumo or Decimal("0")) for c in composicoes)
                else:
                    custo_direto = Decimal("0")

                custo_indireto = custo_direto * percentual_bdi
                preco_unitario = custo_direto + custo_indireto
                preco_total = preco_unitario * item.quantidade

                item.custo_direto_unitario = custo_direto
                item.custo_indireto_unitario = custo_indireto
                item.percentual_indireto = percentual_bdi
                item.preco_unitario = preco_unitario
                item.preco_total = preco_total

                total_direto += preco_total
                resultados["processados"] += 1

            except Exception:
                resultados["erros"] += 1

        # 5. Atualizar proposta
        proposta.total_direto = total_direto
        proposta.total_indireto = total_direto * percentual_bdi
        proposta.total_geral = total_direto + proposta.total_indireto
        proposta.pc_cabecalho_id = pc_cabecalho_id
        proposta.status = StatusProposta.CPU_GERADA

        await self.db.flush()
        return {
            "proposta_id": str(proposta_id),
            "total_geral": float(proposta.total_geral),
            "total_direto": float(total_direto),
            "detalhe": resultados,
        }
```

### Step 2: Commit

```bash
git add app/services/cpu_geracao_service.py
git commit -m "feat(cpu): add CpuGeracaoService orchestrator"
```

---

## Task 5: API Endpoints

**Files:**
- Create: `app/api/v1/endpoints/cpu_geracao.py`
- Modify: `app/api/v1/router.py`

### Step 1: Rotas

```python
# app/api/v1/endpoints/cpu_geracao.py
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_access
from app.core.exceptions import NotFoundError
from app.repositories.proposta_repository import PropostaRepository
from app.services.cpu_geracao_service import CpuGeracaoService

router = APIRouter(prefix="/propostas/{proposta_id}/cpu", tags=["cpu"])

@router.post("/gerar", status_code=200)
async def gerar_cpu(
    proposta_id: UUID,
    pc_cabecalho_id: UUID | None = None,
    percentual_bdi: float = 0.0,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    prop_repo = PropostaRepository(db)
    proposta = await prop_repo.get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = CpuGeracaoService(db)
    resultado = await svc.gerar_cpu_para_proposta(
        proposta_id,
        pc_cabecalho_id=pc_cabecalho_id,
        percentual_bdi=Decimal(str(percentual_bdi)),
    )
    return resultado

@router.get("/itens", status_code=200)
async def listar_cpu_itens(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    prop_repo = PropostaRepository(db)
    proposta = await prop_repo.get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    await require_cliente_access(proposta.cliente_id, current_user, db)

    from app.repositories.proposta_item_repository import PropostaItemRepository
    item_repo = PropostaItemRepository(db)
    items = await item_repo.list_by_proposta(proposta_id)
    return [{
        "id": str(i.id),
        "codigo": i.codigo,
        "descricao": i.descricao,
        "quantidade": float(i.quantidade),
        "preco_unitario": float(i.preco_unitario or 0),
        "preco_total": float(i.preco_total or 0),
        "custo_direto_unitario": float(i.custo_direto_unitario or 0),
    } for i in items]
```

### Step 2: Commit

```bash
git add app/api/v1/endpoints/cpu_geracao.py
git commit -m "feat(cpu): add CPU generation endpoints"
```

---

## Task 6: Testes Unitários

**Files:**
- Create: `app/tests/unit/test_cpu_geracao_service.py`

### Step 1: Testar orquestração

```python
# app/tests/unit/test_cpu_geracao_service.py
import uuid
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.cpu_geracao_service import CpuGeracaoService
from app.models.enums import StatusProposta

@pytest.mark.asyncio
async def test_gerar_cpu_sem_composicao():
    mock_db = AsyncMock()
    svc = CpuGeracaoService(mock_db)

    proposta_id = uuid.uuid4()
    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.total_direto = None
    proposta.total_indireto = None
    proposta.total_geral = None

    item = MagicMock()
    item.id = uuid.uuid4()
    item.quantidade = Decimal("1")

    with patch.object(svc.proposta_repo, "get_by_id", AsyncMock(return_value=proposta)):
        with patch.object(svc.item_repo, "list_by_proposta", AsyncMock(return_value=[item])):
            with patch.object(svc.explosao_svc, "explodir_proposta_item", AsyncMock(return_value=[])):
                resultado = await svc.gerar_cpu_para_proposta(proposta_id)
                assert resultado["detalhe"]["processados"] == 1
                assert proposta.status == StatusProposta.CPU_GERADA


@pytest.mark.asyncio
async def test_gerar_cpu_com_composicao():
    mock_db = AsyncMock()
    svc = CpuGeracaoService(mock_db)

    proposta_id = uuid.uuid4()
    proposta = MagicMock()
    proposta.id = proposta_id

    item = MagicMock()
    item.id = uuid.uuid4()
    item.quantidade = Decimal("2")

    comp = MagicMock()
    comp.custo_total_insumo = Decimal("100")

    with patch.object(svc.proposta_repo, "get_by_id", AsyncMock(return_value=proposta)):
        with patch.object(svc.item_repo, "list_by_proposta", AsyncMock(return_value=[item])):
            with patch.object(svc.explosao_svc, "explodir_proposta_item", AsyncMock(return_value=[comp])):
                with patch.object(svc.comp_repo, "create_batch", AsyncMock()):
                    resultado = await svc.gerar_cpu_para_proposta(proposta_id, percentual_bdi=Decimal("0.1"))
                    assert resultado["detalhe"]["processados"] == 1
                    assert item.preco_total == Decimal("220")  # 100 * 2 * 1.1
```

### Step 2: Commit

```bash
git add app/tests/unit/test_cpu_geracao_service.py
git commit -m "test(cpu): add unit tests for CPU generation"
```

---

## Task 7: Full Regression + Walkthrough

### Step 1: Rodar suite

```bash
pytest app/tests/unit/ -v --tb=short
```
Expected: ALL PASS

### Step 2: Walkthrough

Create: `docs/walkthrough/done/walkthrough-S-11.md`

### Step 3: Commit

```bash
git add docs/walkthrough/done/walkthrough-S-11.md
git commit -m "docs(s-11): add walkthrough for CPU generation"
```

---

## Plan Review Checklist

- [x] Spec coverage: explosão, lookup PcTabelas, BDI, rastreabilidade
- [x] Placeholder scan: no TBD/TODO found
- [x] Reuses existing `explode_composicao` (servico_catalog_service) — não reinventa DFS
- [x] Reuses existing models (`PropostaItem`, `PropostaItemComposicao`, `TipoRecurso`) — não recria
- [x] Type consistency: Decimal, UUID, enums consistentes com codebase

## Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-23-geracao-cpu-composicao-precos.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch subagent per task, review between tasks
2. **Inline Execution** — execute in this session with checkpoints

Which approach?
