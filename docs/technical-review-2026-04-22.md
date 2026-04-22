# Technical Review - 2026-04-22 - Sprint S-01

## Scope Reviewed

- Authorization model alignment for on-premise operation
- API read access behavior for services, versions, and search associations
- Preservation of write RBAC guards
- Required regression tests for sprint acceptance

## Findings

- Read endpoints were aligned to on-premise policy:
  - `GET /servicos/`
  - `GET /servicos/{id}`
  - `GET /servicos/{id}/versoes`
  - `POST /busca/servicos`
  - `GET /busca/associacoes`
- Write endpoints remain protected by `require_cliente_perfil` or `require_cliente_access` where applicable.
- Merge conflicts that blocked app bootstrap were resolved in:
  - `app/api/v1/router.py`
  - `app/api/v1/endpoints/admin.py`
- Test infrastructure was stabilized for integration execution in this environment:
  - `app/tests/conftest.py` now uses `NullPool`.
  - Removed custom `event_loop` fixture causing asyncpg instability.

## Validation Evidence

- `pytest app/tests/unit/test_security_p0.py -v` -> 22 passed
- `pytest app/tests/integration/test_auth_access_control.py -v` -> 7 passed
- `pytest app/tests/unit/test_busca_service.py -v` -> 8 passed

## Risks / Notes

- Integration suite emits SQLAlchemy relationship overlap warnings (non-blocking). Suggested follow-up: explicit `back_populates` or `overlaps` on affected relationships.
- `openpyxl` was required in local environment to import ETL service endpoints.

## Conclusion

Sprint S-01 is technically consistent with the on-premise authorization model and validated as `TESTED`.
