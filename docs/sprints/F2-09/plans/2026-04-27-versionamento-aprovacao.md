# F2-09: Versionamento de Propostas + Workflow de Aprovação — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar ciclo de vida completo às propostas: (1) versionamento — cada proposta pode gerar múltiplas versões concretas agrupadas por `proposta_root_id`; (2) workflow de aprovação opcional — proposta com `requer_aprovacao=True` passa por fluxo `CPU_GERADA → AGUARDANDO_APROVACAO → APROVADA/CPU_GERADA`.

**Architecture:**
- Migration 022: adicionar 8 campos na tabela `propostas` + novo valor `AGUARDANDO_APROVACAO` no enum `status_proposta_enum`. Backfill: `proposta_root_id = id`, `numero_versao = 1`, `is_versao_atual = TRUE`. `ALTER TYPE` requer bloco autocommit em Alembic.
- `require_proposta_role` (já em `core/dependencies.py`): atualizar para resolver ACL via `proposta.proposta_root_id`, não `proposta.id` — versões herdam permissões da raiz automaticamente.
- `PropostaVersionamentoService`: `nova_versao`, `enviar_aprovacao`, `aprovar`, `rejeitar`, `listar_versoes`.
- 5 endpoints novos em `propostas.py` + registrar rota `/propostas/aprovacoes` na lista global.
- Frontend: `ProposalHistoryPanel` como aba colapsável no `ProposalDetailPage` + botões condicionais + `ApprovalQueuePage` em `/propostas/aprovacoes`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Pré-requisito de leitura (obrigatório antes de codar)

**Leia na ordem antes de começar:**

1. `docs/shared/superpowers/plans/roadmap/ROADMAP.md` — Milestone 6, Fase 6.7
2. `docs/sprints/F2-08/technical-review/technical-review-2026-04-26-f2-08.md` — o que F2-08 entregou (PropostaPapel, require_proposta_role, proposta_acl)
3. `app/backend/models/proposta.py` — campos atuais do model `Proposta` (sem versioning ainda)
4. `app/backend/models/enums.py` — `StatusProposta` (RASCUNHO/CPU_GERADA/APROVADA), `PropostaPapel`
5. `app/backend/core/dependencies.py` — `require_proposta_role` atual (resolve por `proposta_id`)
6. `app/backend/api/v1/endpoints/propostas.py` — padrão de endpoint pós F2-08
7. `app/backend/services/proposta_service.py` — `criar_proposta`, `soft_delete`
8. `app/alembic/versions/021_proposta_acl.py` — padrão de migration mais recente
9. `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` — onde entram aba Histórico e botões
10. `app/frontend/src/features/proposals/routes.tsx` — rotas existentes

**Decisões já tomadas (não rediscutir):**
- `VIEWER` implícito = qualquer autenticado (não mora em `proposta_acl`)
- `proposta_acl` permanece com FK para `proposta_root_id` (raiz). Versões NÃO têm linha própria em `proposta_acl`.
- `nova_versao` clona apenas **metadados** (titulo, cliente, descricao, pc_cabecalho_id, requer_aprovacao). PQ e CPU começam do zero (RASCUNHO). Não clone pq_itens nem proposta_itens.
- `APROVADOR` pode aprovar/rejeitar mas NÃO pode enviar para aprovação (somente EDITOR/OWNER enviam).
- Workflow de aprovação é **opcional** por proposta via flag `requer_aprovacao`.
- `rejeitar` retorna status para `CPU_GERADA` (proposta volta para editável, não é arquivada).

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/backend/models/enums.py` | Modificar | Adicionar `AGUARDANDO_APROVACAO` em `StatusProposta` |
| `app/backend/models/proposta.py` | Modificar | Adicionar 8 campos de versioning em `Proposta` |
| `app/alembic/versions/022_proposta_versionamento.py` | Criar | Migration: campos + enum value + backfill + unique constraint |
| `app/backend/core/dependencies.py` | Modificar | `require_proposta_role`: resolver ACL via `proposta_root_id` |
| `app/backend/services/proposta_versionamento_service.py` | Criar | `nova_versao`, `enviar_aprovacao`, `aprovar`, `rejeitar`, `listar_versoes` |
| `app/backend/schemas/proposta.py` | Modificar | Adicionar campos de versioning em `PropostaResponse`; novos request schemas |
| `app/backend/api/v1/endpoints/propostas.py` | Modificar | 5 endpoints novos: nova-versao, enviar-aprovacao, aprovar, rejeitar, versoes |
| `app/backend/api/v1/router.py` | Modificar | Rota aprovacoes se necessário |
| `app/backend/tests/unit/test_proposta_versionamento_service.py` | Criar | 8+ testes do service |
| `app/backend/tests/unit/test_proposta_versionamento_endpoints.py` | Criar | 8+ testes dos endpoints |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | Campos novos em `PropostaResponse` + métodos: `novaVersao`, `enviarAprovacao`, `aprovar`, `rejeitar`, `listarVersoes` |
| `app/frontend/src/features/proposals/components/ProposalHistoryPanel.tsx` | Criar | Tabela de versões com link para cada uma |
| `app/frontend/src/features/proposals/pages/ApprovalQueuePage.tsx` | Criar | Lista de propostas `AGUARDANDO_APROVACAO` onde user é APROVADOR/OWNER |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificar | Aba Histórico + botões condicionais por papel/status |
| `app/frontend/src/features/proposals/routes.tsx` | Modificar | Rota `/propostas/aprovacoes` |

---

## Task 1: Backend — migration 022 + model

**Files:**
- Modify: `app/backend/models/enums.py`
- Modify: `app/backend/models/proposta.py`
- Create: `app/alembic/versions/022_proposta_versionamento.py`

### Step 1: Enum `StatusProposta`

```python
class StatusProposta(str, enum.Enum):
    RASCUNHO = "RASCUNHO"
    CPU_GERADA = "CPU_GERADA"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    APROVADA = "APROVADA"
