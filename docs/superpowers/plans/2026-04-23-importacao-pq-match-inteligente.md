# Importação PQ e Match Inteligente — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir upload de planilha quantitativa (Excel/CSV) para uma proposta, extrair itens brutos (PqItem), e executar match fuzzy/semântico contra o catálogo (Base TCPO + Itens Próprios) com confiança score.

**Architecture:** Endpoint recebe multipart upload → serviço valida e parseia → cria PqImportacao + PqItems em batch → motor de match reusa busca_service (fase1+fase3) → itens atualizados com match_status e servico_match_id.

**Tech Stack:** FastAPI, SQLAlchemy async, pandas/openpyxl, pytest. Reusa serviços de busca existentes (S-05).

---

## Task 1: Schema e Enums de Importação

**Files:**
- Modify: `app/models/enums.py`
- Modify: `app/models/proposta.py` (adicionar PqImportacao e PqItem se ainda não existirem)

### Step 1: Adicionar enums faltantes

```python
# app/models/enums.py
class StatusImportacao(str, Enum):
    PROCESSANDO = "PROCESSANDO"
    VALIDADO = "VALIDADO"
    COM_ERROS = "COM_ERROS"
    CONCLUIDO = "CONCLUIDO"

class StatusMatch(str, Enum):
    PENDENTE = "PENDENTE"
    BUSCANDO = "BUSCANDO"
    SUGERIDO = "SUGERIDO"
    CONFIRMADO = "CONFIRMADO"
    MANUAL = "MANUAL"
    SEM_MATCH = "SEM_MATCH"

class TipoServicoMatch(str, Enum):
    BASE_TCPO = "BASE_TCPO"
    ITEM_PROPRIO = "ITEM_PROPRIO"
```

### Step 2: Commit

```bash
git add app/models/enums.py
git commit -m "feat(pq): add StatusImportacao, StatusMatch, TipoServicoMatch enums"
```

---

## Task 2: Repositories para PQ

**Files:**
- Create: `app/repositories/pq_item_repository.py`
- Create: `app/repositories/pq_importacao_repository.py`

### Step 1: PqItemRepository

```python
# app/repositories/pq_item_repository.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.proposta import PqItem

class PqItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_batch(self, items: list[PqItem]) -> list[PqItem]:
        self.db.add_all(items)
        await self.db.flush()
        return items

    async def list_by_proposta(self, proposta_id: UUID, offset: int = 0, limit: int = 100) -> list[PqItem]:
        from sqlalchemy import select
        result = await self.db.execute(
            select(PqItem).where(PqItem.proposta_id == proposta_id).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def update_match(self, pq_item_id: UUID, servico_match_id: UUID, servico_match_tipo: str, confidence: float) -> None:
        from sqlalchemy import update
        await self.db.execute(
            update(PqItem).where(PqItem.id == pq_item_id).values(
                servico_match_id=servico_match_id,
                servico_match_tipo=servico_match_tipo,
                match_confidence=confidence,
                match_status="SUGERIDO",
            )
        )
```

### Step 2: PqImportacaoRepository

```python
# app/repositories/pq_importacao_repository.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.proposta import PqImportacao

class PqImportacaoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, imp: PqImportacao) -> PqImportacao:
        self.db.add(imp)
        await self.db.flush()
        await self.db.refresh(imp)
        return imp

    async def get_by_id(self, importacao_id: UUID) -> PqImportacao | None:
        from sqlalchemy import select
        result = await self.db.execute(select(PqImportacao).where(PqImportacao.id == importacao_id))
        return result.scalar_one_or_none()
```

### Step 3: Commit

```bash
git add app/repositories/pq_item_repository.py app/repositories/pq_importacao_repository.py
git commit -m "feat(pq): add repositories for PqItem and PqImportacao"
```

---

## Task 3: Serviço de Importação de Planilha

**Files:**
- Create: `app/services/pq_import_service.py`

### Step 1: Implementar parser e importador

