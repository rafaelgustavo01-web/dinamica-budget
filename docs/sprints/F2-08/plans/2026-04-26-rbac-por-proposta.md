# F2-08: RBAC por Proposta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Desacoplar autorização de Propostas do `cliente_id`. Hoje todo endpoint de proposta chama `require_cliente_access(proposta.cliente_id, ...)` — usuários sem vínculo ao cliente da proposta são bloqueados. A regra correta é: qualquer usuário autenticado pode ver/criar propostas para qualquer cliente, e a autorização operacional (editar, aprovar, deletar) é dada por papel **na proposta**, armazenado em `proposta_acl`.

**Architecture:** (1) Nova tabela `operacional.proposta_acl(id, proposta_id, usuario_id, papel, created_at, created_by)` com `UNIQUE(proposta_id, usuario_id, papel)`. (2) Enum `proposta_papel_enum` com 3 valores: `OWNER`, `EDITOR`, `APROVADOR`. **VIEWER é o default implícito** de qualquer usuário autenticado e NÃO mora na tabela. (3) Migration 021 cria tabela + backfill (criador de cada proposta vira `OWNER`). (4) Nova dependency `require_proposta_role(proposta_id, papel_minimo)` em `core/dependencies.py` substitui `require_cliente_access` em 5 routers de proposta. (5) `users.is_admin = true` bypassa qualquer checagem. (6) `GET /propostas` deixa de exigir `cliente_id` e retorna todas as propostas com campo computado `meu_papel`. (7) Endpoints CRUD de ACL (somente OWNER pode gerenciar). (8) Frontend: modal "Compartilhar proposta" + esconder ações conforme papel.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, PostgreSQL enum types, React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Pré-requisito de leitura (obrigatório antes de codar)

Esta sprint é refactor de segurança crítica. **Leia na ordem antes de começar:**

1. `docs/shared/superpowers/plans/roadmap/ROADMAP.md` — Milestone 6, Fase 6.6 (escopo desta sprint)
2. `docs/plano gpt.md` — Seção 10 (origem da reformulação RBAC); ler também a CORREÇÃO em ROADMAP.md (PO descartou ACL como gating de leitura)
3. `app/backend/core/dependencies.py` — `require_cliente_access`, `require_cliente_perfil`, `get_current_admin_user` (padrão a seguir)
4. `app/backend/api/v1/endpoints/propostas.py` — onde `require_cliente_access` é chamado hoje
5. `app/backend/api/v1/endpoints/pq_importacao.py` — chamadas a `require_cliente_access`
6. `app/backend/api/v1/endpoints/cpu_geracao.py` — chamadas a `require_cliente_access`
7. `app/backend/api/v1/endpoints/proposta_export.py` — chamadas a `require_cliente_access`
8. `app/backend/api/v1/endpoints/proposta_recursos.py` — chamadas a `require_cliente_access` (vindo de F2-07)
9. `app/backend/models/usuario.py` — campo `is_admin`
10. `app/backend/models/proposta.py` — `Proposta.criado_por_id`, `Proposta.cliente_id`
11. `app/alembic/versions/020_add_proposta_resumo_recursos_table.py` — padrão de migration mais recente
12. `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` — onde botões de edit/delete vivem
13. `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx` — listagem que hoje filtra por cliente

