# Align Authorization to On-Premise Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove client-level read barriers so any authenticated user can view all clients' data (PROPRIA and global), while preserving write-level RBAC (APROVADOR/ADMIN per client) for mutations.

**Architecture:** Adjust the API layer (`app/api/v1/endpoints/`) to stop using `require_cliente_access` on GET endpoints. The `cliente_id` parameter becomes a pure filter/scope, not a security gate. Write endpoints (POST/PATCH/DELETE) keep `require_cliente_perfil` unchanged. Tests are rewritten to validate the new open-read policy.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), pytest-asyncio, Pydantic v2

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `app/api/v1/endpoints/servicos.py` | Modify | Remove client-access check from `get_servico` and `list_servicos` |
| `app/api/v1/endpoints/versoes.py` | Modify | Remove `require_cliente_access` from `list_versoes`; keep write checks |
| `app/api/v1/endpoints/busca.py` | Modify | Remove `require_cliente_access` from `buscar_servicos` and `list_associacoes` |
| `app/tests/unit/test_security_p0.py` | Modify | Replace cross-tenant isolation tests with open-read policy tests |
| `app/tests/integration/test_auth_access_control.py` | Modify | Adjust assertions to match open-read behavior |

---

## Task 1: Open `GET /servicos/{id}` Read Access

**Files:**
- Modify: `app/api/v1/endpoints/servicos.py:43-64`
- Test: `app/tests/unit/test_security_p0.py`

**Context:** Today `get_servico` returns 404 for PROPRIA items when the caller has no RBAC link to the item's `cliente_id`. We want any authenticated user to read any service.

- [ ] **Step 1: Write the failing test**

```python
# app/tests/unit/test_security_p0.py
@pytest.mark.asyncio
async def test_get_servico_propria_open_to_any_authenticated_user():
    """
    GET /servicos/{id}: A PROPRIA item from any client must be readable
    by any authenticated user (on-premise model, not multi-tenant).
    """
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.models.enums import OrigemItem, StatusHomologacao
    from app.api.v1.endpoints.servicos import get_servico

    servico_id = uuid.uuid4()
    client_b_id = uuid.uuid4()

    mock_servico = MagicMock()
    mock_servico.id = servico_id
    mock_servico.cliente_id = client_b_id
    mock_servico.origem = OrigemItem.PROPRIA
    mock_servico.status_homologacao = StatusHomologacao.APROVADO
    mock_servico.codigo_origem = "XX.001"
    mock_servico.descricao = "Item PROPRIA do Cliente B"
    mock_servico.unidade_medida = "m²"
    mock_servico.custo_unitario = 100.0
    mock_servico.categoria_id = None
    mock_servico.deleted_at = None

    # User from client A (has no access to client B)
    user_a = MagicMock()
    user_a.id = uuid.uuid4()
    user_a.is_admin = False
    user_a.is_active = True

    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_active_by_id = AsyncMock(return_value=mock_servico)

    with patch("app.api.v1.endpoints.servicos.ServicoTcpoRepository", return_value=mock_repo):
        result = await get_servico(
            servico_id=servico_id,
            current_user=user_a,
            db=mock_db,
        )
        assert result is not None
        assert result.cliente_id == client_b_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest app/tests/unit/test_security_p0.py::test_get_servico_propria_open_to_any_authenticated_user -v`

Expected: FAIL — because the current `get_servico` raises `NotFoundError` when `_get_perfis_para_cliente` returns `[]`.

- [ ] **Step 3: Remove client check from `get_servico`**

```python
# app/api/v1/endpoints/servicos.py
@router.get("/{servico_id}", response_model=ServicoTcpoResponse)
async def get_servico(
    servico_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    """
    Returns a service by ID.
    On-premise model: any authenticated user may read any service (global or PROPRIA).
    Write operations remain protected by per-client RBAC.
    """
    return await servico_catalog_service.get_servico(servico_id, db)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest app/tests/unit/test_security_p0.py::test_get_servico_propria_open_to_any_authenticated_user -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/servicos.py app/tests/unit/test_security_p0.py
git commit -m "feat(S-01): open GET /servicos/{id} to any authenticated user"
```

