# Technical Review — S-09 Entidades e CRUD de Propostas

## Status

`TESTED`

## Scope

- Added operational enums for proposal lifecycle and PQ matching in `app/models/enums.py`.
- Added SQLAlchemy 2.0 models for `operacional.propostas`, `operacional.pq_importacoes`, `operacional.pq_itens`, `operacional.proposta_itens`, and `operacional.proposta_item_composicoes`.
- Added repository and service layers for proposal CRUD and tenant-safe reads.
- Added `/propostas` API endpoints and wired the router.
- Added Alembic migration `017_create_proposta_entities`.
- Added unit coverage for proposal service behavior and tenant isolation.

## Findings

- The new proposal flow follows the existing endpoint -> service -> repository pattern introduced in S-02.
- Cross-client access remains enforced at the endpoint boundary through `require_cliente_access`.
- Soft delete is implemented via `deleted_at` and repository filtering.
- The initial endpoint implementation needed cleanup for detail/update/delete lookups; this was normalized by adding `PropostaService.obter_por_id()` and reusing it before authorization checks.
- The migration needed explicit PostgreSQL enum definitions in table columns to make `upgrade head` deterministic.

## Verification

- `pytest app/backend/tests/unit/test_proposta_service.py -q` -> `5 passed`
- `pytest app/backend/tests/unit -q` -> `85 passed`
- `python -m compileall app/api/v1/endpoints/propostas.py app/services/proposta_service.py app/alembic/versions/017_create_proposta_entities.py app/models/proposta.py app/schemas/proposta.py`
- `alembic heads` -> `017 (head)`
- `alembic upgrade head` -> success
- `alembic current` -> `017 (head)`

## Residual Risk

- S-09 delivered the CRUD foundation only; PQ import, matching, and CPU generation remain intentionally deferred to S-10/S-11.
- No endpoint integration suite was added in this sprint; current coverage is service-layer plus migration execution.

