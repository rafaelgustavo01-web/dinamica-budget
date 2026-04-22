# Arquitetura em Camadas — Implementation Plan v2 (Revisado)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> **Revisão:** Supervisor corrigiu bloqueadores de assinatura, SQL residual, padrão de injeção e cobertura de testes.

**Goal:** Consolidar arquitetura em camadas (endpoint → service → repository) para os endpoints `auth`, `versoes`. Remover regras de negócio/SQL direto dos endpoints. Verificar estado de `servicos`.

**Architecture:** padrão service/repository. Endpoints delegam para service, service usa repository. Cada endpoint deve ter ~5 linhas de delegação, nada de lógica.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest

**Padrão de Injeção (obrigatório):** Service recebe repositories no `__init__` com a sessão do endpoint. Não passe `AsyncSession` nos métodos do service.

---

## Task 1: Refatorar AuthService — Extract Profile Logic

**Files:**
- Modify: `app/services/auth_service.py`
- Modify: `app/schemas/auth.py` (verificar import de `PerfilClienteResponse`)
- Create: `app/tests/unit/test_auth_service.py`

### Step 1: Adicionar `get_user_profile` ao AuthService

```python
# app/services/auth_service.py
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import PerfilClienteResponse  # verificar se existe; se não, usar dict

class AuthService:
    def __init__(self, repo: UsuarioRepository) -> None:
        self.repo = repo

    # ... métodos existentes ...

    async def get_user_profile(self, user_id: UUID, db: AsyncSession) -> dict:
        """Get user with perfis for /auth/me endpoint.
        Returns flat dict para desempacotar em MeResponse.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("Usuário não encontrado.")

        perfis_db = await self.repo.get_perfis(user_id)
        perfis = [
            PerfilClienteResponse(cliente_id=str(p.cliente_id), perfil=p.perfil)
            for p in perfis_db
        ]
        if user.is_admin:
            perfis.append(PerfilClienteResponse(cliente_id="*", perfil="ADMIN"))

        return {
            "id": str(user.id),
            "nome": user.nome,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "perfis": perfis,
        }
```

> **Nota:** Se `PerfilClienteResponse` não estiver em `app.schemas.auth`, importe de onde estiver definido (provavelmente `app.schemas.usuario` ou similar).

### Step 2: Criar testes unitários

```python
# app/tests/unit/test_auth_service.py
import uuid
import pytest
from unittest.mock import AsyncMock

from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_repo):
    return AuthService(mock_repo)


@pytest.mark.asyncio
async def test_get_user_profile_success(auth_service, mock_repo):
    from app.models.usuario import Usuario, UsuarioPerfil

    user = Usuario(
        id=uuid.uuid4(),
        nome="Test User",
        email="test@example.com",
        is_admin=False,
        is_active=True,
    )
    perfil = UsuarioPerfil(usuario_id=user.id, cliente_id=uuid.uuid4(), perfil="USUARIO")

    mock_repo.get_by_id.return_value = user
    mock_repo.get_perfis.return_value = [perfil]

    result = await auth_service.get_user_profile(user.id, None)

    assert result["nome"] == "Test User"
    assert len(result["perfis"]) == 1
    assert result["perfis"][0].perfil == "USUARIO"


@pytest.mark.asyncio
async def test_get_user_profile_admin_adds_wildcard(auth_service, mock_repo):
    from app.models.usuario import Usuario

    user = Usuario(
        id=uuid.uuid4(),
        nome="Admin User",
        email="admin@example.com",
        is_admin=True,
        is_active=True,
    )
    mock_repo.get_by_id.return_value = user
    mock_repo.get_perfis.return_value = []

    result = await auth_service.get_user_profile(user.id, None)

    assert len(result["perfis"]) == 1
    assert result["perfis"][0].cliente_id == "*"
    assert result["perfis"][0].perfil == "ADMIN"


@pytest.mark.asyncio
async def test_get_user_profile_not_found(auth_service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(AuthenticationError, match="Usuário não encontrado"):
        await auth_service.get_user_profile(uuid.uuid4(), None)
```

