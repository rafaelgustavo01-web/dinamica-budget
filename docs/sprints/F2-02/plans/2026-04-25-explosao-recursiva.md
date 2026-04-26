# Explosao Recursiva de Composicoes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que composicoes de proposta explodam em sub-niveis (composicao dentro de composicao), registrando arvore completa de insumos com rastreabilidade de nivel e origem.

**Architecture:** Adicionar quatro colunas em `proposta_item_composicoes`: `pai_composicao_id` (FK self-referencial), `nivel` (int), `e_composicao` (bool — insumo possui composicao propria), `composicao_explodida` (bool — sub-explosao ja executada). O `cpu_explosao_service.py` e atualizado para sinalizar insumos com sub-composicao e executar explosao recursiva. Novo endpoint `POST /propostas/{id}/cpu/itens/{composicao_id}/explodir-sub`. Guard de profundidade: nivel > 5 retorna 422.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL 16, pytest-asyncio

---

## File Structure

**Criar:**
- `app/alembic/versions/019_recursao_composicao.py`
- `app/backend/tests/unit/test_explosao_recursiva.py`

**Modificar:**
- `app/backend/models/proposta.py` — 4 colunas + relationship self-ref em `PropostaItemComposicao`
- `app/backend/services/cpu_explosao_service.py` — `_assert_nivel_permitido`, `_verificar_e_marcar_sub_composicao`, `explodir_sub_composicao`
- `app/backend/api/v1/endpoints/cpu_geracao.py` — endpoint `explodir-sub`

---

### Task 1: Migration 019

**Files:**
- Create: `app/alembic/versions/019_recursao_composicao.py`

- [ ] **Step 1.1: Criar migration**

```python
"""Add recursive columns to proposta_item_composicoes

Revision ID: 019
Revises: 018
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("pai_composicao_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="operacional",
    )
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("nivel", sa.Integer(), nullable=False, server_default="0"),
        schema="operacional",
    )
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("e_composicao", sa.Boolean(), nullable=False, server_default="false"),
        schema="operacional",
    )
    op.add_column(
        "proposta_item_composicoes",
        sa.Column("composicao_explodida", sa.Boolean(), nullable=False, server_default="false"),
        schema="operacional",
    )
    op.create_foreign_key(
        "fk_pic_pai_composicao_id",
        "proposta_item_composicoes",
        "proposta_item_composicoes",
        ["pai_composicao_id"],
        ["id"],
        source_schema="operacional",
        referent_schema="operacional",
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_pic_pai_composicao_id",
        "proposta_item_composicoes",
        ["pai_composicao_id"],
        schema="operacional",
    )


def downgrade() -> None:
    op.drop_index("ix_pic_pai_composicao_id", table_name="proposta_item_composicoes", schema="operacional")
    op.drop_constraint(
        "fk_pic_pai_composicao_id", "proposta_item_composicoes",
        schema="operacional", type_="foreignkey",
    )
    op.drop_column("proposta_item_composicoes", "composicao_explodida", schema="operacional")
    op.drop_column("proposta_item_composicoes", "e_composicao", schema="operacional")
    op.drop_column("proposta_item_composicoes", "nivel", schema="operacional")
    op.drop_column("proposta_item_composicoes", "pai_composicao_id", schema="operacional")
```

- [ ] **Step 1.2: Verificar encadeamento**

```bash
cd app && python -m alembic history --verbose 2>&1 | grep -E "018|019"
```
Esperado: linha com `018 -> 019`

- [ ] **Step 1.3: Commit**

```bash
git add app/alembic/versions/019_recursao_composicao.py
git commit -m "feat(f2-02): migration 019 recursive columns in proposta_item_composicoes"
```

---

### Task 2: Atualizar modelo PropostaItemComposicao

**Files:**
- Modify: `app/backend/models/proposta.py`

- [ ] **Step 2.1: Adicionar `Boolean` ao import SQLAlchemy**

No topo de `app/backend/models/proposta.py`, garantir que `Boolean` esta no import:

```python
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text
```

- [ ] **Step 2.2: Adicionar 4 colunas e relationships self-ref em `PropostaItemComposicao`**

Apos a coluna `fonte_custo`, adicionar:

```python
pai_composicao_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("operacional.proposta_item_composicoes.id", ondelete="CASCADE"),
    nullable=True,
    index=True,
)
nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
e_composicao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
composicao_explodida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

sub_composicoes: Mapped[list["PropostaItemComposicao"]] = relationship(
    back_populates="pai",
    lazy="noload",
    cascade="all, delete-orphan",
    foreign_keys="[PropostaItemComposicao.pai_composicao_id]",
)
pai: Mapped["PropostaItemComposicao | None"] = relationship(
    back_populates="sub_composicoes",
    lazy="noload",
    foreign_keys="[PropostaItemComposicao.pai_composicao_id]",
    remote_side="[PropostaItemComposicao.id]",
)
```

- [ ] **Step 2.3: Verificar import do modelo**