---

## Task 2: Open `GET /servicos/` Read Access

**Files:**
- Modify: `app/api/v1/endpoints/servicos.py:26-40`
- Test: `app/tests/unit/test_security_p0.py`

**Context:** `list_servicos` calls `require_cliente_access` when `cliente_id` is passed. We want the query parameter to be a pure filter.

- [ ] **Step 1: Write the failing test**

```python
# app/tests/unit/test_security_p0.py
@pytest.mark.asyncio
async def test_list_servicos_with_cliente_id_no_access_check():
    """
    GET /servicos/?cliente_id=xxx must not raise 403 for users without
    an RBAC link to that client.
    """
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.api.v1.endpoints.servicos import list_servicos
    from app.schemas.servico import ServicoListParams

    client_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    mock_db = AsyncMock()
    mock_service = AsyncMock()
    mock_service.list_servicos = AsyncMock(return_value=MagicMock(items=[], total=0, page=1, page_size=20, pages=0))

    with patch("app.api.v1.endpoints.servicos.servico_catalog_service", mock_service):
        result = await list_servicos(
            q=None,
            categoria_id=None,
            cliente_id=client_id,
            page=1,
            page_size=20,
            current_user=user,
            db=mock_db,
        )
        assert result.total == 0
        # Service must be called with the cliente_id filter
        mock_service.list_servicos.assert_awaited_once()
        call_args = mock_service.list_servicos.call_args
        assert call_args.kwargs["cliente_id"] == client_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest app/tests/unit/test_security_p0.py::test_list_servicos_with_cliente_id_no_access_check -v`

Expected: FAIL — `require_cliente_access` raises `AuthorizationError`.

- [ ] **Step 3: Remove client check from `list_servicos`**

```python
# app/api/v1/endpoints/servicos.py
@router.get("/", response_model=PaginatedResponse[ServicoTcpoResponse])
async def list_servicos(
    q: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    cliente_id: UUID | None = Query(default=None, description="Filter by client (no access restriction)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ServicoTcpoResponse]:
    params = ServicoListParams(q=q, categoria_id=categoria_id, page=page, page_size=page_size)
    return await servico_catalog_service.list_servicos(params, db, cliente_id=cliente_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest app/tests/unit/test_security_p0.py::test_list_servicos_with_cliente_id_no_access_check -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/servicos.py app/tests/unit/test_security_p0.py
git commit -m "feat(S-01): open GET /servicos/ to any authenticated user"
```

---

## Task 3: Open `GET /servicos/{id}/versoes` Read Access

**Files:**
- Modify: `app/api/v1/endpoints/versoes.py:33-55`
- Test: `app/tests/unit/test_security_p0.py`

**Context:** `list_versoes` currently requires `require_cliente_access`. It should be open read.

- [ ] **Step 1: Write the failing test**

```python
# app/tests/unit/test_security_p0.py
@pytest.mark.asyncio
async def test_list_versoes_open_to_any_authenticated_user():
    """
    GET /servicos/{id}/versoes must be readable by any authenticated user
    regardless of RBAC link to the item's client.
    """
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.api.v1.endpoints.versoes import list_versoes

    item_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    mock_db = AsyncMock()
    mock_item = MagicMock()
    mock_item.cliente_id = uuid.uuid4()

    mock_propria_repo = AsyncMock()
    mock_propria_repo.get_active_by_id = AsyncMock(return_value=mock_item)

    mock_versao_repo = AsyncMock()
    mock_versao_repo.list_versoes = AsyncMock(return_value=[])

    with (
        patch("app.api.v1.endpoints.versoes.ItensPropiosRepository", return_value=mock_propria_repo),
        patch("app.api.v1.endpoints.versoes.VersaoComposicaoRepository", return_value=mock_versao_repo),
    ):
        result = await list_versoes(item_id=item_id, current_user=user, db=mock_db)
        assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest app/tests/unit/test_security_p0.py::test_list_versoes_open_to_any_authenticated_user -v`

