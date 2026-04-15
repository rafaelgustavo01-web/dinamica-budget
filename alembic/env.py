import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings

config = context.config

# Use synchronous psycopg2 driver for migrations.
# asyncpg (the runtime driver) causes DO-block exceptions to propagate past
# PL/pgSQL EXCEPTION handlers; psycopg2 handles them correctly.
_sync_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://", 1
).replace(
    "postgresql+asyncio://", "postgresql+psycopg2://", 1
)
config.set_main_option("sqlalchemy.url", _sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Model imports (autogenerate only) ────────────────────────────────────────
# During `alembic upgrade`, importing ORM models registers SAEnum DDL event
# listeners that fire when op.create_table() is called. Those listeners issue
# raw CREATE TYPE statements that race with (and duplicate) the explicit
# CREATE TYPE calls already present in each migration script.
#
# ORM metadata is only required for `alembic revision --autogenerate`.
# Set ALEMBIC_AUTOGENERATE=1 in your shell before running autogenerate:
#
#   ALEMBIC_AUTOGENERATE=1 alembic revision --autogenerate -m "describe change"
#
if os.environ.get("ALEMBIC_AUTOGENERATE", "").lower() in ("1", "true", "yes"):
    from app.models import Base  # noqa: F401
    from app.models import *  # noqa: F401, F403
    target_metadata = Base.metadata
else:
    # Empty metadata — sufficient for upgrade/downgrade; no DDL events registered.
    target_metadata = MetaData()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    # Use synchronous engine (psycopg2) so PL/pgSQL EXCEPTION blocks work correctly
    from sqlalchemy import engine_from_config  # noqa: PLC0415

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