```bash
cd app && python -c "from backend.models.proposta import PropostaItemComposicao; c = PropostaItemComposicao(); print(c.nivel, c.e_composicao)"
```
Esperado: `0 False`

- [ ] **Step 2.4: Commit**

```bash
git add app/backend/models/proposta.py
git commit -m "feat(f2-02): PropostaItemComposicao with pai_composicao_id, nivel, e_composicao, composicao_explodida"
```

---

### Task 3: Testes da logica de recursao

**Files:**
- Create: `app/backend/tests/unit/test_explosao_recursiva.py`

- [ ] **Step 3.1: Criar testes que falham**

```python
import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from backend.models.proposta import PropostaItemComposicao
from backend.models.enums import TipoRecurso


def _make_pic(nivel=0, e_composicao=False, pai_id=None) -> PropostaItemComposicao:
    c = PropostaItemComposicao()
    c.id = uuid.uuid4()
    c.proposta_item_id = uuid.uuid4()
    c.descricao_insumo = "Insumo Teste"
    c.unidade_medida = "UN"
    c.quantidade_consumo = Decimal("1.0")
    c.tipo_recurso = TipoRecurso.INSUMO
    c.nivel = nivel
    c.e_composicao = e_composicao
    c.composicao_explodida = False
    c.pai_composicao_id = pai_id
    c.insumo_base_id = uuid.uuid4()
    c.insumo_proprio_id = None
    c.fonte_custo = "base_tcpo"
    c.sub_composicoes = []
    return c


def test_pic_campos_padrao():
    c = _make_pic()
    assert c.nivel == 0
    assert not c.e_composicao
    assert not c.composicao_explodida
    assert c.pai_composicao_id is None


def test_pic_nivel_incrementado():
    pai = _make_pic(nivel=0, e_composicao=True)
    filho = _make_pic(nivel=1, pai_id=pai.id)
    assert filho.nivel == 1
    assert filho.pai_composicao_id == pai.id


def test_guard_nivel_permitido_aceita_ate_5():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    svc = CpuExplosaoService(AsyncMock())
    for n in range(6):
        svc._assert_nivel_permitido(n)  # nao deve levantar


def test_guard_nivel_rejeita_acima_de_5():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    svc = CpuExplosaoService(AsyncMock())
    with pytest.raises(ValueError, match="Profundidade maxima"):
        svc._assert_nivel_permitido(6)


@pytest.mark.asyncio
async def test_explodir_sub_rejeita_ja_explodida():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository

    pic = _make_pic(e_composicao=True)
    pic.composicao_explodida = True

    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(PropostaItemComposicaoRepository, "get_by_id", return_value=pic):
        with pytest.raises(ValueError, match="ja foi explodida"):
            await svc.explodir_sub_composicao(uuid.uuid4(), pic.id)


@pytest.mark.asyncio
async def test_explodir_sub_rejeita_sem_composicao():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository

    pic = _make_pic(e_composicao=False)
    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(PropostaItemComposicaoRepository, "get_by_id", return_value=pic):
        with pytest.raises(ValueError, match="nao possui composicao"):
            await svc.explodir_sub_composicao(uuid.uuid4(), pic.id)
```

Adicionar `from unittest.mock import patch` ao import inicial.

- [ ] **Step 3.2: Confirmar falha nos testes de guard**

```bash
cd app && python -m pytest backend/tests/unit/test_explosao_recursiva.py -v 2>&1 | tail -20
```
Esperado: `test_guard_nivel_rejeita_acima_de_5` FAIL — `AttributeError: _assert_nivel_permitido`

- [ ] **Step 3.3: Commit dos testes**

```bash
git add app/backend/tests/unit/test_explosao_recursiva.py
git commit -m "test(f2-02): failing tests for recursive explosion guard and validation"
```

---

### Task 4: Atualizar cpu_explosao_service

**Files:**
- Modify: `app/backend/services/cpu_explosao_service.py`

- [ ] **Step 4.1: Localizar metodo de explosao existente**

```bash
grep -n "def \|async def " app/backend/services/cpu_explosao_service.py
```

Identificar onde `PropostaItemComposicao` e instanciado.

- [ ] **Step 4.2: Adicionar `_assert_nivel_permitido`**

```python
def _assert_nivel_permitido(self, nivel: int) -> None:
    if nivel > 5:
        raise ValueError(
            f"Profundidade maxima de explosao atingida (nivel {nivel}). Limite: 5."
        )
```

- [ ] **Step 4.3: Adicionar `_verificar_e_marcar_sub_composicao`**

```python
async def _verificar_e_marcar_sub_composicao(
    self, composicao: PropostaItemComposicao
) -> None:
    if not composicao.insumo_base_id:
        return
    from backend.repositories.composicao_base_repository import ComposicaoBaseRepository
    existe = await ComposicaoBaseRepository(self._db).existe_composicao_para(
        composicao.insumo_base_id
    )
    if existe:
        composicao.e_composicao = True
```

- [ ] **Step 4.4: Chamar `_verificar_e_marcar_sub_composicao` apos criar cada composicao raiz**