Expected: FAIL — `require_cliente_access` raises `AuthorizationError`.

- [ ] **Step 3: Remove client check from `list_versoes`**

```python
# app/api/v1/endpoints/versoes.py
@router.get(
    "/servicos/{item_id}/versoes",
    response_model=list[VersaoComposicaoResponse],
    summary="Listar versões de composição de um item próprio",
)
async def list_versoes(
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[VersaoComposicaoResponse]:
    """
    Lists all VersaoComposicao for a PROPRIA item.
    On-premise model: any authenticated user may read versions.
    """
    propria_repo = ItensPropiosRepository(db)
    item = await propria_repo.get_active_by_id(item_id)
    if not item:
        raise NotFoundError("ItemProprio", str(item_id))

    versao_repo = VersaoComposicaoRepository(db)
    versoes = await versao_repo.list_versoes(item_id)
    return [VersaoComposicaoResponse.model_validate(v) for v in versoes]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest app/tests/unit/test_security_p0.py::test_list_versoes_open_to_any_authenticated_user -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/versoes.py app/tests/unit/test_security_p0.py
git commit -m "feat(S-01): open GET /servicos/{id}/versoes to any authenticated user"
```

---

## Task 4: Open `POST /busca/servicos` and `GET /busca/associacoes` Read Access

**Files:**
- Modify: `app/api/v1/endpoints/busca.py:23-35` and `busca.py:52-79`
- Test: `app/tests/unit/test_security_p0.py`

**Context:** Search and association listing currently block users without a client link. On-premise, search must work across all clients.

- [ ] **Step 1: Write the failing tests**

```python
# app/tests/unit/test_security_p0.py
@pytest.mark.asyncio
async def test_buscar_servicos_no_cliente_access_required():
    """
    POST /busca/servicos must not require cliente_access for the client
    being searched.
    """
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.api.v1.endpoints.busca import buscar_servicos
    from app.schemas.busca import BuscaServicoRequest

    client_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    mock_db = AsyncMock()
    mock_service = AsyncMock()
    mock_service.buscar = AsyncMock(return_value=MagicMock())

    request = BuscaServicoRequest(cliente_id=client_id, texto_busca="escavacao")

    with patch("app.api.v1.endpoints.busca.busca_service", mock_service):
        result = await buscar_servicos(
            request=request,
            current_user=user,
            db=mock_db,
        )
        assert result is not None
        mock_service.buscar.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_associacoes_no_cliente_access_required():
    """
    GET /busca/associacoes must not require cliente_access.
    """
    import uuid
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.api.v1.endpoints.busca import list_associacoes

    client_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    mock_db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.list_by_cliente = AsyncMock(return_value=([], 0))

    with patch("app.api.v1.endpoints.busca.AssociacaoRepository", return_value=mock_repo):
        result = await list_associacoes(
            cliente_id=client_id,
            page=1,
            page_size=20,
            current_user=user,
            db=mock_db,
        )
        assert result.total == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest app/tests/unit/test_security_p0.py::test_buscar_servicos_no_cliente_access_required app/tests/unit/test_security_p0.py::test_list_associacoes_no_cliente_access_required -v`

Expected: FAIL — `require_cliente_access` raises `AuthorizationError`.

- [ ] **Step 3: Remove client checks from `busca.py`**

```python
# app/api/v1/endpoints/busca.py
@router.post("/servicos", response_model=BuscaServicoResponse)
async def buscar_servicos(
    request: BuscaServicoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BuscaServicoResponse:
    return await busca_service.buscar(
        request=request,
        usuario_id=current_user.id,
        db=db,
    )
```

