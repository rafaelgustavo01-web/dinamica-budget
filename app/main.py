from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.exceptions import DinamicaException, dinamica_exception_handler
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("startup_begin")

    # 0. Security: reject insecure SECRET_KEY before anything else starts
    from app.core.config import validate_startup_config
    validate_startup_config(settings.SECRET_KEY)

    # 1. Register SQLAlchemy audit hooks (price + homologacao status changes)
    from app.core.audit_hooks import register_audit_hooks
    register_audit_hooks()

    # 2. Load embedding model (blocks until ready — ~2-5s on first run)
    from app.ml.embedder import embedder

    try:
        embedder.load(settings.EMBEDDING_MODEL_NAME)
    except Exception as exc:
        logger.error("embedding_model_load_failed", error=str(exc))
        # Non-fatal: semantic search will be unavailable but app still starts

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
    from app.api.v1.router import router as v1_router

    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    # Health check
    @app.get("/health", tags=["health"])
    async def health() -> dict:
        from app.ml.embedder import embedder

        return {
            "status": "ok",
            "embedder_ready": embedder.ready,
        }

    return app


app = create_app()