**Antes de codar, mentalmente responda:**
- Quem pode chamar `POST /propostas/{id}/acl` para conceder OWNER a outro usuário? **Resposta:** somente OWNER atual (ou ADMIN global).
- O que acontece quando `is_admin = true`? **Resposta:** bypass total — não checa ACL.
- VIEWER mora em proposta_acl? **Resposta:** NÃO — é o default implícito de qualquer usuário autenticado.
- ACL é por `proposta_id` ou por `proposta_root_id`? **Resposta:** por `proposta_id` nesta sprint. Em F2-09 (versionamento) será migrado para `proposta_root_id`.

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/backend/models/enums.py` | Modificar | Adicionar enum `PropostaPapel` (OWNER, EDITOR, APROVADOR) |
| `app/backend/models/proposta.py` | Modificar | Adicionar `PropostaAcl` model + relationship em `Proposta` |
| `app/alembic/versions/021_proposta_acl.py` | Criar | Migration: enum `proposta_papel_enum` + tabela + backfill OWNER |
| `app/backend/repositories/proposta_acl_repository.py` | Criar | CRUD: `list_by_proposta`, `get_papeis_for_user`, `add_papel`, `remove_papel` |
| `app/backend/services/proposta_acl_service.py` | Criar | Regras de negócio: criar OWNER no create_proposta, validar elevações, checar última-OWNER |
| `app/backend/core/dependencies.py` | Modificar | Adicionar `require_proposta_role(proposta_id, papel_minimo)` + helper `get_meu_papel(proposta_id)` |
| `app/backend/services/proposta_service.py` | Modificar | `criar_proposta`: após persistir, chama `acl_svc.conceder(proposta.id, criador_id, OWNER)` na mesma transação |
| `app/backend/api/v1/endpoints/propostas.py` | Modificar | Substituir `require_cliente_access` por `require_proposta_role`; remover `cliente_id` obrigatório do GET; adicionar `meu_papel` na resposta |
| `app/backend/api/v1/endpoints/pq_importacao.py` | Modificar | Substituir `require_cliente_access` |
| `app/backend/api/v1/endpoints/cpu_geracao.py` | Modificar | Substituir `require_cliente_access` |
| `app/backend/api/v1/endpoints/proposta_export.py` | Modificar | Substituir `require_cliente_access` |
| `app/backend/api/v1/endpoints/proposta_recursos.py` | Modificar | Substituir `require_cliente_access` |
| `app/backend/api/v1/endpoints/proposta_acl.py` | Criar | `GET /propostas/{id}/acl`, `POST /propostas/{id}/acl`, `DELETE /propostas/{id}/acl/{usuario_id}/{papel}` |
| `app/backend/api/v1/router.py` | Modificar | Registrar router proposta_acl |
| `app/backend/schemas/proposta.py` | Modificar | Adicionar `PropostaResponse.meu_papel: PropostaPapel \| None` + `PropostaAclResponse`, `PropostaAclCreate` |
| `app/backend/tests/unit/test_proposta_acl_dependency.py` | Criar | Testes da `require_proposta_role` (cenários por papel + admin bypass) |
| `app/backend/tests/unit/test_proposta_acl_endpoints.py` | Criar | CRUD da ACL + 403 quando não-OWNER tenta gerenciar |
| `app/backend/tests/unit/test_propostas_rbac_refactor.py` | Criar | Regressão dos endpoints de proposta com novo RBAC |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | Tipo `PropostaPapel`; campo `meu_papel` em `PropostaResponse`; `listAcl`, `addAcl`, `removeAcl` |
| `app/frontend/src/features/proposals/components/ProposalShareDialog.tsx` | Criar | Modal: lista usuários com papel + autocomplete para adicionar |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificar | Botão "Compartilhar" (só OWNER); esconder Excluir se !OWNER; esconder Editar/Importar se VIEWER |
| `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx` | Modificar | Remover filtro obrigatório por cliente; coluna "Meu papel" |

---

## Task 1: Backend — enum + model + migration

**Files:**
- Modify: `app/backend/models/enums.py`
- Modify: `app/backend/models/proposta.py`
- Create: `app/alembic/versions/021_proposta_acl.py`

### Step 1: Enum `PropostaPapel`

```python
# em models/enums.py
class PropostaPapel(str, Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    APROVADOR = "APROVADOR"
```

`VIEWER` **NÃO** entra no enum — é default implícito.

### Step 2: Model `PropostaAcl`

```python
# em models/proposta.py
class PropostaAcl(Base, TimestampMixin):
    __tablename__ = "proposta_acl"
    __table_args__ = (
        UniqueConstraint("proposta_id", "usuario_id", "papel", name="uq_proposta_acl"),
        {"schema": "operacional"},
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    papel: Mapped[PropostaPapel] = mapped_column(
        SAEnum(PropostaPapel, name="proposta_papel_enum", create_type=False), nullable=False,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id"),
        nullable=False,
    )
```

Adicionar `relationship("PropostaAcl", back_populates="proposta", cascade="all, delete-orphan")` no `Proposta`.

### Step 3: Migration 021

Seguir padrão de `020_add_proposta_resumo_recursos_table.py`. **Importante:**
- `revision = "021"`, `down_revision = "020"`
- Criar `proposta_papel_enum` no Postgres ANTES da tabela: `op.execute("CREATE TYPE proposta_papel_enum AS ENUM ('OWNER', 'EDITOR', 'APROVADOR')")`
- Criar tabela `operacional.proposta_acl`
- **Backfill OWNER**: `op.execute("INSERT INTO operacional.proposta_acl (id, proposta_id, usuario_id, papel, created_by, created_at, updated_at) SELECT gen_random_uuid(), id, criado_por_id, 'OWNER'::proposta_papel_enum, criado_por_id, NOW(), NOW() FROM operacional.propostas WHERE criado_por_id IS NOT NULL")`
- `downgrade`: drop tabela + drop enum

- [ ] **Step 1**: enum + model
- [ ] **Step 2**: migration 021 (revisão correta, schema, backfill)
- [ ] **Step 3**: Commit `feat(f2-08): add PropostaAcl model and migration 021 with backfill`

---

## Task 2: Backend — repository + service de ACL

**Files:**
- Create: `app/backend/repositories/proposta_acl_repository.py`
- Create: `app/backend/services/proposta_acl_service.py`
- Create: `app/backend/tests/unit/test_proposta_acl_service.py`

### Repository (métodos mínimos)

```python
class PropostaAclRepository(BaseRepository[PropostaAcl]):
    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaAcl]: ...
    async def get_papeis_for_user(self, proposta_id: UUID, usuario_id: UUID) -> set[PropostaPapel]: ...
    async def add_papel(self, proposta_id: UUID, usuario_id: UUID, papel: PropostaPapel, created_by: UUID) -> PropostaAcl: ...
    async def remove_papel(self, proposta_id: UUID, usuario_id: UUID, papel: PropostaPapel) -> bool: ...
    async def count_owners(self, proposta_id: UUID) -> int: ...
```

### Service

```python
class PropostaAclService:
    HIERARQUIA = {  # papel -> nivel (maior = mais poder)
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
        # VIEWER implicito = 1
    }

    async def conceder(self, proposta_id, usuario_id, papel, created_by) -> PropostaAcl: ...
    async def revogar(self, proposta_id, usuario_id, papel) -> None:
        # Bloqueia se for o ULTIMO OWNER (count_owners == 1 e papel == OWNER)
        ...
    async def listar(self, proposta_id) -> list[PropostaAcl]: ...
    async def papel_efetivo(self, proposta_id, usuario_id) -> PropostaPapel | None:
        # Retorna o MAIOR papel do usuario nesta proposta. None = VIEWER implicito.
        ...
```

### Testes (5+)

- conceder OWNER duplicado → idempotente (não estoura)
- revogar último OWNER → erro 422 ("Proposta não pode ficar sem OWNER")
- `papel_efetivo` retorna o maior quando usuário tem múltiplos
- `papel_efetivo` retorna None se usuário sem ACL nessa proposta
- `count_owners` correto após múltiplas operações

- [ ] **Step 1**: testes
- [ ] **Step 2**: repo + service
- [ ] **Step 3**: pytest PASS + commit `feat(f2-08): add proposta_acl repository and service with last-owner guard`

---

## Task 3: Backend — `require_proposta_role` dependency

**Files:**
- Modify: `app/backend/core/dependencies.py`
- Create: `app/backend/tests/unit/test_proposta_acl_dependency.py`

### Step 1: implementar

```python
async def require_proposta_role(
    proposta_id: UUID,
    papel_minimo: PropostaPapel | None,  # None = qualquer usuario autenticado (VIEWER)
    current_user,
    db: AsyncSession,
) -> PropostaPapel | None:
    """
    Valida que o usuario tem ao menos o papel_minimo na proposta.
    is_admin bypassa. Retorna o papel efetivo (None se VIEWER implicito).

    papel_minimo=None significa "qualquer usuario autenticado pode acessar".
    Util para endpoints de leitura puramente.
    """
    if current_user.is_admin:
        return PropostaPapel.OWNER  # admin tem o maximo

    from backend.services.proposta_acl_service import PropostaAclService
    svc = PropostaAclService(db)
    papel = await svc.papel_efetivo(proposta_id, current_user.id)

    if papel_minimo is None:
        return papel  # VIEWER ou superior = OK

    nivel_user = PropostaAclService.HIERARQUIA.get(papel, 1)  # 1 = VIEWER implicito
    nivel_minimo = PropostaAclService.HIERARQUIA[papel_minimo]
    if nivel_user < nivel_minimo:
        raise AuthorizationError(
            f"Papel insuficiente nesta proposta. Requerido: {papel_minimo.value}."
        )
    return papel
```

### Step 2: testes

7 cenários:
- `is_admin=True` + sem ACL → retorna OWNER (bypass)
- usuário sem ACL + `papel_minimo=None` → retorna None (VIEWER implícito)
- usuário sem ACL + `papel_minimo=EDITOR` → AuthorizationError
- usuário com OWNER + `papel_minimo=EDITOR` → OK retorna OWNER
- usuário com APROVADOR + `papel_minimo=EDITOR` → AuthorizationError (APROVADOR < EDITOR)
- usuário com EDITOR + `papel_minimo=APROVADOR` → OK (EDITOR > APROVADOR)
- usuário com múltiplos papéis (EDITOR + APROVADOR) → retorna o maior (EDITOR)

- [ ] **Step 1**: dependency
- [ ] **Step 2**: testes
- [ ] **Step 3**: pytest PASS + commit `feat(f2-08): add require_proposta_role dependency with admin bypass`

---

## Task 4: Backend — refator dos 5 endpoints

**Files (modificar):**
- `app/backend/api/v1/endpoints/propostas.py`
- `app/backend/api/v1/endpoints/pq_importacao.py`
- `app/backend/api/v1/endpoints/cpu_geracao.py`
- `app/backend/api/v1/endpoints/proposta_export.py`
- `app/backend/api/v1/endpoints/proposta_recursos.py`
- `app/backend/services/proposta_service.py` (criar OWNER no create)
- `app/backend/schemas/proposta.py` (campo `meu_papel`)
- Create: `app/backend/tests/unit/test_propostas_rbac_refactor.py`

### Mapeamento substituição

| Endpoint | Antes | Depois |
|---|---|---|
| `POST /propostas` | `require_cliente_access(data.cliente_id, ...)` | apenas `current_user` autenticado (qualquer um pode criar) |
| `GET /propostas` | exige `cliente_id` query + `require_cliente_access` | sem `cliente_id` obrigatório (passa a ser filtro opcional); retorna todas com `meu_papel` |
| `GET /propostas/{id}` | `require_cliente_access(proposta.cliente_id, ...)` | `require_proposta_role(id, None)` (qualquer auth) |
| `PATCH /propostas/{id}` | `require_cliente_access(...)` | `require_proposta_role(id, EDITOR)` |
| `DELETE /propostas/{id}` | `require_cliente_access(...)` | `require_proposta_role(id, OWNER)` |
| `POST /pq/importar` (vinculado a proposta) | `require_cliente_access(proposta.cliente_id, ...)` | `require_proposta_role(proposta_id, EDITOR)` |
| `GET /pq/itens` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, None)` |
| `PATCH /pq/itens/{id}` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, EDITOR)` |
| `POST /cpu/gerar` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, EDITOR)` |
| `GET /cpu/itens` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, None)` |
| `GET /export/excel` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, None)` |
| `GET /export/pdf` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, None)` |
| `GET /recursos` | `require_cliente_access(...)` | `require_proposta_role(proposta_id, None)` |

### Atenção: `criar_proposta`

Em `proposta_service.criar_proposta`, **na mesma sessão** que persiste a Proposta, chamar `acl_svc.conceder(proposta.id, criado_por_id, OWNER, created_by=criado_por_id)`. Não fazer commit no meio. Garante atomicidade.

### Atenção: `GET /propostas` — adicionar `meu_papel` na resposta

Em `PropostaResponse` adicionar `meu_papel: PropostaPapel | None = None`. Após buscar lista de propostas, fazer 1 query bulk em `proposta_acl` para o `current_user` e mapear na hidratação. **Não** fazer N+1.

```python
# pseudo-codigo
papeis_map = await acl_repo.get_papeis_bulk(proposta_ids, current_user.id)
# papeis_map: {proposta_id: PropostaPapel | None}
items_response = [
    PropostaResponse(**p.__dict__, meu_papel=papeis_map.get(p.id))
    for p in items
]
```

Adicionar método `PropostaAclRepository.get_papeis_bulk(proposta_ids: list[UUID], usuario_id: UUID) -> dict[UUID, PropostaPapel]` (retorna o MAIOR papel por proposta).

### Testes regressão (mínimo 8)

- POST sem ser dono do cliente → **agora 201** (antes era 403)
- PATCH como VIEWER → 403
- PATCH como EDITOR → 200
- DELETE como EDITOR → 403
- DELETE como OWNER → 204
- DELETE como ADMIN global → 204
- GET lista sem cliente_id → 200 com todas as propostas
- GET lista contém `meu_papel` corretamente para cada item

- [ ] **Step 1**: refator dos 5 endpoints + service.criar_proposta
- [ ] **Step 2**: schema PropostaResponse + bulk loader
- [ ] **Step 3**: testes regressão
- [ ] **Step 4**: pytest PASS + commit `refactor(f2-08): replace require_cliente_access with require_proposta_role across proposta endpoints`

---

## Task 5: Backend — endpoints CRUD de ACL

**Files:**
- Create: `app/backend/api/v1/endpoints/proposta_acl.py`
- Modify: `app/backend/api/v1/router.py`
- Modify: `app/backend/schemas/proposta.py`
- Create: `app/backend/tests/unit/test_proposta_acl_endpoints.py`

### Schemas

```python
class PropostaAclResponse(BaseModel):
    id: UUID
    proposta_id: UUID
    usuario_id: UUID
    usuario_nome: str  # join com users
    usuario_email: str
    papel: PropostaPapel
    created_at: datetime
    created_by: UUID
    model_config = ConfigDict(from_attributes=True)