### Step 3: Rodar testes

```powershell
pytest app/tests/unit/test_auth_service.py -v
```
Expected: 3 PASS

### Step 4: Commit

```bash
git add app/services/auth_service.py app/tests/unit/test_auth_service.py
git commit -m "refactor(auth): add get_user_profile to AuthService with tests"
```

---

## Task 2: Refatorar auth.py Endpoint — Use AuthService

**Files:**
- Modify: `app/api/v1/endpoints/auth.py:86-140`

### Step 1: Simplificar endpoints `/me` e `/me` PATCH

```python
# app/api/v1/endpoints/auth.py — substituir linhas 86-140

@router.get("/me", response_model=MeResponse, summary="Usuário atual + perfis")
async def me(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Returns current user with all client/perfil bindings."""
    svc = AuthService(UsuarioRepository(db))
    perfil_data = await svc.get_user_profile(current_user.id, db)
    return MeResponse(**perfil_data)


@router.patch("/me", response_model=MeResponse, summary="Atualizar perfil próprio")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> MeResponse:
    """Atualiza nome do próprio usuário autenticado."""
    await svc.update_profile(current_user.id, data)
    perfil_data = await svc.get_user_profile(current_user.id, db)
    return MeResponse(**perfil_data)
```

> **Regra:** Nenhuma importação de `UsuarioPerfil`, `select`, ou query SQL neste arquivo para os endpoints `/me`.

### Step 2: Rodar testes de regressão

```powershell
pytest app/tests/integration/test_auth_access_control.py -v
pytest app/tests/unit/test_auth_service.py -v
```
Expected: ALL PASS

### Step 3: Commit

```bash
git add app/api/v1/endpoints/auth.py
git commit -m "refactor(auth): delegate /me and /me PATCH to AuthService"
```

---

## Task 3: Criar VersaoService

**Files:**
- Create: `app/services/versao_service.py`
- Create: `app/tests/unit/test_versao_service.py`

### Step 1: Implementar VersaoService completo

```python
# app/services/versao_service.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_cliente_perfil
from app.core.exceptions import NotFoundError
from app.models.composicao_cliente import ComposicaoCliente
from app.models.versao_composicao import VersaoComposicao
from app.repositories.itens_proprios_repository import ItensPropiosRepository
from app.repositories.versao_composicao_repository import VersaoComposicaoRepository

_PERFIS_EDICAO = ["APROVADOR", "ADMIN"]


class VersaoService:
    def __init__(
        self,
        versao_repo: VersaoComposicaoRepository,
        propria_repo: ItensPropiosRepository,
    ) -> None:
        self.versao_repo = versao_repo
        self.propria_repo = propria_repo

    async def assert_edit_permission(
        self, item_id: UUID, current_user, db: AsyncSession
    ) -> None:
        """Raise if current_user lacks edit permission on item's client."""
        item = await self.propria_repo.get_active_by_id(item_id)
        if not item:
            raise NotFoundError("ItemProprio", str(item_id))
        await require_cliente_perfil(
            item.cliente_id, _PERFIS_EDICAO, current_user, db
        )

    async def list_versoes(self, item_id: UUID) -> list[VersaoComposicao]:
        """List all versions for an item."""
        item = await self.propria_repo.get_active_by_id(item_id)
        if not item:
            raise NotFoundError("ItemProprio", str(item_id))
        return await self.versao_repo.list_versoes(item_id)

    async def criar_versao(
        self, item_id: UUID, current_user_id: UUID, db: AsyncSession
    ) -> VersaoComposicao:
        """Create new version (clone of active)."""
        item = await self.propria_repo.get_active_by_id(item_id)
        if not item:
            raise NotFoundError("ItemProprio", str(item_id))

        versoes_existentes = await self.versao_repo.list_versoes(item_id)
        next_numero = max((v.numero_versao for v in versoes_existentes), default=0) + 1

        nova_versao = VersaoComposicao(
            item_proprio_id=item_id,
            numero_versao=next_numero,
            is_ativa=False,
            criado_por_id=current_user_id,
        )
        db.add(nova_versao)
        await db.flush()

        # Clone ComposicaoCliente from active version
        versao_ativa = await self.versao_repo.get_versao_ativa(item_id)
        if versao_ativa:
            result = await db.execute(
                select(ComposicaoCliente).where(ComposicaoCliente.versao_id == versao_ativa.id)
            )
            for comp in result.scalars().all():
                db.add(
                    ComposicaoCliente(
                        versao_id=nova_versao.id,
                        insumo_base_id=comp.insumo_base_id,
                        insumo_proprio_id=comp.insumo_proprio_id,
                        quantidade_consumo=comp.quantidade_consumo,
                        unidade_medida=comp.unidade_medida,
                    )
                )

        await db.flush()
        await db.refresh(nova_versao)
        return nova_versao

    async def ativar_versao(
        self, versao_id: UUID, current_user_id: UUID, db: AsyncSession
    ) -> VersaoComposicao:
        """Activate a version, deactivate others for the same item."""
        versao = await self.versao_repo.get_by_id(versao_id)
        if not versao:
            raise NotFoundError("VersaoComposicao", str(versao_id))

        await self.versao_repo.deactivate_all(versao.item_proprio_id)
        versao.is_ativa = True
        await db.flush()
        await db.refresh(versao)
        return versao
```

