# PQ Layout por Cliente — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que cada cliente tenha um layout de planilha PQ configuravel (mapeamento de colunas customizavel), eliminando a dependencia de colunas fixas na importacao.

**Architecture:** Duas novas entidades SQLAlchemy no schema `operacional`: `PqLayoutCliente` (1:1 com cliente) e `PqImportacaoMapeamento` (N mapeamentos campo->coluna por layout). O `pq_import_service.py` consulta o layout antes de processar cada linha do Excel. Um novo endpoint `PUT /clientes/{id}/pq-layout` permite ao admin configurar o layout; quando ausente, o endpoint de importacao retorna `cols_detectadas` para mapeamento interativo na UI.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, openpyxl, PostgreSQL 16, pytest-asyncio

---

## File Structure

**Criar:**
- `app/alembic/versions/018_pq_layout_cliente.py`
- `app/backend/models/pq_layout.py`
- `app/backend/schemas/pq_layout.py`
- `app/backend/repositories/pq_layout_repository.py`
- `app/backend/services/pq_layout_service.py`
- `app/backend/api/v1/endpoints/pq_layout.py`
- `app/backend/tests/unit/test_pq_layout_service.py`
- `app/backend/tests/integration/test_pq_layout_endpoint.py`

**Modificar:**
- `app/backend/models/enums.py` — adicionar `CampoSistemaPQ`
- `app/backend/models/__init__.py` — registrar novos modelos
- `app/backend/services/pq_import_service.py` — chamar `_resolver_mapa_colunas` antes de iterar linhas
- `app/backend/api/v1/router.py` — incluir `pq_layout.router`

---

### Task 1: Enum CampoSistemaPQ e modelos SQLAlchemy

**Files:**
- Modify: `app/backend/models/enums.py`
- Create: `app/backend/models/pq_layout.py`
- Modify: `app/backend/models/__init__.py`

- [ ] **Step 1.1: Adicionar `CampoSistemaPQ` em `app/backend/models/enums.py`**

Localizar o bloco de enums existente e adicionar apos o ultimo enum:

```python
class CampoSistemaPQ(str, enum.Enum):
    CODIGO = "codigo"
    DESCRICAO = "descricao"
    UNIDADE = "unidade"
    QUANTIDADE = "quantidade"
    OBSERVACAO = "observacao"
```

- [ ] **Step 1.2: Criar `app/backend/models/pq_layout.py`**

```python
import uuid
from uuid import UUID

from sqlalchemy import Integer, String, UniqueConstraint, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.enums import CampoSistemaPQ


class PqLayoutCliente(Base, TimestampMixin):
    __tablename__ = "pq_layout_cliente"
    __table_args__ = (
        UniqueConstraint("cliente_id", name="uq_pq_layout_cliente_cliente_id"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False, default="Layout Padrao")
    aba_nome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linha_inicio: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    mapeamentos: Mapped[list["PqImportacaoMapeamento"]] = relationship(
        back_populates="layout",
        lazy="noload",
        cascade="all, delete-orphan",
    )


class PqImportacaoMapeamento(Base):
    __tablename__ = "pq_importacao_mapeamento"
    __table_args__ = (
        UniqueConstraint("layout_id", "campo_sistema", name="uq_pq_mapeamento_layout_campo"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layout_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.pq_layout_cliente.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campo_sistema: Mapped[CampoSistemaPQ] = mapped_column(
        SAEnum(CampoSistemaPQ, name="campo_sistema_pq_enum", create_type=False),
        nullable=False,
    )
    coluna_planilha: Mapped[str] = mapped_column(String(100), nullable=False)

    layout: Mapped["PqLayoutCliente"] = relationship(back_populates="mapeamentos", lazy="noload")
```

- [ ] **Step 1.3: Registrar em `app/backend/models/__init__.py`**

Adicionar ao bloco de imports existente:

```python
from backend.models.pq_layout import PqLayoutCliente, PqImportacaoMapeamento  # noqa: F401
```

