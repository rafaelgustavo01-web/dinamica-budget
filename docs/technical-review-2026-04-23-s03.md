# Technical Review — S-03 Revisao Transacional

## Status

`TESTED`

## Scope

- Confirmed request-scoped transaction boundary in `app/core/database.py`.
- Documented the service-level rule: use `flush()` inside request work; leave durable `commit()`/`rollback()` to the dependency.
- Added regression coverage for transaction commit/rollback behavior, session factory configuration, read purity, and service `flush()` usage.
- Reviewed target services: `AuthService`, `VersaoService`, and `ServicoCatalogService`.

## Findings

- `async_session_factory` already had `autocommit=False` and `autoflush=False`.
- `VersaoService` and `ServicoCatalogService` already used `flush()` in write paths and did not require behavior refactor.
- `AuthService` writes through `UsuarioRepository`, which already flushes token/profile/password updates without service-level commits.
- GET/read paths reviewed for this sprint do not perform synchronous mutations.

## Verification

- `pytest app/tests/unit/test_transactional_purity.py -q` -> `6 passed`
- `pytest app/tests/unit -q` -> `80 passed`

## Blocked External Check

- `pytest app/tests/integration/test_auth_access_control.py -q` failed during fixture setup because local `dinamica_budget_test` connection closed mid-operation via `asyncpg.exceptions.ConnectionDoesNotExistError`.
- No S-03 assertion executed before the environment failure.

## Residual Risk

- Integration rollback coverage still depends on a healthy local test database.
- Explicit commits remain valid in owned transaction boundaries such as startup seed and long-running ETL/background-style flows.