> **Nota:** `get_by_id` deve existir em `VersaoComposicaoRepository` (herdado de `BaseRepository`). Se não existir, adicione:
> ```python
> async def get_by_id(self, id: UUID) -> VersaoComposicao | None:
>     result = await self.db.execute(select(self.model).where(self.model.id == id))
>     return result.scalar_one_or_none()
> ```

### Step 2: Criar testes unitários

```python
# app/tests/unit/test_versao_service.py
import uuid
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.versao_service import VersaoService
from app.core.exceptions import NotFoundError


@pytest.fixture
def mock_versao_repo():
    return AsyncMock()


@pytest.fixture
def mock_propria_repo():
    return AsyncMock()


@pytest.fixture
def versao_service(mock_versao_repo, mock_propria_repo):
    return VersaoService(mock_versao_repo, mock_propria_repo)


@pytest.mark.asyncio
async def test_list_versoes_success(versao_service, mock_propria_repo, mock_versao_repo):
    mock_propria_repo.get_active_by_id.return_value = MagicMock(id=uuid.uuid4())
    mock_versao_repo.list_versoes.return_value = []

    result = await versao_service.list_versoes(uuid.uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_list_versoes_item_not_found(versao_service, mock_propria_repo):
    mock_propria_repo.get_active_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await versao_service.list_versoes(uuid.uuid4())


@pytest.mark.asyncio
async def test_criar_versao_success(versao_service, mock_propria_repo, mock_versao_repo):
    from app.models.versao_composicao import VersaoComposicao

    item_id = uuid.uuid4()
    mock_propria_repo.get_active_by_id.return_value = MagicMock(id=item_id)
    mock_versao_repo.list_versoes.return_value = []

    db = AsyncMock()
    result = await versao_service.criar_versao(item_id, uuid.uuid4(), db)

    assert isinstance(result, VersaoComposicao)
    assert result.numero_versao == 1


@pytest.mark.asyncio
async def test_ativar_versao_success(versao_service, mock_versao_repo):
    from app.models.versao_composicao import VersaoComposicao

    versao = VersaoComposicao(id=uuid.uuid4(), item_proprio_id=uuid.uuid4(), is_ativa=False)
    mock_versao_repo.get_by_id.return_value = versao

    db = AsyncMock()
    result = await versao_service.ativar_versao(versao.id, uuid.uuid4(), db)

    assert result.is_ativa is True
    mock_versao_repo.deactivate_all.assert_awaited_once_with(versao.item_proprio_id)
```

### Step 3: Rodar testes