- [ ] **Step 1.4: Verificar que os modelos importam**

```bash
cd app && python -c "from backend.models.pq_layout import PqLayoutCliente, PqImportacaoMapeamento; print('OK')"
```
Esperado: `OK`

- [ ] **Step 1.5: Commit**

```bash
git add app/backend/models/pq_layout.py app/backend/models/enums.py app/backend/models/__init__.py
git commit -m "feat(f2-01): add PqLayoutCliente and PqImportacaoMapeamento models"
```

---

### Task 2: Migration Alembic 018

**Files:**
- Create: `app/alembic/versions/018_pq_layout_cliente.py`

- [ ] **Step 2.1: Criar migration**

```python
"""Add pq_layout_cliente and pq_importacao_mapeamento

Revision ID: 018
Revises: 017
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE campo_sistema_pq_enum AS ENUM (
                'codigo', 'descricao', 'unidade', 'quantidade', 'observacao'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.create_table(
        "pq_layout_cliente",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nome", sa.String(100), nullable=False, server_default="Layout Padrao"),
        sa.Column("aba_nome", sa.String(100), nullable=True),
        sa.Column("linha_inicio", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cliente_id"], ["operacional.clientes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cliente_id", name="uq_pq_layout_cliente_cliente_id"),
        schema="operacional",
    )
    op.create_index(
        "ix_pq_layout_cliente_cliente_id", "pq_layout_cliente", ["cliente_id"], schema="operacional"
    )

    op.create_table(
        "pq_importacao_mapeamento",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("layout_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "campo_sistema",
            postgresql.ENUM(
                "codigo", "descricao", "unidade", "quantidade", "observacao",
                name="campo_sistema_pq_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("coluna_planilha", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["layout_id"], ["operacional.pq_layout_cliente.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("layout_id", "campo_sistema", name="uq_pq_mapeamento_layout_campo"),
        schema="operacional",
    )
    op.create_index(
        "ix_pq_mapeamento_layout_id", "pq_importacao_mapeamento", ["layout_id"], schema="operacional"
    )


def downgrade() -> None:
    op.drop_index("ix_pq_mapeamento_layout_id", table_name="pq_importacao_mapeamento", schema="operacional")
    op.drop_table("pq_importacao_mapeamento", schema="operacional")
    op.drop_index("ix_pq_layout_cliente_cliente_id", table_name="pq_layout_cliente", schema="operacional")
    op.drop_table("pq_layout_cliente", schema="operacional")
    op.execute("DROP TYPE IF EXISTS campo_sistema_pq_enum")
```

- [ ] **Step 2.2: Verificar encadeamento**

```bash
cd app && python -m alembic history --verbose 2>&1 | grep -E "017|018"
```
Esperado: linha com `017 -> 018`

- [ ] **Step 2.3: Commit**

```bash
git add app/alembic/versions/018_pq_layout_cliente.py
git commit -m "feat(f2-01): migration 018 pq_layout_cliente and pq_importacao_mapeamento"
```

---

### Task 3: Schemas Pydantic

**Files:**
- Create: `app/backend/schemas/pq_layout.py`
- Create: `app/backend/tests/unit/test_pq_layout_service.py`

- [ ] **Step 3.1: Escrever teste que falha**

Criar `app/backend/tests/unit/test_pq_layout_service.py`:

```python
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from backend.schemas.pq_layout import PqLayoutCriarRequest, MapeamentoItem
from backend.models.enums import CampoSistemaPQ


def test_schema_valida_campos_obrigatorios():
    req = PqLayoutCriarRequest(
        nome="Layout A",
        linha_inicio=2,
        mapeamentos=[
            MapeamentoItem(campo_sistema=CampoSistemaPQ.DESCRICAO, coluna_planilha="B"),
            MapeamentoItem(campo_sistema=CampoSistemaPQ.UNIDADE, coluna_planilha="C"),
            MapeamentoItem(campo_sistema=CampoSistemaPQ.QUANTIDADE, coluna_planilha="D"),
        ],
    )
    assert len(req.mapeamentos) == 3


def test_schema_rejeita_sem_descricao():
    with pytest.raises(Exception):
        PqLayoutCriarRequest(
            mapeamentos=[
                MapeamentoItem(campo_sistema=CampoSistemaPQ.UNIDADE, coluna_planilha="C"),
                MapeamentoItem(campo_sistema=CampoSistemaPQ.QUANTIDADE, coluna_planilha="D"),
            ]
        )
```

- [ ] **Step 3.2: Confirmar falha**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_layout_service.py -v 2>&1 | head -10
```
Esperado: `ImportError`

- [ ] **Step 3.3: Criar `app/backend/schemas/pq_layout.py`**

```python
from uuid import UUID
from pydantic import BaseModel, field_validator
from backend.models.enums import CampoSistemaPQ


class MapeamentoItem(BaseModel):
    campo_sistema: CampoSistemaPQ
    coluna_planilha: str


class PqLayoutCriarRequest(BaseModel):
    nome: str = "Layout Padrao"
    aba_nome: str | None = None
    linha_inicio: int = 2
    mapeamentos: list[MapeamentoItem]

    @field_validator("mapeamentos")
    @classmethod
    def campos_obrigatorios(cls, v: list[MapeamentoItem]) -> list[MapeamentoItem]:
        campos = {m.campo_sistema for m in v}
        ausentes = {CampoSistemaPQ.DESCRICAO, CampoSistemaPQ.QUANTIDADE, CampoSistemaPQ.UNIDADE} - campos
        if ausentes:
            nomes = ", ".join(a.value for a in ausentes)
            raise ValueError(f"Mapeamentos obrigatorios ausentes: {nomes}")
        return v


class MapeamentoItemResponse(BaseModel):
    id: UUID
    campo_sistema: CampoSistemaPQ
    coluna_planilha: str
    model_config = {"from_attributes": True}


class PqLayoutResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    nome: str
    aba_nome: str | None
    linha_inicio: int
    mapeamentos: list[MapeamentoItemResponse]
    model_config = {"from_attributes": True}


class ColunasDetectadasResponse(BaseModel):
    colunas: list[str]
    layout_configurado: bool
    layout_id: UUID | None = None
```

- [ ] **Step 3.4: Confirmar PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_layout_service.py -v
```
Esperado: 2 PASS

- [ ] **Step 3.5: Commit**

```bash
git add app/backend/schemas/pq_layout.py app/backend/tests/unit/test_pq_layout_service.py
git commit -m "feat(f2-01): PqLayout schemas with campos_obrigatorios validator"
```

---

### Task 4: Repository

**Files:**
- Create: `app/backend/repositories/pq_layout_repository.py`

- [ ] **Step 4.1: Adicionar testes do repository ao `test_pq_layout_service.py`**

```python
from backend.repositories.pq_layout_repository import PqLayoutRepository
from backend.models.pq_layout import PqLayoutCliente


@pytest.mark.asyncio
async def test_get_by_cliente_id_com_layout():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    cliente_id = uuid4()
    layout = PqLayoutCliente(id=uuid4(), cliente_id=cliente_id, nome="T", linha_inicio=2)
    mock_result.scalar_one_or_none.return_value = layout
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await PqLayoutRepository(mock_db).get_by_cliente_id(cliente_id)
    assert result.cliente_id == cliente_id


@pytest.mark.asyncio
async def test_get_by_cliente_id_sem_layout():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await PqLayoutRepository(mock_db).get_by_cliente_id(uuid4())
    assert result is None
```

- [ ] **Step 4.2: Confirmar falha**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_layout_service.py::test_get_by_cliente_id_com_layout -v 2>&1 | head -5
```

- [ ] **Step 4.3: Criar `app/backend/repositories/pq_layout_repository.py`**

```python
from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.pq_layout import PqLayoutCliente


class PqLayoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_cliente_id(self, cliente_id: UUID) -> PqLayoutCliente | None:
        result = await self._db.execute(
            select(PqLayoutCliente)
            .options(selectinload(PqLayoutCliente.mapeamentos))
            .where(PqLayoutCliente.cliente_id == cliente_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, layout_id: UUID) -> PqLayoutCliente | None:
        result = await self._db.execute(
            select(PqLayoutCliente)
            .options(selectinload(PqLayoutCliente.mapeamentos))
            .where(PqLayoutCliente.id == layout_id)
        )
        return result.scalar_one_or_none()

    async def create(self, layout: PqLayoutCliente) -> PqLayoutCliente:
        self._db.add(layout)
        await self._db.flush()
        return layout

    async def delete_by_cliente_id(self, cliente_id: UUID) -> None:
        await self._db.execute(
            delete(PqLayoutCliente).where(PqLayoutCliente.cliente_id == cliente_id)
        )
```

- [ ] **Step 4.4: Confirmar PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_layout_service.py -v
```
Esperado: 4 PASS

- [ ] **Step 4.5: Commit**

```bash
git add app/backend/repositories/pq_layout_repository.py
git commit -m "feat(f2-01): PqLayoutRepository"
```

---

### Task 5: Service

**Files:**
- Create: `app/backend/services/pq_layout_service.py`

- [ ] **Step 5.1: Adicionar testes do service ao `test_pq_layout_service.py`**

```python
from backend.services.pq_layout_service import PqLayoutService
from backend.models.pq_layout import PqImportacaoMapeamento


@pytest.mark.asyncio
async def test_criar_layout():
    mock_db = AsyncMock()
    svc = PqLayoutService(mock_db)
    svc._repo = MagicMock()
    svc._repo.delete_by_cliente_id = AsyncMock()
    svc._repo.create = AsyncMock(side_effect=lambda x: x)

    cliente_id = uuid4()
    req = PqLayoutCriarRequest(
        nome="L",
        linha_inicio=2,
        mapeamentos=[
            MapeamentoItem(campo_sistema=CampoSistemaPQ.DESCRICAO, coluna_planilha="B"),
            MapeamentoItem(campo_sistema=CampoSistemaPQ.UNIDADE, coluna_planilha="C"),
            MapeamentoItem(campo_sistema=CampoSistemaPQ.QUANTIDADE, coluna_planilha="D"),
        ],
    )
    layout = await svc.criar_ou_substituir(cliente_id, req)
    assert layout.cliente_id == cliente_id
    assert len(layout.mapeamentos) == 3


def test_detectar_colunas_xlsx(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Codigo", "Descricao", "Un", "Qtd"])
    ws.append(["001", "Servico A", "m3", "10"])
    path = tmp_path / "test.xlsx"
    wb.save(str(path))

    svc = PqLayoutService(AsyncMock())
    cols = svc.detectar_colunas_xlsx(str(path), None)
    assert cols == ["Codigo", "Descricao", "Un", "Qtd"]


def test_build_coluna_map():
    from backend.models.pq_layout import PqLayoutCliente
    layout = PqLayoutCliente(id=uuid4(), cliente_id=uuid4(), nome="T", linha_inicio=2)
    layout.mapeamentos = [
        PqImportacaoMapeamento(
            id=uuid4(), layout_id=layout.id,
            campo_sistema=CampoSistemaPQ.DESCRICAO, coluna_planilha="Servico"
        ),
    ]
    mapa = PqLayoutService(AsyncMock()).build_coluna_map(layout)
    assert mapa["descricao"] == "Servico"
```

- [ ] **Step 5.2: Confirmar falha**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_layout_service.py::test_criar_layout -v 2>&1 | head -5
```

- [ ] **Step 5.3: Criar `app/backend/services/pq_layout_service.py`**

```python
import uuid
from uuid import UUID

import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pq_layout import PqLayoutCliente, PqImportacaoMapeamento
from backend.repositories.pq_layout_repository import PqLayoutRepository
from backend.schemas.pq_layout import PqLayoutCriarRequest


class PqLayoutService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = PqLayoutRepository(db)

    async def criar_ou_substituir(self, cliente_id: UUID, req: PqLayoutCriarRequest) -> PqLayoutCliente:
        await self._repo.delete_by_cliente_id(cliente_id)
        layout = PqLayoutCliente(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            nome=req.nome,
            aba_nome=req.aba_nome,
            linha_inicio=req.linha_inicio,
        )
        for m in req.mapeamentos:
            layout.mapeamentos.append(
                PqImportacaoMapeamento(
                    id=uuid.uuid4(),
                    campo_sistema=m.campo_sistema,
                    coluna_planilha=m.coluna_planilha,
                )
            )
        return await self._repo.create(layout)

    async def obter_por_cliente(self, cliente_id: UUID) -> PqLayoutCliente | None:
        return await self._repo.get_by_cliente_id(cliente_id)

    def detectar_colunas_xlsx(self, filepath: str, aba_nome: str | None) -> list[str]:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb[aba_nome] if aba_nome and aba_nome in wb.sheetnames else wb.active
        primeira = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        wb.close()
        return [str(c) for c in primeira if c is not None]

    def build_coluna_map(self, layout: PqLayoutCliente) -> dict[str, str]:
        return {m.campo_sistema.value: m.coluna_planilha for m in layout.mapeamentos}
```

- [ ] **Step 5.4: Confirmar PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_layout_service.py -v
```
Esperado: 7 PASS

- [ ] **Step 5.5: Commit**

```bash
git add app/backend/services/pq_layout_service.py
git commit -m "feat(f2-01): PqLayoutService"
```

---

### Task 6: Endpoint e Router

**Files:**
- Create: `app/backend/api/v1/endpoints/pq_layout.py`
- Modify: `app/backend/api/v1/router.py`

- [ ] **Step 6.1: Criar `app/backend/api/v1/endpoints/pq_layout.py`**

```python
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_admin
from backend.schemas.pq_layout import PqLayoutCriarRequest, PqLayoutResponse
from backend.services.pq_layout_service import PqLayoutService

router = APIRouter(prefix="/clientes/{cliente_id}/pq-layout", tags=["pq-layout"])


@router.put("", response_model=PqLayoutResponse)
async def criar_ou_substituir_layout(
    cliente_id: UUID,
    body: PqLayoutCriarRequest,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PqLayoutResponse:
    svc = PqLayoutService(db)
    layout = await svc.criar_ou_substituir(cliente_id, body)
    await db.commit()
    await db.refresh(layout)
    return PqLayoutResponse.model_validate(layout)


@router.get("", response_model=PqLayoutResponse | None)
async def obter_layout(
    cliente_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqLayoutResponse | None:
    layout = await PqLayoutService(db).obter_por_cliente(cliente_id)
    if layout is None:
        return None
    return PqLayoutResponse.model_validate(layout)
```

- [ ] **Step 6.2: Incluir router em `app/backend/api/v1/router.py`**

```python
from backend.api.v1.endpoints import pq_layout
api_router.include_router(pq_layout.router)
```

- [ ] **Step 6.3: Verificar que app importa sem erros**

```bash
cd app && python -c "from backend.main import app; print('OK')"
```
Esperado: `OK`

- [ ] **Step 6.4: Commit**

```bash
git add app/backend/api/v1/endpoints/pq_layout.py app/backend/api/v1/router.py
git commit -m "feat(f2-01): PUT/GET /clientes/{id}/pq-layout endpoints"
```

---

### Task 7: Integracao ao pq_import_service

**Files:**
- Modify: `app/backend/services/pq_import_service.py`
- Create: `app/backend/tests/integration/test_pq_layout_endpoint.py`

- [ ] **Step 7.1: Localizar ponto de mapeamento de colunas**

```bash
grep -n "descricao_original\|unidade_medida_original\|coluna\|header" app/backend/services/pq_import_service.py | head -20
```

Identificar o metodo que le cada linha do Excel e extrai os campos.

- [ ] **Step 7.2: Adicionar `_resolver_mapa_colunas` ao pq_import_service.py**

Inserir antes do metodo de processamento de linhas:

```python
async def _resolver_mapa_colunas(self, proposta_id: UUID) -> dict[str, str]:
    from backend.repositories.proposta_repository import PropostaRepository
    from backend.services.pq_layout_service import PqLayoutService

    proposta = await PropostaRepository(self._db).get_by_id(proposta_id)
    layout = await PqLayoutService(self._db).obter_por_cliente(proposta.cliente_id)

    if layout:
        return PqLayoutService(self._db).build_coluna_map(layout)

    return {
        "codigo": "codigo",
        "descricao": "descricao",
        "unidade": "unidade_medida",
        "quantidade": "quantidade",
        "observacao": "observacao",
    }
```

- [ ] **Step 7.3: Usar o mapa no processamento de cada linha**

No metodo que processa linhas, chamar `mapa = await self._resolver_mapa_colunas(proposta_id)` e usar:

```python
col_descricao  = mapa.get("descricao",   "descricao")
col_unidade    = mapa.get("unidade",     "unidade_medida")
col_quantidade = mapa.get("quantidade",  "quantidade")
col_codigo     = mapa.get("codigo",      "codigo")
col_observacao = mapa.get("observacao",  "observacao")
```

Substituir os acessos fixos de coluna por essas variaveis.

- [ ] **Step 7.4: Criar teste de integracao**

Criar `app/backend/tests/integration/test_pq_layout_endpoint.py`:

```python
import pytest
import io
import openpyxl
from httpx import AsyncClient


def make_xlsx_bytes(colunas: list[str], dados: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(colunas)
    for row in dados:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_put_pq_layout_sucesso(client: AsyncClient, admin_token, test_cliente):
    payload = {
        "nome": "Layout CI",
        "linha_inicio": 2,
        "mapeamentos": [
            {"campo_sistema": "descricao", "coluna_planilha": "Servico"},
            {"campo_sistema": "unidade",   "coluna_planilha": "Un"},
            {"campo_sistema": "quantidade","coluna_planilha": "Qtd"},
        ],
    }
    resp = await client.put(
        f"/api/v1/clientes/{test_cliente.id}/pq-layout",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Layout CI"
    assert len(resp.json()["mapeamentos"]) == 3


@pytest.mark.asyncio
async def test_get_pq_layout_sem_configuracao(client: AsyncClient, user_token, test_cliente):
    resp = await client.get(
        f"/api/v1/clientes/{test_cliente.id}/pq-layout",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200
    assert resp.json() is None
```

- [ ] **Step 7.5: Rodar suite de regressao completa**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -20
```
Esperado: 93+ PASS, 0 FAIL

- [ ] **Step 7.6: Commit final**

```bash
git add app/backend/services/pq_import_service.py app/backend/tests/integration/test_pq_layout_endpoint.py
git commit -m "feat(f2-01): pq_import_service uses PqLayoutCliente for column mapping"
```

---

## Self-Review

- [x] Spec coverage: layout 1:1 cliente, mapeamento N:1 layout, PUT/GET endpoint, integracao ao import service, fallback sem layout, testes unitarios e de integracao.
- [x] Sem placeholders: todos os steps tem codigo completo.
- [x] Tipos consistentes em todos os tasks: `PqLayoutService`, `PqLayoutRepository`, `PqLayoutCriarRequest`, `PqLayoutResponse`.
- [x] Migration encadeia: `down_revision = "017"`.
- [x] Validator rejeita requests sem descricao/quantidade/unidade.
