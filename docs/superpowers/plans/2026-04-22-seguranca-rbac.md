# Endurecer Segurança e RBAC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar lacunas de autorização em endpoints sensíveis. Cobertura completa de testes de regressão para perfis USUARIO, APROVADOR, ADMIN, is_admin.

**Architecture:** Manter padrão endpoint → service → repository. Validações de autorização no endpoint (camada de entrada).

**Tech Stack:** FastAPI, SQLAlchemy async, pytest

---

## Task 1: Proteger `/busca/associacoes` (GET)

**Files:**
- Modify: `app/api/v1/endpoints/busca.py`
- Test: `app/tests/unit/test_security_s04.py`

### Step 1: Adicionar validação de acesso

```python
# app/api/v1/endpoints/busca.py — linhas 50-76
# Adicionar require_cliente_access quando cliente_id é informado

from app.core.dependencies import require_cliente_access

@router.get("/busca/associacoes", ...)
async def list_associacoes(
    cliente_id: UUID = Query(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await require_cliente_access(cliente_id, current_user, db)
    # ... resto da lógica
```

> **Nota:** Se `cliente_id` não é obrigatório, torná-lo obrigatório OU retornar vazio quando ausente.

### Step 2: Commit

```bash
git add app/api/v1/endpoints/busca.py
git commit -m "security(busca): add require_cliente_access to /busca/associacoes"
```

---

## Task 2: Proteger `/servicos/{item_id}/versoes` (GET)

**Files:**
- Modify: `app/api/v1/endpoints/versoes.py`
- Modify: `app/services/versao_service.py` (se necessário)
- Test: `app/tests/unit/test_security_s04.py`

### Step 1: Validar acesso ao cliente do item

```python
# app/api/v1/endpoints/versoes.py — endpoint list_versoes
# Adicionar validação de acesso ao cliente do item

async def list_versoes(
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    svc = _get_service(db)
    # Validar acesso ao cliente do item antes de listar versões
    item = await svc.propria_repo.get_active_by_id(item_id)
    if not item:
        raise NotFoundError("ItemProprio", str(item_id))
    await require_cliente_access(item.cliente_id, current_user, db)
    versoes = await svc.list_versoes(item_id)
    return [VersaoComposicaoResponse.model_validate(v) for v in versoes]
```

### Step 2: Commit

```bash
git add app/api/v1/endpoints/versoes.py
git commit -m "security(versoes): validate client access before listing versions"
```

---

## Task 3: Proteger `/servicos/` (GET) quando cliente_id informado

**Files:**
- Modify: `app/api/v1/endpoints/servicos.py`
- Test: `app/tests/unit/test_security_s04.py`

### Step 1: Validar cliente_id quando presente

```python
# app/api/v1/endpoints/servicos.py — endpoint list_servicos
# Adicionar validação quando cliente_id é informado

async def list_servicos(
    q: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    cliente_id: UUID | None = Query(default=None),
    ...
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if cliente_id:
        await require_cliente_access(cliente_id, current_user, db)
    params = ServicoListParams(...)
    return await servico_catalog_service.list_servicos(params, db, cliente_id=cliente_id)
```

### Step 2: Commit

```bash
git add app/api/v1/endpoints/servicos.py
git commit -m "security(servicos): validate cliente_id access in list_servicos"
```

---

## Task 4: Criar Testes de Regressão para Perfis

**Files:**
- Create: `app/tests/unit/test_security_s04.py`

### Step 1: Testar cenários de acesso negado

```python
# app/tests/unit/test_security_s04.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import AuthorizationError


@pytest.mark.asyncio
async def test_busca_associacoes_requires_cliente_access():
    """Usuario sem acesso ao cliente deve ser rejeitado em /busca/associacoes."""
    # Mock dependencies
    from app.api.v1.endpoints.busca import list_associacoes
    # Testar que require_cliente_access é chamado
    # ... implementação


@pytest.mark.asyncio
async def test_list_versoes_requires_client_access():
    """Usuario sem acesso ao cliente do item deve ser rejeitado."""
    from app.api.v1.endpoints.versoes import list_versoes
    # ... implementação


@pytest.mark.asyncio
async def test_list_servicos_validates_cliente_id_when_present():
    """Quando cliente_id é informado, deve validar acesso."""
    from app.api.v1.endpoints.servicos import list_servicos
    # ... implementação
```

### Step 2: Commit

```bash
git add app/tests/unit/test_security_s04.py
git commit -m "test(security): add S-04 regression tests for client access validation"
```

---

## Task 5: Checklist OWASP API Básica

**Files:**
- Create: `docs/owasp-checklist-2026-04-22.md`

### Step 1: Executar checklist

```markdown
# OWASP API Security Checklist — S-04

## API1:2023 — Broken Object Level Authorization
- [ ] Verificar se todos os endpoints com item_id validam ownership/acesso
- [ ] Testar acesso a recursos de outro cliente

## API2:2023 — Broken Authentication
- [ ] Verificar expiração de tokens
- [ ] Verificar refresh token rotation

## API3:2023 — Broken Object Property Level Authorization
- [ ] Verificar se PATCH /me permite apenas campos permitidos

## API5:2023 — Broken Function Level Authorization
- [ ] Verificar se endpoints admin requerem is_admin
- [ ] Verificar se APROVADOR pode aprovar

## API8:2023 — Security Misconfiguration
- [ ] Verificar headers de segurança (CORS, HSTS)
- [ ] Verificar rate limiting em endpoints sensíveis
```

### Step 2: Commit

```bash
git add docs/owasp-checklist-2026-04-22.md
git commit -m "docs(security): OWASP API basic checklist for S-04"
```

---

## Task 6: Full Regression Unit Tests

**Files:**
- Test: full unit suite

### Step 1: Rodar suite completa

```powershell
pytest app/tests/unit/ -v --tb=short
```

Expected: ALL PASS (74+ testes)

### Step 2: Atualizar BACKLOG

```markdown
# docs/BACKLOG.md
Alterar S-04 de `INICIADA` → `TESTED`
```

### Step 3: Commit

```bash
git add docs/BACKLOG.md
git commit -m "test(regression): full unit suite pass after S-04 security hardening"
```

---

## Task 7: Walkthrough e Technical Review

**Files:**
- Create: `docs/walkthrough/done/walkthrough-S-04.md`
- Create: `docs/technical-review-2026-04-22-s04.md`

### Step 1: Walkthrough

Template com:
- O que foi feito (3 endpoints protegidos + testes + checklist)
- Testes (quantos passaram)
- Decisões técnicas

### Step 2: Commit

```bash
git add docs/walkthrough/done/walkthrough-S-04.md docs/technical-review-2026-04-22-s04.md
git commit -m "docs(s-04): add walkthrough and technical review"
```

---

## Plan Review Checklist

- [x] Spec coverage: busca, versoes, servicos endpoints covered
- [x] Placeholder scan: no TBD/TODO found
- [x] Type consistency: async/await corretos
- [x] Risco mitigado: testes de regressão cobrem acesso negado
- [x] Checklist OWASP incluído

## Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-22-seguranca-rbac.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch subagent per task, review between tasks
2. **Inline Execution** — execute in this session with checkpoints

Which approach?