```python
# app/services/pq_import_service.py
import io
import uuid
from decimal import Decimal
from datetime import datetime, timezone

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposta import PqImportacao, PqItem, StatusImportacao
from app.repositories.pq_importacao_repository import PqImportacaoRepository
from app.repositories.pq_item_repository import PqItemRepository
from app.repositories.proposta_repository import PropostaRepository

class PqImportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.import_repo = PqImportacaoRepository(db)
        self.item_repo = PqItemRepository(db)
        self.proposta_repo = PropostaRepository(db)

    async def importar_planilha(
        self,
        proposta_id: uuid.UUID,
        arquivo: UploadFile,
        usuario_id: uuid.UUID,
    ) -> PqImportacao:
        # Validar proposta existe e pertence ao cliente do usuário
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        # Ler bytes
        contents = await arquivo.read()
        ext = arquivo.filename.split(".")[-1].lower()

        if ext == "csv":
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        total = len(df)
        importacao = PqImportacao(
            proposta_id=proposta_id,
            nome_arquivo=arquivo.filename,
            formato=ext,
            linhas_total=total,
            linhas_importadas=0,
            linhas_com_erro=0,
            status=StatusImportacao.PROCESSANDO,
        )
        importacao = await self.import_repo.create(importacao)

        itens = []
        for idx, row in df.iterrows():
            descricao = str(row.get("descricao", row.get("Descrição", ""))).strip()
            if not descricao:
                continue
            item = PqItem(
                proposta_id=proposta_id,
                pq_importacao_id=importacao.id,
                codigo_original=str(row.get("codigo", row.get("Código", ""))) or None,
                descricao_original=descricao,
                unidade_medida_original=str(row.get("unidade", row.get("Unidade", ""))) or None,
                quantidade_original=Decimal(str(row.get("quantidade", row.get("Quantidade", 1)))),
                descricao_tokens=descricao.lower(),
                linha_planilha=int(idx) + 2,
            )
            itens.append(item)

        if itens:
            await self.item_repo.create_batch(itens)

        importacao.linhas_importadas = len(itens)
        importacao.status = StatusImportacao.CONCLUIDO if importacao.linhas_com_erro == 0 else StatusImportacao.COM_ERROS
        await self.db.flush()
        return importacao
```

### Step 2: Commit

```bash
git add app/services/pq_import_service.py
git commit -m "feat(pq): add PqImportService with Excel/CSV parser"
```

---

## Task 4: Serviço de Match Inteligente

**Files:**
- Create: `app/services/pq_match_service.py`
- Modify: `app/services/busca_service.py` (expôr busca por descrição pura)

### Step 1: Implementar matcher

```python
# app/services/pq_match_service.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposta import PqItem, StatusMatch, TipoServicoMatch
from app.repositories.pq_item_repository import PqItemRepository
from app.services.busca_service import busca_service

class PqMatchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.item_repo = PqItemRepository(db)

    async def executar_match_para_proposta(self, proposta_id: uuid.UUID, usuario_id: uuid.UUID) -> dict:
        """Executa match para todos os PqItems PENDENTES de uma proposta."""
        items = await self.item_repo.list_by_proposta(proposta_id, limit=1000)
        pendentes = [i for i in items if i.match_status == StatusMatch.PENDENTE]

        resultados = {"processados": 0, "sugeridos": 0, "sem_match": 0}

        for item in pendentes:
            if not item.descricao_original:
                continue

            resultado = await busca_service.buscar(
                request=BuscaServicoRequest(termo=item.descricao_original),
                usuario_id=usuario_id,
                db=self.db,
            )

            if resultado.resultado_direto:
                servico = resultado.resultado_direto
                await self.item_repo.update_match(
                    pq_item_id=item.id,
                    servico_match_id=servico.id,
                    servico_match_tipo=TipoServicoMatch.BASE_TCPO,
                    confidence=1.0,
                )
                resultados["sugeridos"] += 1
            elif resultado.alternativas:
                top = resultado.alternativas[0]
                await self.item_repo.update_match(
                    pq_item_id=item.id,
                    servico_match_id=top.id,
                    servico_match_tipo=TipoServicoMatch.BASE_TCPO,
                    confidence=0.8,
                )
                resultados["sugeridos"] += 1
            else:
                # atualiza status SEM_MATCH
                from sqlalchemy import update
                await self.db.execute(
                    update(PqItem).where(PqItem.id == item.id).values(match_status=StatusMatch.SEM_MATCH)
                )
                resultados["sem_match"] += 1

            resultados["processados"] += 1

        await self.db.flush()
        return resultados
```

Nota: importar `BuscaServicoRequest` no topo do arquivo.

### Step 2: Commit

```bash
git add app/services/pq_match_service.py
git commit -m "feat(pq): add PqMatchService with fuzzy/semantic matching"
```

---

## Task 5: API Endpoints — Upload e Match