class PropostaAclCreate(BaseModel):
    usuario_id: UUID
    papel: PropostaPapel
```

### Endpoints

```python
router = APIRouter(prefix="/propostas/{proposta_id}/acl", tags=["proposta-acl"])

@router.get("/", response_model=list[PropostaAclResponse])
async def listar_acl(proposta_id, current_user, db):
    # qualquer usuario com papel >= VIEWER pode listar
    await require_proposta_role(proposta_id, None, current_user, db)
    return await acl_svc.listar_com_users(proposta_id)

@router.post("/", response_model=PropostaAclResponse, status_code=201)
async def conceder_papel(proposta_id, body: PropostaAclCreate, current_user, db):
    # somente OWNER pode conceder
    await require_proposta_role(proposta_id, PropostaPapel.OWNER, current_user, db)
    return await acl_svc.conceder(proposta_id, body.usuario_id, body.papel, current_user.id)

@router.delete("/{usuario_id}/{papel}", status_code=204)
async def revogar_papel(proposta_id, usuario_id, papel: PropostaPapel, current_user, db):
    await require_proposta_role(proposta_id, PropostaPapel.OWNER, current_user, db)
    await acl_svc.revogar(proposta_id, usuario_id, papel)
```

### Testes (5+)

- GET ACL como VIEWER autenticado → 200
- POST ACL como EDITOR → 403
- POST ACL como OWNER concedendo EDITOR → 201
- DELETE ACL revogando único OWNER → 422
- POST ACL com papel inválido → 422

- [ ] **Step 1**: schemas + router
- [ ] **Step 2**: registrar router
- [ ] **Step 3**: testes
- [ ] **Step 4**: commit `feat(f2-08): add proposta_acl CRUD endpoints (OWNER-gated)`

---

## Task 6: Frontend — proposalsApi + ProposalShareDialog

**Files:**
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts`
- Create: `app/frontend/src/features/proposals/components/ProposalShareDialog.tsx`

