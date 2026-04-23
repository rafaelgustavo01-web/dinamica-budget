# Walkthrough — S-09 Entidades e CRUD de Propostas

## Status

`TESTED`

## What Changed

- Added new budget-module enums in `app/models/enums.py`.
- Added proposal-domain models in `app/models/proposta.py`.
- Added `PropostaRepository` and `PqItemRepository`.
- Added `PropostaService` with create, list, detail, status-transition support, metadata update, and soft delete paths.
- Added `/propostas` endpoints in `app/api/v1/endpoints/propostas.py` and wired them in `app/api/v1/router.py`.
- Added migration `alembic/versions/017_create_proposta_entities.py`.
- Added unit regression file `app/tests/unit/test_proposta_service.py`.

## Acceptance Criteria

- Tabelas criadas via Alembic: done.
- CRUD de proposta funcional: covered by service tests and endpoint wiring.
- Isolamento por cliente: covered by service validation plus endpoint `require_cliente_access`.
- Modelagem alinhada com `MODELAGEM_ORCAMENTOS_FASE2.md`: implemented for the five core entities in schema `operacional`.

## Verification

- `pytest app/tests/unit/test_proposta_service.py -q` -> `5 passed`
- `pytest app/tests/unit -q` -> `85 passed`
- `alembic upgrade head` -> success
- `alembic current` -> `017 (head)`

## Notes For QA

- Focus review on tenant isolation, proposal soft delete behavior, and migration shape.
- This sprint does not yet cover PQ import flow or CPU generation behavior; those remain backlog items in S-10 and S-11.
