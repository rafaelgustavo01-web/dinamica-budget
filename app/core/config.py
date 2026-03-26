from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Keys that must never reach production
_INSECURE_SECRET_KEYS: set[str] = {
    "CHANGE_ME_use_secrets_token_hex_32",
    "secret",
    "changeme",
    "change_me",
    "insecure",
    "",
}
_MIN_SECRET_KEY_LEN = 32


def validate_startup_config(secret_key: str) -> None:
    """
    Raises ValueError if the SECRET_KEY is insecure (default, empty, or too short).
    Called once in the FastAPI lifespan startup.
    """
    if (
        not secret_key
        or secret_key.strip() in _INSECURE_SECRET_KEYS
        or len(secret_key.strip()) < _MIN_SECRET_KEY_LEN
    ):
        raise ValueError(
            "SECRET_KEY insegura detectada no startup. "
            "Defina SECRET_KEY no .env com pelo menos 32 caracteres aleatórios. "
            "Gere com: python -c \"import secrets; print(secrets.token_hex(32))\""
        )


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/dinamica_budget"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT
    SECRET_KEY: str = "CHANGE_ME_use_secrets_token_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ML
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SENTENCE_TRANSFORMERS_HOME: str = "./ml_models"
    FUZZY_THRESHOLD: float = 0.85
    SEMANTIC_THRESHOLD: float = 0.65

    # App
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # CORS — configurable list of allowed origins for intranet/on-premise deploy
    # In .env: ALLOWED_ORIGINS=["http://app.intranet.local","http://localhost:3000"]
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins. Set via ALLOWED_ORIGINS env var (JSON array).",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
