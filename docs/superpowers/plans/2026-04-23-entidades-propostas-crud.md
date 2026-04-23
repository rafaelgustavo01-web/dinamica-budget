# Entidades e CRUD de Propostas — Implementation Plan

> **Goal:** Criar a fundação de dados para o Módulo de Orçamentos (Fase 2).

---

## Task 1: Enums e Modelagem de Dados

**Files:**
- Modify: `app/models/enums.py`
- Create: `app/models/proposta.py`

### Step 1: Enums
Adicionar `StatusProposta`, `StatusImportacao`, `StatusMatch` e `TipoServicoMatch`.

### Step 2: Modelos
Implementar as classes `Proposta`, `PqImportacao`, `PqItem`, `PropostaItem` e `PropostaItemComposicao` conforme especificado na `MODELAGEM_ORCAMENTOS_FASE2.md`.
*Nota: Usar schema "operacional".*

---

## Task 2: Repositories e Camada de Acesso

**Files:**
- Create: `app/repositories/proposta_repository.py`
- Create: `app/repositories/pq_item_repository.py`

### Step 1: Base CRUD
Implementar métodos `get_by_id`, `list_by_cliente`, `create`, `update` e `soft_delete`.

---

## Task 3: PropostaService (Lógica de Negócio)

**Files:**
- Create: `app/services/proposta_service.py`

### Step 1: Implementar PropostaService
- `criar_proposta(cliente_id, usuario_id, dados)`
- `listar_propostas(cliente_id)`
- `obter_detalhe(proposta_id, cliente_id)`
- `atualizar_status(proposta_id, novo_status)`

---

## Task 4: API Endpoints

**Files:**
- Create: `app/api/v1/endpoints/propostas.py`
- Modify: `app/api/v1/router.py`

### Step 1: Implementar Rotas
- `POST /`
- `GET /`
- `GET /{id}`
- `PATCH /{id}`
- `DELETE /{id}`

*Obrigatório: Usar dependência `require_cliente_access`.*

---

## Task 5: Migração e Testes

**Files:**
- Create: `app/tests/unit/test_proposta_service.py`
- Run: `alembic revision --autogenerate -m "create_proposta_entities"`

### Step 1: Alembic
Gerar e revisar a migration. Executar `upgrade head`.

### Step 2: Testes Unitários
Validar criação de proposta e isolamento entre clientes.

---

## Task 6: Walkthrough

**Files:**
- Create: `docs/walkthrough/done/walkthrough-S-09.md`

### Step 1: Registrar entrega
Documentar as novas entidades e rotas criadas.
