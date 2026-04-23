# Transaction Strategy

## Boundary

Database transactions are scoped to a FastAPI request through `get_db_session` in `app/core/database.py`.

- `commit()` happens once after a request dependency completes successfully.
- `rollback()` happens when an exception is raised before the dependency completes.
- Services and repositories should not commit normal request work directly.

## Service Pattern

Use `await db.flush()` when code needs database-generated values, relationship consistency, or constraint validation before the request finishes. This keeps multi-step operations atomic while still surfacing database errors early.

Use explicit `commit()` only for code that owns its own transaction boundary outside the request dependency, such as startup seed jobs, long-running ETL jobs, or background tasks.

## Read Purity

GET/read paths must not mutate state synchronously. If future product requirements need read analytics, last-access timestamps, or audit side effects, implement them outside the request transaction through an explicit async/background mechanism.

## Rollback Rule

If a service performs multiple writes and a later step fails, the request dependency rolls back all flushed changes. A `flush()` is not durable until the request-level commit succeeds.