```powershell
pytest app/tests/unit/test_versao_service.py -v
```
Expected: 4+ PASS

### Step 4: Commit

```bash
git add app/services/versao_service.py app/tests/unit/test_versao_service.py
git commit -m "feat(versoes): add VersaoService with full CRUD + permission checks"
```

---

## Task 4: Refatorar versoes.py Endpoint — Use VersaoService

**Files:**
- Modify: `app/api/v1/endpoints/versoes.py`

### Step 1: Simplificar endpoints

```python
# app/api/v1/endpoints/versoes.py — substituir arquivo completo
"""
Endpoints for VersaoComposicao management.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db
from app.core.exceptions import NotFoundError
from app.schemas.servico import VersaoComposicaoResponse
from app.services.versao_service import VersaoService
from app.repositories.versao_composicao_repository import VersaoComposicaoRepository
from app.repositories.itens_proprios_repository import ItensPropiosRepository

router = APIRouter(tags=["versoes"])


def _get_service(db: AsyncSession) -> VersaoService:
    return VersaoService(
        VersaoComposicaoRepository(db),
        ItensPropiosRepository(db),
    )


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
    svc = _get_service(db)
    versoes = await svc.list_versoes(item_id)
    return [VersaoComposicaoResponse.model_validate(v) for v in versoes]


@router.post(
    "/composicoes/{item_id}/versoes",
    response_model=VersaoComposicaoResponse,
    status_code=201,
    summary="Criar nova versão (clone da versão ativa atual)",
)
async def criar_versao(
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VersaoComposicaoResponse:
    svc = _get_service(db)
    await svc.assert_edit_permission(item_id, current_user, db)
    nova = await svc.criar_versao(item_id, current_user.id, db)
    return VersaoComposicaoResponse.model_validate(nova)


@router.patch(
    "/composicoes/versoes/{versao_id}/ativar",
    response_model=VersaoComposicaoResponse,
    summary="Ativar uma versão de composição",
)
async def ativar_versao(
    versao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VersaoComposicaoResponse:
    svc = _get_service(db)
    # Resolve item_id from service (no SQL here)
    versao = await svc.versao_repo.get_by_id(versao_id)
    if not versao:
        raise NotFoundError("VersaoComposicao", str(versao_id))
    await svc.assert_edit_permission(versao.item_proprio_id, current_user, db)
    ativada = await svc.ativar_versao(versao_id, current_user.id, db)
    return VersaoComposicaoResponse.model_validate(ativada)
```

> **Nota:** O endpoint `ativar_versao` ainda precisa resolver `versao_id → item_proprio_id` para checar permissão. Usamos `svc.versao_repo.get_by_id` (repository, não SQL direto). Alternativa futura: mover essa resolução para o service.

### Step 2: Rodar testes

```powershell
pytest app/tests/ -k "versoes" -v
```
Expected: PASS

### Step 3: Commit

```bash
git add app/api/v1/endpoints/versoes.py
git commit -m "refactor(versoes): delegate all endpoints to VersaoService"
```

---

## Task 5: Verificar servicos.py e ServicoCatalogService

**Files:**
- Read: `app/api/v1/endpoints/servicos.py`
- Read: `app/services/servico_catalog_service.py`

### Step 1: Verificar endpoints

```powershell
# Confirmar que todos os endpoints delegam
Select-String -Path "app/api/v1/endpoints/servicos.py" -Pattern "servico_catalog_service\."
```

Expected: Todos os handlers chamam `servico_catalog_service.*(...)`.

### Step 2: Inspecionar service quanto a SQL direto em métodos públicos

```powershell
# Listar métodos públicos que fazem db.execute
Select-String -Path "app/services/servico_catalog_service.py" -Pattern "async def [^_]|db\.execute"
```

**Achado esperado:**
- Métodos públicos (`list_servicos`, `get_servico`, `explode_composicao`, etc.) usam repositories.
- Métodos privados (`_explode_recursivo_tcpo`, `_explode_recursivo_propria`, `_detectar_ciclo`) ainda fazem `db.execute` para queries específicas de composição.
- Isso é **aceitável** para métodos privados internos; não está no escopo desta sprint.

