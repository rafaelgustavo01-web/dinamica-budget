import os

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class Embedder:
    """
    Singleton wrapper around SentenceTransformer.
    Loaded once at FastAPI startup via lifespan context.
    Stateless for inference — safe for concurrent reads.
    """

    def __init__(self) -> None:
        self._model = None
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def load(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer

        name = model_name or settings.EMBEDDING_MODEL_NAME
        cache_dir = settings.SENTENCE_TRANSFORMERS_HOME

        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", cache_dir)

        logger.info("loading_embedding_model", model=name, cache_dir=cache_dir)
        self._model = SentenceTransformer(name, cache_folder=cache_dir)
        self._ready = True
        logger.info("embedding_model_loaded", model=name)

    def encode(self, text: str) -> list[float]:
        if not self._ready or self._model is None:
            raise RuntimeError("Embedder não inicializado. Chame load() primeiro.")
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def encode_batch(
        self, texts: list[str], batch_size: int = 64
    ) -> list[list[float]]:
        if not self._ready or self._model is None:
            raise RuntimeError("Embedder não inicializado. Chame load() primeiro.")
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return [v.tolist() for v in vectors]


# Application-level singleton — load() deferred to FastAPI lifespan
embedder = Embedder()

