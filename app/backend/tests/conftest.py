import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import dotenv_values
from httpx import ASGITransport, AsyncClient

# asyncpg uses raw sockets that conflict with the Windows ProactorEventLoop
# (IOCP). Force SelectorEventLoop on Windows to avoid WinError 64 in batch runs.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.core.dependencies import get_db
from backend.models.base import Base

# Resolve test DB URL: prefer explicit TEST_DATABASE_URL env var, then derive
# from DATABASE_URL (env or .env file), falling back to a local default.
def _resolve_test_db_url() -> str:
    if url := os.environ.get("TEST_DATABASE_URL"):
        return url
    # Load .env from the app root (parent of backend/)
    env_path = Path(__file__).parent.parent.parent / ".env"
    dotenv = dotenv_values(env_path) if env_path.exists() else {}
    base = os.environ.get("DATABASE_URL") or dotenv.get("DATABASE_URL") or (
        "postgresql+asyncpg://postgres:password@localhost:5432/dinamica_budget"
    )
    return base.rsplit("/", 1)[0] + "/dinamica_budget_test"


TEST_DATABASE_URL = _resolve_test_db_url()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Engine created per-test so it shares the same event loop as pytest-asyncio.
    # A module-level engine would bind to a different loop and cause WinError 64
    # (connection reset) when tests run in batch on Windows.
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        from sqlalchemy import text

        # Ensure custom schemas exist; Alembic creates these in production
        # but the test DB may not have all migrations applied.
        for schema in ("bcu", "referencia", "operacional"):
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

        # Create Postgres ENUM types used by models (all defined with
        # create_type=False so SQLAlchemy won't auto-create them).
        # PostgreSQL has no CREATE TYPE IF NOT EXISTS; use DO block instead.
        _enum_ddl = [
            ("bcu_table_type_enum", "'MO','EQP','EPI','FER','MOB'"),
            ("campo_sistema_pq_enum", "'codigo','descricao','unidade','quantidade','observacao'"),
            ("origem_associacao_enum", "'MANUAL_USUARIO','IA_CONSOLIDADA'"),
            ("proposta_papel_enum", "'OWNER','EDITOR','APROVADOR'"),
            ("status_homologacao_enum", "'PENDENTE','APROVADO','REPROVADO'"),
            ("status_importacao_enum", "'PROCESSANDO','VALIDADO','COM_ERROS','CONCLUIDO'"),
            ("status_match_enum", "'PENDENTE','BUSCANDO','SUGERIDO','CONFIRMADO','MANUAL','SEM_MATCH'"),
            ("status_proposta_enum", "'RASCUNHO','EM_ANALISE','CPU_GERADA','AGUARDANDO_APROVACAO','APROVADA','REPROVADA','ARQUIVADA'"),
            ("status_validacao_associacao_enum", "'SUGERIDA','VALIDADA','CONSOLIDADA'"),
            ("tipo_custo_enum", "'HORISTA','MENSALISTA','GLOBAL'"),
            ("tipo_operacao_auditoria_enum", "'CREATE','UPDATE','DELETE','APROVAR','REPROVAR'"),
            ("tipo_recurso_enum", "'MO','INSUMO','FERRAMENTA','EQUIPAMENTO','SERVICO'"),
            ("tipo_servico_match_enum", "'BASE_TCPO','ITEM_PROPRIO'"),
        ]
        for type_name, values in _enum_ddl:
            await conn.execute(text(
                f"DO $$ BEGIN "
                f"CREATE TYPE {type_name} AS ENUM ({values}); "
                f"EXCEPTION WHEN duplicate_object THEN NULL; "
                f"END $$"
            ))

        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def seed_user(db_session: AsyncSession):
    """Insert a minimal Usuario so FK constraints on criado_por_id are satisfied.

    Returns the UUID of the created user. Use this fixture in any test that
    passes a user-id to a service that stores it under a FK column.
    """
    import uuid as _uuid
    from backend.core.security import hash_password
    from backend.models.usuario import Usuario

    user = Usuario(
        id=_uuid.uuid4(),
        nome="Seed Test User",
        email=f"seed-{_uuid.uuid4().hex[:8]}@test.invalid",
        hashed_password=hash_password("testpass123!"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user.id


@pytest.fixture
def token_factory():
    """Return a callable: token_factory(user_id: str) -> JWT access token string."""
    from backend.core.security import create_access_token
    return lambda user_id: create_access_token(user_id)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from backend.main import create_app

    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
