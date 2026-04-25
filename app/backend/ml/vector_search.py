"""
Vector search module.
Delegates the actual query to TcpoEmbeddingsRepository.
This module provides the interface contract consumed by busca_service.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class VectorSearcher:
    """
    Stateless vector searcher.
    Wraps repository call for cosine similarity search via pgvector.
    """

    async def search(
        self,
        query_vector: list[float],
        db: AsyncSession,
        threshold: float | None = None,
        limit: int = 10,
    ) -> list[tuple[UUID, float, dict]]:
        """
        Returns list of (servico_id, cosine_similarity, metadata).
        Uses pgvector HNSW index via <=> operator.
        """
        from backend.repositories.tcpo_embeddings_repository import TcpoEmbeddingsRepository

        t = threshold or settings.SEMANTIC_THRESHOLD
        repo = TcpoEmbeddingsRepository(db)

        results = await repo.vector_search(
            query_vector=query_vector,
            threshold=t,
            limit=limit,
        )

        logger.debug(
            "vector_search_completed",
            candidates=len(results),
            threshold=t,
        )
        return results


# Application-level singleton
vector_searcher = VectorSearcher()