### Step 1: tipos + métodos no proposalsApi

```typescript
export type PropostaPapel = 'OWNER' | 'EDITOR' | 'APROVADOR';
// VIEWER nao existe no enum — e o null/undefined em meu_papel

// Adicionar em PropostaResponse:
//   meu_papel: PropostaPapel | null;

export interface PropostaAclResponse {
  id: string;
  proposta_id: string;
  usuario_id: string;
  usuario_nome: string;
  usuario_email: string;
  papel: PropostaPapel;
  created_at: string;
  created_by: string;
}

export interface PropostaAclCreate {
  usuario_id: string;
  papel: PropostaPapel;
}

async listAcl(propostaId: string) { ... },
async addAcl(propostaId: string, payload: PropostaAclCreate) { ... },
async removeAcl(propostaId: string, usuarioId: string, papel: PropostaPapel) { ... },
```

### Step 2: ProposalShareDialog

- Props: `propostaId`, `open`, `onClose`
- Lista usuários com papel atual (table com colunas Nome, Email, Papel, Ação)
- Autocomplete (`/users` — verificar endpoint existente; senão pegar lista bruta) + Select de papel + botão "Adicionar"
- Botão de remover papel por linha (com confirmação)
- TanStack Query: `['proposta-acl', propostaId]`