No metodo existente de explosao de nivel 0, apos instanciar cada `PropostaItemComposicao`, adicionar:

```python
await self._verificar_e_marcar_sub_composicao(composicao)
```

Tambem garantir que ao criar a composicao raiz os campos novos sejam passados com defaults:

```python
composicao = PropostaItemComposicao(
    # ... campos existentes ...
    pai_composicao_id=None,
    nivel=0,
    e_composicao=False,
    composicao_explodida=False,
)
```

- [ ] **Step 4.5: Implementar `explodir_sub_composicao`**

```python
async def explodir_sub_composicao(
    self,
    proposta_id: UUID,
    composicao_id: UUID,
) -> list[PropostaItemComposicao]:
    import uuid as uuid_mod
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
    from backend.repositories.composicao_base_repository import ComposicaoBaseRepository

    repo = PropostaItemComposicaoRepository(self._db)
    composicao = await repo.get_by_id(composicao_id)

    if composicao is None:
        raise ValueError(f"Composicao {composicao_id} nao encontrada.")
    if composicao.composicao_explodida:
        raise ValueError("Sub-composicao ja foi explodida.")
    if not composicao.e_composicao:
        raise ValueError("Este insumo nao possui composicao propria.")

    proximo_nivel = composicao.nivel + 1
    self._assert_nivel_permitido(proximo_nivel)

    insumos = await ComposicaoBaseRepository(self._db).listar_por_servico(
        composicao.insumo_base_id
    )

    filhos: list[PropostaItemComposicao] = []
    for insumo in insumos:
        filho = PropostaItemComposicao(
            id=uuid_mod.uuid4(),
            proposta_item_id=composicao.proposta_item_id,
            insumo_base_id=insumo.insumo_base_id,
            insumo_proprio_id=insumo.insumo_proprio_id,
            descricao_insumo=insumo.descricao_insumo or "",
            unidade_medida=insumo.unidade_medida or "UN",
            quantidade_consumo=insumo.coeficiente * composicao.quantidade_consumo,
            tipo_recurso=insumo.tipo_recurso,
            fonte_custo="base_tcpo",
            pai_composicao_id=composicao.id,
            nivel=proximo_nivel,
            e_composicao=False,
            composicao_explodida=False,
        )
        await self._verificar_e_marcar_sub_composicao(filho)
        self._db.add(filho)
        filhos.append(filho)

    composicao.composicao_explodida = True
    await self._db.flush()
    return filhos
```

- [ ] **Step 4.6: Rodar testes**

```bash
cd app && python -m pytest backend/tests/unit/test_explosao_recursiva.py -v
```
Esperado: 6 PASS

- [ ] **Step 4.7: Commit**

```bash
git add app/backend/services/cpu_explosao_service.py
git commit -m "feat(f2-02): recursive explosion with depth guard in cpu_explosao_service"
```

---

### Task 5: Endpoint explodir-sub

**Files:**
- Modify: `app/backend/api/v1/endpoints/cpu_geracao.py`

- [ ] **Step 5.1: Garantir HTTPException no import**

No topo de `cpu_geracao.py`, garantir:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

- [ ] **Step 5.2: Adicionar endpoint apos `listar_cpu_itens`**

```python
@router.post(
    "/itens/{composicao_id}/explodir-sub",
    status_code=201,
)
async def explodir_sub_composicao(
    proposta_id: UUID,
    composicao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    from backend.services.cpu_explosao_service import CpuExplosaoService
    svc = CpuExplosaoService(db)
    try:
        filhos = await svc.explodir_sub_composicao(proposta_id, composicao_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    await db.commit()
    return [
        {
            "id": str(f.id),
            "descricao_insumo": f.descricao_insumo,
            "unidade_medida": f.unidade_medida,
            "quantidade_consumo": str(f.quantidade_consumo),
            "nivel": f.nivel,
            "e_composicao": f.e_composicao,
            "pai_composicao_id": str(f.pai_composicao_id),
        }
        for f in filhos
    ]
```

- [ ] **Step 5.3: Verificar que app importa**

```bash
cd app && python -c "from backend.main import app; print('OK')"
```
Esperado: `OK`

- [ ] **Step 5.4: Rodar suite de regressao completa**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -20
```
Esperado: 93+ PASS, 0 FAIL

- [ ] **Step 5.5: Commit final**

```bash
git add app/backend/api/v1/endpoints/cpu_geracao.py
git commit -m "feat(f2-02): POST explodir-sub endpoint with depth guard 422"
```

---

## Self-Review

- [x] Spec coverage: pai_composicao_id self-ref FK, nivel, e_composicao, composicao_explodida, guard nivel > 5 com 422, endpoint explodir-sub, testes de guard e validacao.
- [x] Sem placeholders: todos os steps tem codigo completo.
- [x] Migration encadeia: `down_revision = "018"`.
- [x] Self-ref explicito: `foreign_keys="[PropostaItemComposicao.pai_composicao_id]"` evita ambiguidade SQLAlchemy.
- [x] Tipos consistentes: `PropostaItemComposicao` em tasks 2, 4 e 5.