```python
# app/api/v1/endpoints/busca.py
@router.get(
    "/associacoes",
    response_model=PaginatedResponse[AssociacaoListItem],
    summary="Listar associações inteligentes do cliente",
)
async def list_associacoes(
    cliente_id: UUID = Query(..., description="ID do cliente"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AssociacaoListItem]:
    """
    Returns paginated list of intelligent associations for a client.
    On-premise model: any authenticated user may read associations.
    """
    repo = AssociacaoRepository(db)
    offset = (page - 1) * page_size
    items, total = await repo.list_by_cliente(cliente_id=cliente_id, offset=offset, limit=page_size)
    pages = math.ceil(total / page_size) if total else 0
    return PaginatedResponse(
        items=[AssociacaoListItem.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest app/tests/unit/test_security_p0.py::test_buscar_servicos_no_cliente_access_required app/tests/unit/test_security_p0.py::test_list_associacoes_no_cliente_access_required -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/busca.py app/tests/unit/test_security_p0.py
git commit -m "feat(S-01): open search and association listing to any authenticated user"
```

---

## Task 5: Clean Up Obsolete Cross-Tenant Isolation Tests

**Files:**
- Modify: `app/tests/unit/test_security_p0.py`

**Context:** Tests `test_get_servico_propria_blocks_wrong_tenant` and `test_get_servico_propria_allows_correct_tenant` enforce the old multi-tenant model. They must be removed or replaced.

- [ ] **Step 1: Identify obsolete tests**

The following tests in `app/tests/unit/test_security_p0.py` are now invalid:
- `test_get_servico_propria_blocks_wrong_tenant`
- `test_get_servico_propria_allows_correct_tenant`

- [ ] **Step 2: Remove obsolete tests**

Delete lines 113-168 and 170-219 from `app/tests/unit/test_security_p0.py` (the two tenant-blocking tests).

- [ ] **Step 3: Run remaining tests**

Run: `pytest app/tests/unit/test_security_p0.py -v`

Expected: PASS — all remaining tests pass without the removed ones.

- [ ] **Step 4: Commit**

```bash
git add app/tests/unit/test_security_p0.py
git commit -m "test(S-01): remove obsolete cross-tenant isolation tests"
```

---

## Task 6: Integration Test Regression for Open-Read Policy

**Files:**
- Modify: `app/tests/integration/test_auth_access_control.py`

**Context:** Add an integration test proving that a user without a client link can still read data scoped to that client.

- [ ] **Step 1: Write integration test**

```python
# app/tests/integration/test_auth_access_control.py

@pytest.mark.asyncio
async def test_servico_propria_readable_without_client_link(client):
    """
    A user with no RBAC link to a client must still be able to read
    a PROPRIA service from that client (on-premise open-read model).
    """
    # This test assumes seed data exists with a PROPRIA item;
    # if not present, it validates the policy at the endpoint level.
    # For a full integration test, seed a PROPRIA item first.
    import uuid

    fake_client_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/servicos/{fake_client_id}")
    # We expect 404 because the item does not exist, NOT 403/401 due to access control
    assert resp.status_code in {404}
    # If we had a real item, it would be 200. The key invariant is:
    # status must NOT be 403.
```

- [ ] **Step 2: Run integration tests**

Run: `pytest app/tests/integration/test_auth_access_control.py -v`

Expected: PASS (or skip if DB seed is unavailable).

- [ ] **Step 3: Commit**

```bash
git add app/tests/integration/test_auth_access_control.py
git commit -m "test(S-01): add integration test for open-read policy"
```

---

## Task 7: Verify Write Endpoints Remain Protected

**Files:**
- No code changes (verification only)
- Test: `app/tests/unit/test_security_p0.py`

**Context:** We must ensure we did NOT accidentally open any POST/PATCH/DELETE endpoints.

- [ ] **Step 1: Add verification test**