- [ ] **Step 1**: api types/methods
- [ ] **Step 2**: dialog component
- [ ] **Step 3**: tsc OK
- [ ] **Step 4**: commit `feat(f2-08): add proposta ACL API client and ProposalShareDialog`

---

## Task 7: Frontend — esconder ações conforme papel

**Files:**
- Modify: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx`

### ProposalDetailPage

- Botão "Compartilhar" (ícone `ShareIcon`) — visível **somente se** `proposta.meu_papel === 'OWNER'` ou `currentUser.is_admin`
- Botão "Excluir" — mesma regra (somente OWNER/admin)
- Botões "Editar", "Importar PQ", "Gerar CPU", "Recalcular BDI" — visíveis se `meu_papel in ['OWNER', 'EDITOR']` ou admin
- Botões "Aprovar"/"Rejeitar" (se status `AGUARDANDO_APROVACAO`) — visíveis se `meu_papel in ['OWNER', 'APROVADOR']` ou admin (preparar slot — implementação completa fica para F2-09)
- Helper: `function podeEditar(papel) { return papel === 'OWNER' || papel === 'EDITOR'; }`

### ProposalsListPage

- Remover obrigatoriedade do filtro `cliente_id`. Cliente vira filtro **opcional**.
- Coluna nova "Meu papel" mostrando badge: OWNER/EDITOR/APROVADOR/VIEWER (quando `meu_papel === null`)
- Default: lista todas as propostas

- [ ] **Step 1**: ProposalDetailPage com gating de botões
- [ ] **Step 2**: ProposalsListPage com filtro opcional + coluna meu_papel
- [ ] **Step 3**: tsc OK
- [ ] **Step 4**: commit `feat(f2-08): conditional UI actions based on proposta_acl role`

---

## Task 8: Validação final

- [ ] `cd app && python -m pytest backend/tests/ --tb=short` → **145+ PASS, 0 FAIL** (a sprint adiciona ~20 testes novos sobre ~143)
- [ ] `cd app/frontend && npx tsc --noEmit` → **0 erros**
- [ ] Verificar regressão de match (F2-03/F2-04/F2-07) ainda passa
- [ ] **Validação de migração manual** (se DB local disponível): `alembic upgrade head` aplica 021 sem erro; SELECT count(*) em `proposta_acl` = count(*) em `propostas WHERE criado_por_id IS NOT NULL`
- [ ] Smoke manual no frontend: usuário não-OWNER não enxerga botão Excluir; ADMIN enxerga tudo
- [ ] Atualizar `BACKLOG.md` (status F2-08 → TESTED)
- [ ] Criar `docs/sprints/F2-08/technical-review/technical-review-2026-04-26-f2-08.md`
- [ ] Criar `docs/sprints/F2-08/walkthrough/done/walkthrough-F2-08.md`

---

## Self-Review

**Spec coverage:**
- ✅ Tabela `proposta_acl` com 3 papéis (OWNER/EDITOR/APROVADOR), VIEWER implícito
- ✅ Migration 021 com backfill OWNER para criadores existentes
- ✅ `require_proposta_role` substitui `require_cliente_access` em 5 routers
- ✅ Criador automaticamente vira OWNER
- ✅ Somente OWNER deleta proposta
- ✅ ADMIN global bypassa via `is_admin`
- ✅ `GET /propostas` retorna todas com `meu_papel`
- ✅ Endpoints CRUD de ACL (gating por OWNER)
- ✅ Last-OWNER guard (não pode revogar último OWNER)
- ✅ Frontend: modal de compartilhamento + UI condicional

**Decisões arquiteturais:**
- VIEWER **não** é armazenado — é o default implícito. Reduz volume de linhas e simplifica query de listagem.
- ACL ligada a `proposta_id` nesta sprint (não `proposta_root_id`). Em F2-09 (versionamento), `require_proposta_role` será modificada para resolver via `proposta_root_id` — refator pequeno.
- Hierarquia EDITOR > APROVADOR é deliberada: APROVADOR é papel restrito (só aprova/rejeita), enquanto EDITOR pode tudo de operacional. APROVADOR não pode editar — só aprovar.
- Endpoints de leitura usam `papel_minimo=None` (qualquer usuário autenticado). É a interpretação do "VIEWER implícito".
- Bulk loader em `GET /propostas` evita N+1 ao computar `meu_papel`.
- Backfill no `down_revision` apenas dropa tabela e enum — não tenta reverter ACL para cliente.

**Critérios de aceite finais:**
- 145+ pytest PASS, 0 FAIL
- 0 erros tsc
- Migration 021 sintaticamente correta
- Backfill OWNER aplicado a 100% das propostas existentes com `criado_por_id`
- Endpoints de proposta retornam 403 corretamente para usuários sem papel suficiente
- Endpoints de proposta retornam 200/201 corretamente para usuários com papel suficiente, **independentemente do cliente da proposta**
- Frontend: usuário VIEWER vê listagem mas não edita; OWNER vê botão Compartilhar; ADMIN vê tudo
