from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tcpo_embeddings import TcpoEmbedding
from app.repositories.base_repository import BaseRepository


class TcpoEmbeddingsRepository(BaseRepository[TcpoEmbedding]):
    model = TcpoEmbedding

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def upsert(
        self,
        servico_id: UUID,
        vetor: list[float],
        metadata: dict,
    ) -> TcpoEmbedding:
        existing = await self.db.get(TcpoEmbedding, servico_id)
        if existing:
            existing.vetor = vetor
            existing.embedding_metadata = metadata  # 'metadata' is reserved by SQLAlchemy
            await self.db.flush()
            return existing

        embedding = TcpoEmbedding(
            id=servico_id,
            vetor=vetor,
            embedding_metadata=metadata,  # ORM attribute renamed to embedding_metadata
        )
        self.db.add(embedding)
        await self.db.flush()
        return embedding

    async def delete_by_servico_id(self, servico_id: UUID) -> None:
        await self.db.execute(
            delete(TcpoEmbedding).where(TcpoEmbedding.id == servico_id)
        )
        await self.db.flush()

    async def vector_search(
        self,
        query_vector: list[float],
        threshold: float,
        limit: int,
    ) -> list[tuple[UUID, float, dict]]:
        """
        Cosine similarity search using pgvector <=> operator.
        Returns list of (servico_id, similarity_score, metadata).
        """
        stmt = text(
            """
            SELECT id,
                   1 - (vetor <=> CAST(:query_vec AS vector)) AS cosine_sim,
                   embedding_metadata
            FROM referencia.tcpo_embeddings
            WHERE vetor IS NOT NULL
              AND 1 - (vetor <=> CAST(:query_vec AS vector)) >= :threshold
            ORDER BY cosine_sim DESC
            LIMIT :limit
            """
        )
        import json

        query_vec_str = "[" + ",".join(str(v) for v in query_vector) + "]"
        result = await self.db.execute(
            stmt,
            {"query_vec": query_vec_str, "threshold": threshold, "limit": limit},
        )
        rows = result.fetchall()
        return [(row[0], float(row[1]), row[2] or {}) for row in rows]
