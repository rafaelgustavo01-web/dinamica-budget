# Sprint Briefing - S-01 - Align Authorization to On-Premise Model

> Date: 2026-04-22
> Prepared by: Supervisor (Kimi Code CLI)
> Assigned role: Worker
> Assigned worker: TBD (Scrum Master will assign)
> Execution mode: BUILD
> Plan: `docs/sprints/S-01/plans/2026-04-22-align-authorization-onpremise-model.md`

## Mission

The Dinamica Budget system runs on-premise inside an engineering firm's Windows Server. In this environment, an orçamentista (estimator) needs to read data from ALL clients to prepare budgets — the `cliente_id` is a budget linkage, not a security tenant. However, the current API layer incorrectly applies `require_cliente_access` on GET endpoints as if the system were multi-tenant. This blocks users from viewing PROPRIA items and associations belonging to clients where they have no explicit `UsuarioPerfil` record.

This sprint removes read-level client barriers while preserving write-level RBAC. Any authenticated user must be able to read services, compositions, versions, search results, and associations. Only APROVADOR or ADMIN profiles on a specific client may create, approve, clone, or edit items for that client.

## Delegation Envelope

- Sprint status on entry: `PLAN`
- Worker status target on exit: `TESTED`
- Assigned worker: TBD
- Provider: TBD
- Auth status snapshot: UNKNOWN
- Quota status snapshot: UNKNOWN
- Execution mode: BUILD

## Current Code State

### `app/api/v1/endpoints/servicos.py`
- Line 43-64: `get_servico` raises `NotFoundError` for PROPRIA items when caller has no RBAC link to the item's `cliente_id`. Must be opened.
- Line 26-40: `list_servicos` calls `require_cliente_access` when `cliente_id` query param is present. Must be opened.
- Line 67-73: `explode_composicao` is already open (only requires `get_current_active_user`). No change needed.
- Risk note: `servico_catalog_service.get_servico` and `list_servicos` must remain untouched; changes are API-layer only.

### `app/api/v1/endpoints/versoes.py`
- Line 33-55: `list_versoes` calls `require_cliente_access(item.cliente_id, ...)`. Must be opened.
- Line 58-119: `criar_versao` correctly requires `require_cliente_perfil(APROVADOR/ADMIN)`. Keep protected.
- Line 122-163: `ativar_versao` correctly requires `require_cliente_perfil(APROVADOR/ADMIN)`. Keep protected.
- Risk note: Do not accidentally remove protection from `criar_versao` or `ativar_versao`.

### `app/api/v1/endpoints/busca.py`
- Line 23-35: `buscar_servicos` calls `require_cliente_access` when `request.cliente_id` is present. Must be opened.
- Line 52-79: `list_associacoes` calls `require_cliente_access`. Must be opened.
- Line 82-109: `delete_associacao` correctly requires `require_cliente_perfil(APROVADOR/ADMIN)`. Keep protected.
- Risk note: `criar_associacao` (POST /busca/associar) currently validates `require_cliente_access`. This is a write-like action (creating an association). Keep protected for now; open-read is the priority.

### `app/backend/tests/unit/test_security_p0.py`
- Line 113-168: `test_get_servico_propria_blocks_wrong_tenant` enforces old multi-tenant behavior. Must be removed.
- Line 170-219: `test_get_servico_propria_allows_correct_tenant` enforces old multi-tenant behavior. Must be removed.
- Risk note: Replace with tests that assert 200 for any authenticated user reading any PROPRIA item.

### `app/backend/tests/integration/test_auth_access_control.py`
- Line 16-30: `test_create_usuario_unauthenticated_returns_401` is unaffected.
- Line 32-53: `test_create_usuario_short_password_returns_422` is unaffected.
- Risk note: Append a test proving open-read for PROPRIA items without client link.

## Required Changes

### Task 1.1 - Open `GET /servicos/{id}`
- File: `app/api/v1/endpoints/servicos.py`
- Change: Remove `_get_perfis_para_cliente` check from `get_servico`. Return the service for any authenticated user.
- Constraints: Do not change `servico_catalog_service.get_servico` logic. Do not alter `create_servico` (admin-only).

### Task 1.2 - Open `GET /servicos/`
- File: `app/api/v1/endpoints/servicos.py`
- Change: Remove `require_cliente_access` call from `list_servicos`. The `cliente_id` query parameter becomes a pure filter.
- Constraints: `servico_catalog_service.list_servicos` signature and behavior must not change.

### Task 1.3 - Open `GET /servicos/{id}/versoes`
- File: `app/api/v1/endpoints/versoes.py`
- Change: Remove `require_cliente_access` from `list_versoes`.
- Constraints: Keep `require_cliente_perfil` on `criar_versao` and `ativar_versao`.

### Task 1.4 - Open `POST /busca/servicos` and `GET /busca/associacoes`
- File: `app/api/v1/endpoints/busca.py`
- Change: Remove `require_cliente_access` from `buscar_servicos` and `list_associacoes`.
- Constraints: Keep `require_cliente_perfil` on `delete_associacao`. Keep `require_cliente_access` on `criar_associacao` (write-like action).

### Task 1.5 - Update Unit Tests
- File: `app/backend/tests/unit/test_security_p0.py`
- Change: Delete obsolete cross-tenant isolation tests. Add tests asserting open-read for `get_servico`, `list_servicos`, `list_versoes`, `buscar_servicos`, and `list_associacoes`.
- Constraints: Keep all existing tests that verify write protection, rate limiting, password length, and CORS.

### Task 1.6 - Add Integration Test
- File: `app/backend/tests/integration/test_auth_access_control.py`
- Change: Append test verifying that a user without a client link can read a PROPRIA service from that client (or at minimum, receives 404 for missing item rather than 403 for access denial).
- Constraints: Do not break existing integration tests.

### Task 1.7 - Verify Write Protection
- File: `app/backend/tests/unit/test_security_p0.py`
- Change: Add a sanity-check test scanning write endpoint source code to confirm `require_cliente_perfil` or `require_cliente_access` is still present.
- Constraints: Pure verification, no production code changes.

### Task 1.8 - Clean Unused Imports
- Files: `app/api/v1/endpoints/servicos.py`, `app/api/v1/endpoints/versoes.py`, `app/api/v1/endpoints/busca.py`
- Change: Remove `require_cliente_access` and `_get_perfis_para_cliente` from imports if no longer used in the file.
- Constraints: Do not remove imports still used by other endpoints in the same file.

## Mandatory Tests

- `app/backend/tests/unit/test_security_p0.py`: add 5 new tests, remove 2 obsolete tests
- `app/backend/tests/integration/test_auth_access_control.py`: append 1 integration test
- Validation commands:
```bash
pytest app/backend/tests/unit/test_security_p0.py -v
pytest app/backend/tests/integration/test_auth_access_control.py -v
pytest app/backend/tests/unit/test_busca_service.py -v
```

## Required Artifacts Before Status `TESTED`

- `docs/sprints/S-05/technical-review/technical-review-2026-04-22.md` updated
- `docs/sprints/S-01/walkthrough/done/walkthrough-S-01.md` written
- `docs/BACKLOG.md` updated from `TODO` to `TESTED`

## Critical Warnings

1. Use incremental edits. Do not rewrite full files unless the plan explicitly requires it.
2. Do not change sprint status out of order.
3. Do not mark the sprint `DONE`.
4. If blocked, record the blocker in the walkthrough and leave the status unchanged.
5. Double-check that NO POST/PATCH/DELETE endpoint is accidentally opened. The business rule is: read = open, write = protected by APROVADOR/ADMIN per client.



