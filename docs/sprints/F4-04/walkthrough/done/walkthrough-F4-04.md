# Walkthrough — F4-04 Cadastro de Clientes para Folha PC

## Delivered
- Added optional Folha PC client fields to `Cliente` ORM model.
- Added migration `027_cliente_campos_folha_pc.py` with reversible nullable-column upgrade/downgrade.
- Updated Pydantic schemas for create, patch, and response.
- Updated cliente endpoint/repository flow to persist and return the new fields.
- Updated Excel export to append available client metadata without moving existing cells.
- Updated shared TypeScript client contract.
- Added backend unit tests for field validation and endpoint-to-repository payload handling.

## Files Changed
- `app/backend/models/cliente.py`
- `app/backend/schemas/cliente.py`
- `app/backend/repositories/cliente_repository.py`
- `app/backend/api/v1/endpoints/clientes.py`
- `app/backend/services/proposta_export_service.py`
- `app/alembic/versions/027_cliente_campos_folha_pc.py`
- `app/backend/tests/unit/test_cliente_pc_fields.py`
- `app/backend/tests/unit/test_proposta_export_service.py`
- `app/frontend/src/shared/types/contracts/clientes.ts`

## Validation
- `git diff --check`: PASS.
- `python3 -m compileall app/backend/models/cliente.py app/backend/schemas/cliente.py app/backend/repositories/cliente_repository.py app/backend/api/v1/endpoints/clientes.py app/backend/services/proposta_export_service.py app/backend/tests/unit/test_cliente_pc_fields.py app/backend/tests/unit/test_proposta_export_service.py app/alembic/versions/027_cliente_campos_folha_pc.py`: PASS.
- `python3 -m pytest app/backend/tests/unit/test_cliente_pc_fields.py app/backend/tests/unit/test_proposta_export_service.py app/backend/tests/unit/test_governance_routes.py -q`: BLOCKED, `pytest` is not installed.
- Local install attempt for test dependencies: BLOCKED by network/DNS when resolving PyPI.

## QA Notes
- Review migration safety first: it is schema-only, additive, nullable, and has a direct downgrade.
- Confirm frontend worker wires the new contract into the Clientes form before claiming full UI acceptance.
- Export compatibility check: existing Excel `Capa` positions used by current tests remain unchanged.