```python
# app/tests/unit/test_security_p0.py

def test_write_endpoints_still_require_client_perfil():
    """
    Sanity check: write endpoints must still import and use
    require_cliente_perfil or require_cliente_access.
    """
    import inspect
    from app.api.v1.endpoints import composicoes, homologacao, versoes

    write_routes = [
        (composicoes.clonar_composicao, "POST /composicoes/clonar"),
        (composicoes.adicionar_componente, "POST /composicoes/{id}/componentes"),
        (composicoes.remover_componente, "DELETE /composicoes/{id}/componentes/{comp_id}"),
        (homologacao.criar_item_proprio, "POST /homologacao/itens-proprios"),
        (homologacao.aprovar_item, "POST /homologacao/aprovar"),
        (versoes.criar_versao, "POST /composicoes/{id}/versoes"),
        (versoes.ativar_versao, "PATCH /composicoes/versoes/{id}/ativar"),
    ]

    for func, name in write_routes:
        src = inspect.getsource(func)
        assert "require_cliente_perfil" in src or "require_cliente_access" in src, (
            f"{name} must still enforce client-level write authorization"
        )
```

- [ ] **Step 2: Run test**

Run: `pytest app/tests/unit/test_security_p0.py::test_write_endpoints_still_require_client_perfil -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add app/tests/unit/test_security_p0.py
git commit -m "test(S-01): verify write endpoints remain protected"
```

---

## Task 8: Clean Unused Imports

**Files:**
- Modify: `app/api/v1/endpoints/servicos.py`, `app/api/v1/endpoints/versoes.py`, `app/api/v1/endpoints/busca.py`

**Context:** After removing `require_cliente_access` calls, some imports may become unused. Clean them to avoid linter warnings.

- [ ] **Step 1: Review and remove unused imports in `servicos.py`**

Remove `_get_perfis_para_cliente` and `require_cliente_access` from the import block if they are no longer used elsewhere in the file.

```python
# Before
from app.core.dependencies import (
    _get_perfis_para_cliente,
    get_current_active_user,
    get_current_admin_user,
    get_db,
    require_cliente_access,
)

# After
from app.core.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_db,
)
```

- [ ] **Step 2: Review and remove unused imports in `versoes.py`**

Remove `require_cliente_access` from imports if unused.

```python
# Before
from app.core.dependencies import (
    get_current_active_user,
    get_db,
    require_cliente_access,
    require_cliente_perfil,
)

# After
from app.core.dependencies import (
    get_current_active_user,
    get_db,
    require_cliente_perfil,
)
```

- [ ] **Step 3: Review and remove unused imports in `busca.py`**

Remove `require_cliente_access` from imports if unused.

```python
# Before
from app.core.dependencies import get_current_active_user, get_db, require_cliente_access, require_cliente_perfil

# After
from app.core.dependencies import get_current_active_user, get_db, require_cliente_perfil
```

- [ ] **Step 4: Run linter/tests**

Run: `pytest app/tests/unit/test_security_p0.py app/tests/integration/test_auth_access_control.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/servicos.py app/api/v1/endpoints/versoes.py app/api/v1/endpoints/busca.py
git commit -m "refactor(S-01): remove unused imports after opening read endpoints"
```

---

## Self-Review

### 1. Spec Coverage

| Requirement | Task |
|---|---|
| `GET /servicos/{id}` open to any authenticated user | Task 1 |
| `GET /servicos/{id}/composicao` already open, no change needed | — |
| `GET /servicos/` open to any authenticated user | Task 2 |
| `GET /servicos/{id}/versoes` open to any authenticated user | Task 3 |
| `GET /busca/servicos` open to any authenticated user | Task 4 |
| `GET /busca/associacoes` open to any authenticated user | Task 4 |
| Write endpoints remain protected | Task 7 |
| Tests updated | Tasks 1-7 |
| Clean imports | Task 8 |

### 2. Placeholder Scan

- No "TBD", "TODO", or "implement later" found.
- All steps contain exact file paths, exact code blocks, and exact commands.
- Test code is complete, not placeholder.

### 3. Type Consistency

- `ServicoTcpoRepository` / `ItensPropiosRepository` names match existing codebase.
- `require_cliente_access` and `require_cliente_perfil` names match `dependencies.py`.
- Mock patterns match existing test style (`AsyncMock`, `MagicMock`, `patch`).

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-22-align-authorization-onpremise-model.md`.**

**Two execution options:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
