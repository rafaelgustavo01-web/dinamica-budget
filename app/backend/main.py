from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.exceptions import DinamicaException, dinamica_exception_handler
from backend.core.logging import configure_logging, get_logger
from backend.core.rate_limit import limiter

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("startup_begin")

    # 0. Security: reject insecure SECRET_KEY before anything else starts
    from backend.core.config import validate_startup_config
    validate_startup_config(settings.SECRET_KEY)

    # 1. Register SQLAlchemy audit hooks (price + homologacao status changes)
    from backend.core.audit_hooks import register_audit_hooks
    register_audit_hooks()

    # 2. Load embedding model (blocks until ready — ~2-5s on first run)
    from backend.ml.embedder import embedder

    try:
        embedder.load(settings.EMBEDDING_MODEL_NAME)
    except Exception as exc:
        logger.error("embedding_model_load_failed", error=str(exc))
        # Non-fatal: semantic search will be unavailable but app still starts

    # 3. Auto-create root user if configured and not already present
    if settings.ROOT_USER_EMAIL and settings.ROOT_USER_PASSWORD:
        from backend.core.database import async_session_factory
        from backend.core.security import hash_password
        from backend.models.usuario import Usuario
        from sqlalchemy import select
        import uuid as _uuid

        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Usuario).where(Usuario.email == settings.ROOT_USER_EMAIL.lower())
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    root = Usuario(
                        id=_uuid.uuid4(),
                        nome=settings.ROOT_USER_NAME,
                        email=settings.ROOT_USER_EMAIL.lower(),
                        hashed_password=hash_password(settings.ROOT_USER_PASSWORD),
                        is_admin=True,
                        is_active=True,
                    )
                    session.add(root)
                    await session.commit()
                    logger.info("root_user_created", email=settings.ROOT_USER_EMAIL)
                else:
                    logger.info("root_user_exists", email=settings.ROOT_USER_EMAIL)
        except Exception as exc:
            logger.error("root_user_seed_failed", error=str(exc))

    logger.info("startup_complete")
    yield

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dinamica Budget API",
        description="Motor de busca de serviços TCPO com associação direta, fuzzy e IA semântica.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS — configurable origin list; never allow wildcard in production
    # Set ALLOWED_ORIGINS in .env: ["http://app.intranet.local","http://localhost:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting (slowapi — in-memory, simple, no external infra required)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Exception handlers
    app.add_exception_handler(DinamicaException, dinamica_exception_handler)

    # Routers
    from backend.api.v1.router import router as v1_router

    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    # Health check
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        from backend.ml.embedder import embedder
        from backend.core.database import async_session_factory
        from sqlalchemy import text

        db_ok = False
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                db_ok = True
        except Exception:
            pass

        status = "ok" if db_ok else "degraded"
        return {
            "status": status,
            "embedder_ready": embedder.ready,
            "database_connected": db_ok,
        }

    # ── Serve frontend SPA (only if dist exists — e.g. Docker build) ─────────
    _frontend_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if _frontend_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_frontend_dir / "assets")), name="static-assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            file_path = _frontend_dir / full_path
            if full_path and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(_frontend_dir / "index.html"))

    return app


app = create_app()