```

### Step 2: Campos no model `Proposta`

Adicionar após `deleted_at` (antes dos relationships):

```python
# Versionamento
proposta_root_id: Mapped[UUID] = mapped_column(
    PGUUID(as_uuid=True), nullable=True, index=True
)
numero_versao: Mapped[int] = mapped_column(Integer, nullable=True, default=1)
versao_anterior_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("operacional.propostas.id"),
    nullable=True,
)
is_versao_atual: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
is_fechada: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

# Aprovação
requer_aprovacao: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
aprovado_por_id: Mapped[UUID | None] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("operacional.usuarios.id"),
    nullable=True,
)
aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
motivo_revisao: Mapped[str | None] = mapped_column(Text, nullable=True)
```

Adicionar ao `__table_args__`:
```python
UniqueConstraint("proposta_root_id", "numero_versao", name="uq_proposta_versao")
```
Atenção: `__table_args__` hoje é `{"schema": "operacional"}`. Mudar para tuple:
```python
__table_args__ = (
    UniqueConstraint("proposta_root_id", "numero_versao", name="uq_proposta_versao"),
    {"schema": "operacional"},
)
```

### Step 3: Migration 022

**ATENÇÃO CRÍTICA:** `ALTER TYPE ... ADD VALUE` não pode rodar dentro de uma transação no PostgreSQL. Usar `autocommit_block` do Alembic:

```python
# app/alembic/versions/022_proposta_versionamento.py
revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID

def upgrade():
    # 1. ADD VALUE ao enum FORA de transação
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE operacional.status_proposta_enum "
            "ADD VALUE IF NOT EXISTS 'AGUARDANDO_APROVACAO'"
        )

    # 2. Adicionar colunas (dentro de transação normal)
    op.add_column("propostas",
        sa.Column("proposta_root_id", PGUUID(as_uuid=True), nullable=True, index=True),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("numero_versao", sa.Integer(), nullable=True, server_default="1"),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("versao_anterior_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("is_versao_atual", sa.Boolean(), nullable=True, server_default="TRUE"),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("is_fechada", sa.Boolean(), nullable=True, server_default="FALSE"),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("requer_aprovacao", sa.Boolean(), nullable=True, server_default="FALSE"),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("aprovado_por_id", PGUUID(as_uuid=True), nullable=True),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("aprovado_em", sa.DateTime(timezone=True), nullable=True),
        schema="operacional"
    )
    op.add_column("propostas",
        sa.Column("motivo_revisao", sa.Text(), nullable=True),
        schema="operacional"
    )

    # 3. Backfill: proposta_root_id = id, numero_versao = 1, is_versao_atual = TRUE
    op.execute("""
        UPDATE operacional.propostas
        SET proposta_root_id = id,
            numero_versao = 1,
            is_versao_atual = TRUE,
            is_fechada = FALSE
        WHERE proposta_root_id IS NULL
    """)

    # 4. FK versao_anterior_id (self-ref, nullable)
    op.create_foreign_key(
        "fk_proposta_versao_anterior",
        "propostas", "propostas",
        ["versao_anterior_id"], ["id"],
        source_schema="operacional", referent_schema="operacional",
    )

    # 5. FK aprovado_por_id
    op.create_foreign_key(
        "fk_proposta_aprovado_por",
        "propostas", "usuarios",
        ["aprovado_por_id"], ["id"],
        source_schema="operacional", referent_schema="operacional",
    )

    # 6. Unique constraint
    op.create_unique_constraint(
        "uq_proposta_versao",
        "propostas",
        ["proposta_root_id", "numero_versao"],
        schema="operacional",
    )

def downgrade():
    op.drop_constraint("uq_proposta_versao", "propostas", schema="operacional")
    op.drop_constraint("fk_proposta_versao_anterior", "propostas", schema="operacional", type_="foreignkey")
    op.drop_constraint("fk_proposta_aprovado_por", "propostas", schema="operacional", type_="foreignkey")
    for col in ["proposta_root_id", "numero_versao", "versao_anterior_id",
                "is_versao_atual", "is_fechada", "requer_aprovacao",
                "aprovado_por_id", "aprovado_em", "motivo_revisao"]:
        op.drop_column("propostas", col, schema="operacional")
    # Nota: não é possível remover um valor de enum no PostgreSQL sem recriar o tipo.
    # O downgrade remove apenas as colunas.
```

- [ ] **Step 1**: enum + model
- [ ] **Step 2**: migration 022 com autocommit_block + backfill
- [ ] **Step 3**: commit `feat(f2-09): add versioning and approval fields to Proposta model + migration 022`

---

## Task 2: Backend — atualizar `require_proposta_role`

**File:** `app/backend/core/dependencies.py`

Hoje `require_proposta_role` chama `acl_svc.papel_efetivo(proposta_id, ...)`. Após o versionamento, versões (proposta.id != proposta_root_id) precisam usar a ACL da raiz.

```python
async def require_proposta_role(
    proposta_id: UUID,
    papel_minimo: "PropostaPapel | None",
    current_user,
    db: AsyncSession,
) -> "PropostaPapel | None":
    if current_user.is_admin:
        return PropostaPapel.OWNER

    # Resolver root: versões herdam ACL da raiz
    from backend.repositories.proposta_repository import PropostaRepository
    repo = PropostaRepository(db)
    proposta = await repo.get_by_id(proposta_id)
    if proposta is None:
        raise NotFoundError(f"Proposta '{proposta_id}' não encontrada.")

    # root_id = proposta_root_id quando disponível, senão o próprio id (legado)
    root_id = proposta.proposta_root_id or proposta_id

    from backend.services.proposta_acl_service import PropostaAclService
    svc = PropostaAclService(db)
    papel = await svc.papel_efetivo(root_id, current_user.id)

    if papel_minimo is None:
        return papel

    nivel_user = PropostaAclService.HIERARQUIA.get(papel, 1)
    nivel_minimo = PropostaAclService.HIERARQUIA[papel_minimo]
    if nivel_user < nivel_minimo:
        raise AuthorizationError(
            f"Papel insuficiente nesta proposta. Requerido: {papel_minimo.value}."
        )
    return papel
```

Atenção: esta mudança é **retrocompatível** — propostas existentes têm `proposta_root_id = id` após backfill, então o comportamento de F2-08 é preservado integralmente.

- [ ] **Step 1**: atualizar `require_proposta_role`
- [ ] **Step 2**: pytest passando (regressão F2-08)
- [ ] **Step 3**: commit `refactor(f2-09): require_proposta_role resolves ACL via proposta_root_id for version inheritance`

---

## Task 3: Backend — `PropostaVersionamentoService`

**Files:**
- Create: `app/backend/services/proposta_versionamento_service.py`
- Create: `app/backend/tests/unit/test_proposta_versionamento_service.py`

```python
class PropostaVersionamentoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PropostaRepository(db)

    async def nova_versao(
        self,
        proposta_id: UUID,
        criador_id: UUID,
        motivo_revisao: str | None = None,
    ) -> Proposta:
        """
        Clona metadados da versão atual, fecha-a e cria nova versão numerada.
        PQ e CPU iniciam do zero (RASCUNHO).
        """
        atual = await self.repo.get_by_id(proposta_id)
        if atual is None:
            raise NotFoundError(f"Proposta '{proposta_id}' não encontrada.")
        if not atual.is_versao_atual:
            raise UnprocessableEntityError("Só é possível criar nova versão a partir da versão atual.")
        if atual.is_fechada:
            raise UnprocessableEntityError("A versão atual está fechada. Não é possível gerar nova versão.")

        # Buscar próximo numero_versao
        max_versao = await self.repo.max_numero_versao(atual.proposta_root_id)
        proximo_numero = (max_versao or 1) + 1

        # Fechar versão atual
        atual.is_versao_atual = False
        atual.is_fechada = True
        self.db.add(atual)
        await self.db.flush()

        # Criar nova versão
        nova = Proposta(
            cliente_id=atual.cliente_id,
            criado_por_id=criador_id,
            codigo=f"{atual.codigo.split('-v')[0]}-v{proximo_numero}",
            titulo=atual.titulo,
            descricao=atual.descricao,
            proposta_root_id=atual.proposta_root_id,
            numero_versao=proximo_numero,
            versao_anterior_id=atual.id,
            is_versao_atual=True,
            is_fechada=False,
            status=StatusProposta.RASCUNHO,
            requer_aprovacao=atual.requer_aprovacao,
            pc_cabecalho_id=atual.pc_cabecalho_id,
            motivo_revisao=motivo_revisao,
        )
        self.db.add(nova)
        await self.db.flush()
        await self.db.refresh(nova)
        return nova

    async def enviar_aprovacao(self, proposta_id: UUID) -> Proposta:
        proposta = await self._get_or_404(proposta_id)
        if not proposta.requer_aprovacao:
            raise UnprocessableEntityError("Esta proposta não requer aprovação formal.")
        if proposta.status != StatusProposta.CPU_GERADA:
            raise UnprocessableEntityError(
                f"Proposta deve estar em CPU_GERADA para enviar aprovação. Status atual: {proposta.status.value}"
            )
        proposta.status = StatusProposta.AGUARDANDO_APROVACAO
        self.db.add(proposta)
        await self.db.flush()
        await self.db.refresh(proposta)
        return proposta

    async def aprovar(self, proposta_id: UUID, aprovador_id: UUID) -> Proposta:
        proposta = await self._get_or_404(proposta_id)
        if proposta.status != StatusProposta.AGUARDANDO_APROVACAO:
            raise UnprocessableEntityError(
                f"Proposta não está aguardando aprovação. Status atual: {proposta.status.value}"
            )
        proposta.status = StatusProposta.APROVADA
        proposta.aprovado_por_id = aprovador_id
        proposta.aprovado_em = datetime.now(UTC)
        self.db.add(proposta)
        await self.db.flush()
        await self.db.refresh(proposta)
        return proposta

    async def rejeitar(self, proposta_id: UUID, aprovador_id: UUID, motivo: str | None = None) -> Proposta:
        proposta = await self._get_or_404(proposta_id)
        if proposta.status != StatusProposta.AGUARDANDO_APROVACAO:
            raise UnprocessableEntityError(
                f"Proposta não está aguardando aprovação. Status atual: {proposta.status.value}"
            )
        proposta.status = StatusProposta.CPU_GERADA
        proposta.aprovado_por_id = None
        proposta.aprovado_em = None
        if motivo:
            proposta.motivo_revisao = motivo
        self.db.add(proposta)
        await self.db.flush()
        await self.db.refresh(proposta)
        return proposta

    async def listar_versoes(self, proposta_root_id: UUID) -> list[Proposta]:
        return await self.repo.list_by_root(proposta_root_id)

    async def _get_or_404(self, proposta_id: UUID) -> Proposta:
        p = await self.repo.get_by_id(proposta_id)
        if p is None:
            raise NotFoundError(f"Proposta '{proposta_id}' não encontrada.")
        return p
```

Adicionar em `PropostaRepository`: `max_numero_versao(root_id)` e `list_by_root(root_id)`.

### Testes (8 mínimo)

- `nova_versao` em proposta não-atual → UnprocessableEntityError
- `nova_versao` em proposta fechada → UnprocessableEntityError
- `nova_versao` válida → nova versão com numero_versao=2, anterior fechada, status=RASCUNHO
- `enviar_aprovacao` sem `requer_aprovacao=True` → UnprocessableEntityError
- `enviar_aprovacao` com status errado (RASCUNHO) → UnprocessableEntityError
- `enviar_aprovacao` válida → status=AGUARDANDO_APROVACAO
- `aprovar` com status errado → UnprocessableEntityError
- `aprovar` válida → status=APROVADA, aprovado_por_id preenchido
- `rejeitar` válida → status=CPU_GERADA, motivo salvo

- [ ] **Step 1**: testes
- [ ] **Step 2**: service + repository methods
- [ ] **Step 3**: pytest PASS + commit `feat(f2-09): add PropostaVersionamentoService with nova_versao, approve/reject workflow`

---

## Task 4: Backend — schemas + 5 endpoints

**Files:**
- Modify: `app/backend/schemas/proposta.py`
- Modify: `app/backend/api/v1/endpoints/propostas.py`
- Create: `app/backend/tests/unit/test_proposta_versionamento_endpoints.py`

### Schemas novos

```python
class PropostaNovaVersaoRequest(BaseModel):
    motivo_revisao: str | None = None

class PropostaAprovarRequest(BaseModel):
    pass  # corpo vazio, aprovador vem do current_user

class PropostaRejeitarRequest(BaseModel):
    motivo: str | None = None
```

Adicionar em `PropostaResponse` (todos opcionais, nullable para retrocompatibilidade):
```python
proposta_root_id: UUID | None = None
numero_versao: int | None = None
versao_anterior_id: UUID | None = None
is_versao_atual: bool | None = None
is_fechada: bool | None = None
requer_aprovacao: bool = False
aprovado_por_id: UUID | None = None
aprovado_em: datetime | None = None
motivo_revisao: str | None = None
```

### Endpoints (adicionar em `propostas.py`)

```python
@router.get("/aprovacoes", response_model=list[PropostaResponse])
async def fila_aprovacoes(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropostaResponse]:
    """Propostas AGUARDANDO_APROVACAO onde o user é APROVADOR ou OWNER."""
    ...  # busca propostas com status=AGUARDANDO_APROVACAO
         # filtra pelas que o user tem papel >= APROVADOR

@router.get("/root/{root_id}/versoes", response_model=list[PropostaResponse])
async def listar_versoes(
    root_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropostaResponse]:
    await require_proposta_role(root_id, None, current_user, db)
    svc = PropostaVersionamentoService(db)
    versoes = await svc.listar_versoes(root_id)
    return [PropostaResponse.model_validate(v) for v in versoes]

@router.post("/{proposta_id}/nova-versao", response_model=PropostaResponse, status_code=201)
async def nova_versao(
    proposta_id: UUID,
    body: PropostaNovaVersaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    nova = await svc.nova_versao(proposta_id, current_user.id, body.motivo_revisao)
    await db.commit()
    return PropostaResponse.model_validate(nova)

@router.post("/{proposta_id}/enviar-aprovacao", response_model=PropostaResponse)
async def enviar_aprovacao(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    proposta = await svc.enviar_aprovacao(proposta_id)
    await db.commit()
    return PropostaResponse.model_validate(proposta)

@router.post("/{proposta_id}/aprovar", response_model=PropostaResponse)
async def aprovar_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.APROVADOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    proposta = await svc.aprovar(proposta_id, current_user.id)
    await db.commit()
    return PropostaResponse.model_validate(proposta)

@router.post("/{proposta_id}/rejeitar", response_model=PropostaResponse)
async def rejeitar_proposta(
    proposta_id: UUID,
    body: PropostaRejeitarRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.APROVADOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    proposta = await svc.rejeitar(proposta_id, current_user.id, body.motivo)
    await db.commit()
    return PropostaResponse.model_validate(proposta)
```

**Atenção:** rota `/aprovacoes` e `/root/{root_id}/versoes` devem ser declaradas **ANTES** de `/{proposta_id}` no router para evitar conflito de match (FastAPI resolve rotas na ordem de registro).

### Testes de endpoint (8 mínimo)

- GET `/root/{root_id}/versoes` como VIEWER → 200
- POST `/nova-versao` como VIEWER → 403
- POST `/nova-versao` como EDITOR → 201, versão criada
- POST `/enviar-aprovacao` sem requer_aprovacao=True → 422
- POST `/aprovar` como EDITOR (não APROVADOR) → 403
- POST `/aprovar` como APROVADOR → 200, status=APROVADA
- POST `/rejeitar` como APROVADOR → 200, status=CPU_GERADA
- GET `/aprovacoes` → lista só propostas onde user tem papel >= APROVADOR

- [ ] **Step 1**: schemas
- [ ] **Step 2**: endpoints (atenção à ordem de registro)
- [ ] **Step 3**: testes
- [ ] **Step 4**: pytest PASS + commit `feat(f2-09): add versioning and approval endpoints`

---

## Task 5: Frontend — API client

**File:** `app/frontend/src/shared/services/api/proposalsApi.ts`

Adicionar ao final do arquivo:

```typescript
// Versionamento + Aprovação
export interface PropostaNovaVersaoRequest {
  motivo_revisao?: string;
}

export interface PropostaRejeitarRequest {
  motivo?: string;
}

// Em PropostaResponse adicionar campos opcionais:
// proposta_root_id?: string;
// numero_versao?: number;
// versao_anterior_id?: string | null;
// is_versao_atual?: boolean;
// is_fechada?: boolean;
// requer_aprovacao?: boolean;
// aprovado_por_id?: string | null;
// aprovado_em?: string | null;
// motivo_revisao?: string | null;

async listarVersoes(rootId: string) {
  const res = await apiClient.get<PropostaResponse[]>(`/propostas/root/${rootId}/versoes`);
  return res.data;
},

async novaVersao(propostaId: string, payload: PropostaNovaVersaoRequest) {
  const res = await apiClient.post<PropostaResponse>(`/propostas/${propostaId}/nova-versao`, payload);
  return res.data;
},

async enviarAprovacao(propostaId: string) {
  const res = await apiClient.post<PropostaResponse>(`/propostas/${propostaId}/enviar-aprovacao`);
  return res.data;
},

async aprovar(propostaId: string) {
  const res = await apiClient.post<PropostaResponse>(`/propostas/${propostaId}/aprovar`);
  return res.data;
},

async rejeitar(propostaId: string, payload: PropostaRejeitarRequest) {
  const res = await apiClient.post<PropostaResponse>(`/propostas/${propostaId}/rejeitar`, payload);
  return res.data;
},

async filaAprovacoes() {
  const res = await apiClient.get<PropostaResponse[]>(`/propostas/aprovacoes`);
  return res.data;
},
```

- [ ] **Step 1**: tipos + métodos (append ao final, sem reescrever blocos existentes)
- [ ] **Step 2**: tsc OK
- [ ] **Step 3**: commit `feat(f2-09): add versioning/approval API client methods`

---

## Task 6: Frontend — UI

**Files:**
- Create: `app/frontend/src/features/proposals/components/ProposalHistoryPanel.tsx`
- Create: `app/frontend/src/features/proposals/pages/ApprovalQueuePage.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- Modify: `app/frontend/src/features/proposals/routes.tsx`

### ProposalHistoryPanel

- Props: `proposta: PropostaResponse`
- Se `proposta.proposta_root_id` disponível, chama `listarVersoes(proposta_root_id)`
- Exibe tabela: Versão nº | Status (Badge) | Data | Motivo | Ação (Link "Abrir")
- Versão atual marcada com chip "Atual"
- `useQuery(['proposta-versoes', proposta.proposta_root_id])`

### ProposalDetailPage — alterações

**Badge de status:** adicionar cor/label para `AGUARDANDO_APROVACAO` (cor amber/warning).

**Seção de versão** (logo abaixo do header de status):
```
Versão 2 de 3  |  [Histórico ▾]  |  [Nova Versão] (EDITOR+, não fechada)
```

**Toggle "Requer aprovação"** (somente OWNER, em modo de edição/chips de config):
```
[Switch] Esta versão precisa de aprovação formal
```

**Botão "Enviar para Aprovação"** — visível quando:
- `proposta.requer_aprovacao === true`
- `proposta.status === 'CPU_GERADA'`
- `meu_papel in ['OWNER', 'EDITOR']`

**Botões "Aprovar" / "Rejeitar"** — visíveis quando:
- `proposta.status === 'AGUARDANDO_APROVACAO'`
- `meu_papel in ['OWNER', 'APROVADOR']`
- "Rejeitar" abre Dialog com campo de motivo

**Seção de aprovação** (visível quando `status === 'APROVADA'`):
```
✅ Aprovada em [data]  por [aprovador]
```

### ApprovalQueuePage

- Rota: `/propostas/aprovacoes`
- `useQuery(['fila-aprovacoes'])` → `filaAprovacoes()`
- Tabela: Código | Cliente | Título | Nº Versão | Enviada em | Ações
- Ações por linha: "Abrir" (link para detail) + "Aprovar" + "Rejeitar"
- Aprovar inline (sem modal) → mutation + invalidate
- Rejeitar → Dialog com campo motivo obrigatório

### routes.tsx

Adicionar:
```typescript
const ApprovalQueuePage = lazy(() => import('./pages/ApprovalQueuePage'));
// ...
{ path: 'aprovacoes', element: <ApprovalQueuePage /> },
```

Atenção: a rota `aprovacoes` deve vir **antes** da rota `:id` para evitar que "aprovacoes" seja interpretado como um UUID.

- [ ] **Step 1**: ProposalHistoryPanel
- [ ] **Step 2**: ApprovalQueuePage
- [ ] **Step 3**: ProposalDetailPage (badge + seção versão + toggle + botões condicionais)
- [ ] **Step 4**: routes.tsx
- [ ] **Step 5**: tsc OK + commit `feat(f2-09): add ProposalHistoryPanel, ApprovalQueuePage and conditional approval UI`

---

## Task 7: Validação final

- [ ] `cd app && python -m pytest backend/tests/ --tb=short` → **170+ PASS, 0 FAIL** (adiciona ~16 novos testes sobre 158)
- [ ] `cd app/frontend && npx tsc --noEmit` → **0 erros**
- [ ] Verificar regressão de F2-08: `require_proposta_role` ainda funciona para propostas sem versioning (proposta_root_id = id)
- [ ] Validação manual de migração (se DB disponível):
  - `alembic upgrade head` sem erro
  - `SELECT count(*) FROM operacional.propostas WHERE proposta_root_id IS NULL` = 0
  - `SELECT count(*) FROM operacional.propostas WHERE is_versao_atual = TRUE` = `SELECT count(*) FROM operacional.propostas WHERE deleted_at IS NULL`
- [ ] Smoke: `POST /nova-versao` retorna 201 com `numero_versao = 2`; versão anterior tem `is_versao_atual = FALSE`
- [ ] Rota `/aprovacoes` no frontend registrada antes de `/:id` (sem conflito de match)
- [ ] Atualizar `BACKLOG.md` (F2-09 → TESTED)
- [ ] Criar `docs/sprints/F2-09/technical-review/technical-review-2026-04-27-f2-09.md`
- [ ] Criar `docs/sprints/F2-09/walkthrough/done/walkthrough-F2-09.md`

---

## Self-Review

**Spec coverage:**
- ✅ Migration 022: 8 campos + enum value `AGUARDANDO_APROVACAO` + backfill + UNIQUE constraint
- ✅ `require_proposta_role` resolve ACL via `proposta_root_id` (versões herdam permissões da raiz)
- ✅ `nova_versao`: clona metadados, fecha anterior, cria v2 limpa (RASCUNHO)
- ✅ Workflow: `enviar_aprovacao` → `aprovar` / `rejeitar` com guards de status
- ✅ Endpoints: nova-versao, enviar-aprovacao, aprovar, rejeitar, versoes, aprovacoes
- ✅ Frontend: ProposalHistoryPanel + ApprovalQueuePage + botões condicionais

**Decisões arquiteturais:**
- `nova_versao` não clona PQ/CPU — versão nova começa limpa (RASCUNHO). Evita dados duplicados e mantém a nova versão independente.
- `rejeitar` volta para `CPU_GERADA` (não para RASCUNHO) — a CPU já existe e pode ser reavaliada.
- Rota `/aprovacoes` declarada antes de `/{proposta_id}` para evitar clash de match.
- `ALTER TYPE ... ADD VALUE` usa `autocommit_block` — obrigatório no PostgreSQL.
- `proposta_root_id` nullable na coluna mas backfill garante NOT NULL em dados existentes. Novos registros são populados no service.

**Critérios de aceite:**
- 170+ pytest PASS, 0 FAIL
- 0 erros tsc
- Migration 022 aplicada sem erro
- Todas as propostas existentes com `proposta_root_id` preenchido (backfill)
- Versões herdam ACL da raiz corretamente
- Workflow AGUARDANDO_APROVACAO → APROVADA / CPU_GERADA funcional