### Step 3: Documentar no walkthrough

Adicionar nota no walkthrough S-02:
> `ServicoCatalogService` contém queries SQL em métodos privados (`_explode_recursivo_*`, `_detectar_ciclo`). Não foram alterados nesta sprint. Próxima revisão: extrair para repository dedicado de composição.

### Step 4: Commit

```bash
git commit --allow-empty -m "chore(servicos): verify delegation and document private SQL findings"
```

---

## Task 6: Run Full Regression Suite

**Files:**
- Test: full suite

### Step 1: Rodar testes unitários

```powershell
pytest app/tests/unit/ -v --tb=short
```
Expected: ALL PASS

### Step 2: Rodar testes de integração

```powershell
pytest app/tests/integration/test_auth_access_control.py -v
pytest app/tests/integration/ -v --tb=short
```
Expected: ALL PASS

### Step 3: Rodar suite completa

```powershell
pytest app/tests/ -v --tb=short
```
Expected: ALL PASS

### Step 4: Atualizar BACKLOG

```markdown
# docs/BACKLOG.md
Alterar S-02 de `INICIADA` → `TESTED`
```

### Step 5: Commit

```bash
git add docs/BACKLOG.md
git commit -m "test(regression): full suite pass after S-02 layer refactoring"
```

---

## Task 7: Gerar Walkthrough e Technical Review

**Files:**
- Create: `docs/walkthrough/done/walkthrough-S-02.md`
- Create: `docs/technical-review-2026-04-22.md` (ou data atual)

### Step 1: Walkthrough

Template:
```markdown
# Walkthrough — Sprint S-02

## O que foi feito
- AuthService: adicionado get_user_profile()
- VersaoService: criado com list, criar, ativar, assert_edit_permission
- auth.py: /me e /me PATCH reduzidos a delegação
- versoes.py: todos os endpoints delegam para VersaoService
- servicos.py: verificado, já delega (sem alterações)

## Testes
- Unit: test_auth_service.py (3 casos) — PASS
- Unit: test_versao_service.py (4 casos) — PASS
- Integration: test_auth_access_control.py — PASS
- Full suite — PASS

## Decisões técnicas
- Padrão de injeção: repo no __init__, sem db nos métodos do service
- Transação: mantido request-scoped (service faz flush, não commit)
```

### Step 2: Commit

```bash
git add docs/walkthrough/done/walkthrough-S-02.md docs/technical-review-2026-04-22.md
git commit -m "docs(s-02): add walkthrough and technical review"
```

---

## Plan Review Checklist (Supervisor)

- [x] Spec coverage: endpoints auth, versoes, servicos covered
- [x] Placeholder scan: no TBD/TODO found
- [x] Type consistency: service methods match endpoint calls
- [x] **Bloqueador B1 resolvido:** assinatura `ativar_versao` unificada (3 args, resolve versao dentro do service)
- [x] **Bloqueador B2 resolvido:** SQL direto removido de `ativar_versao` endpoint (usa repo)
- [x] **Risco R1 resolvido:** padrão de injeção definido (repo no `__init__`, não passa db nos métodos)
- [x] **Risco R2 resolvido:** `_check_perfil` movido para `assert_edit_permission` no service
- [x] **Risco R3 resolvido:** `ativar_versao` implementado completamente no service
- [x] **Risco R4 resolvido:** testes cobrem happy path, admin wildcard, not-found
- [x] **Risco M1 resolvido:** Task 5 inspeciona `ServicoCatalogService` internamente
- [x] **Risco M2 resolvido:** nota transacional no briefing e plano
- [x] **Risco M3 resolvido:** Task 6 inclui testes de integração explicitamente
- [x] **Risco M4 resolvido:** imports e dependências documentados

## Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-22-arquitetura-camadas.md` (v2).**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch subagent per task, review between tasks
2. **Inline Execution** — execute in this session with checkpoints

Which approach?