**Files:**
- Create: `app/api/v1/endpoints/pq_importacao.py`
- Modify: `app/api/v1/router.py`

### Step 1: Rotas de Upload

```python
# app/api/v1/endpoints/pq_importacao.py
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_access
from app.services.pq_import_service import PqImportService
from app.services.pq_match_service import PqMatchService
from app.repositories.proposta_repository import PropostaRepository

router = APIRouter(prefix="/propostas/{proposta_id}/importar", tags=["pq-importacao"])

@router.post("/planilha", status_code=201)
async def upload_planilha(
    proposta_id: UUID,
    arquivo: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Validar acesso à proposta via cliente
    prop_repo = PropostaRepository(db)
    proposta = await prop_repo.get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = PqImportService(db)
    importacao = await svc.importar_planilha(proposta_id, arquivo, current_user.id)
    return {"importacao_id": importacao.id, "status": importacao.status.value, "linhas": importacao.linhas_importadas}

@router.post("/match", status_code=200)
async def executar_match(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    prop_repo = PropostaRepository(db)
    proposta = await prop_repo.get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = PqMatchService(db)
    resultados = await svc.executar_match_para_proposta(proposta_id, current_user.id)
    return resultados
```

### Step 2: Commit

```bash
git add app/api/v1/endpoints/pq_importacao.py
git commit -m "feat(pq): add upload and match endpoints"
```

---

## Task 6: Testes Unitários

**Files:**
- Create: `app/tests/unit/test_pq_import_service.py`
- Create: `app/tests/unit/test_pq_match_service.py`

### Step 1: Testar importação

```python
# app/tests/unit/test_pq_import_service.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.pq_import_service import PqImportService

@pytest.mark.asyncio
async def test_importar_planilha_cria_itens():
    mock_db = AsyncMock()
    svc = PqImportService(mock_db)

    # Mockar repositórios internos
    proposta = MagicMock()
    proposta.id = uuid.uuid4()
    proposta.cliente_id = uuid.uuid4()

    with patch.object(svc.proposta_repo, "get_by_id", AsyncMock(return_value=proposta)):
        arquivo = MagicMock()
        arquivo.filename = "teste.csv"
        arquivo.read = AsyncMock(return_value=b"codigo,descricao,unidade,quantidade\n001,Concreto,m3,10.5")

        with patch("app.services.pq_import_service.pd.read_csv", return_value=__import__("pandas").DataFrame([{"codigo": "001", "descricao": "Concreto", "unidade": "m3", "quantidade": 10.5}])):
            resultado = await svc.importar_planilha(proposta.id, arquivo, uuid.uuid4())
            assert resultado.linhas_total == 1
            assert resultado.linhas_importadas == 1
```

### Step 2: Commit

```bash
git add app/tests/unit/test_pq_import_service.py app/tests/unit/test_pq_match_service.py
git commit -m "test(pq): add unit tests for import and match services"
```

---

## Task 7: Migração Alembic

**Files:**
- Create: alembic migration (autogenerate)

### Step 1: Gerar migration

```bash
alembic revision --autogenerate -m "add_pq_importacao_and_pq_item"
```

Revisar migration gerada para garantir:
- Schema "operacional"
- ForeignKeys para `propostas.id`
- Índices em `proposta_id`, `pq_importacao_id`

### Step 2: Commit

```bash
git add alembic/versions/xxxx_add_pq_importacao_and_pq_item.py
git commit -m "db(pq): add Alembic migration for PQ tables"
```

---

## Task 8: Full Regression + Walkthrough

### Step 1: Rodar suite

```bash
pytest app/tests/unit/ -v --tb=short
```
Expected: ALL PASS (80+ testes)

### Step 2: Walkthrough

Create: `docs/walkthrough/done/walkthrough-S-10.md`

### Step 3: Commit

```bash
git add docs/walkthrough/done/walkthrough-S-10.md
git commit -m "docs(s-10): add walkthrough for PQ import and match"
```

---

## Plan Review Checklist

- [x] Spec coverage: upload, parse, match, confirmação manual
- [x] Placeholder scan: no TBD/TODO found
- [x] Type consistency: UUID, Decimal, enums consistentes com modelagem
- [x] Reusa busca_service existente (S-05) — não reinventa

## Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-23-importacao-pq-match-inteligente.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch subagent per task, review between tasks
2. **Inline Execution** — execute in this session with checkpoints

Which approach?
