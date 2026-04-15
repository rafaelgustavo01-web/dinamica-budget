"""
Keeps tcpo_embeddings in sync with servico_tcpo.
Called by servico_catalog_service on every CREATE / UPDATE / soft DELETE.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.ml.embedder import embedder
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.repositories.tcpo_embeddings_repository import TcpoEmbeddingsRepository

logger = get_logger(__name__)


class EmbeddingSyncService:
    async def sync_create_or_update(
        self,
        servico_id: UUID,
        db: AsyncSession,
    ) -> None:
        """Encode the service description and upsert into tcpo_embeddings."""
        servico_repo = ServicoTcpoRepository(db)
        emb_repo = TcpoEmbeddingsRepository(db)

        servico = await servico_repo.get_active_by_id(servico_id)
        if not servico:
            logger.warning("sync_skipped_service_not_found", servico_id=str(servico_id))
            return

        if not embedder.ready:
            logger.warning("sync_skipped_embedder_not_ready", servico_id=str(servico_id))
            return

        vetor = embedder.encode(servico.descricao)
        metadata = {
            "descricao": servico.descricao,
            "categoria_id": servico.categoria_id,
        }

        await emb_repo.upsert(servico_id, vetor, metadata)
        logger.info("embedding_synced", servico_id=str(servico_id))

    async def sync_delete(self, servico_id: UUID, db: AsyncSession) -> None:
        """Remove embedding when service is soft-deleted."""
        emb_repo = TcpoEmbeddingsRepository(db)
        await emb_repo.delete_by_servico_id(servico_id)
        logger.info("embedding_deleted", servico_id=str(servico_id))

    async def compute_all_missing(
        self, db: AsyncSession, batch_size: int = 100
    ) -> int:
        """Batch-compute embeddings for all services without one."""
        servico_repo = ServicoTcpoRepository(db)
        emb_repo = TcpoEmbeddingsRepository(db)

        if not embedder.ready:
            raise RuntimeError("Embedder não está pronto.")

        total = 0
        while True:
            servicos = await servico_repo.get_without_embeddings(limit=batch_size)
            if not servicos:
                break

            texts = [s.descricao for s in servicos]
            vectors = embedder.encode_batch(texts)

            for servico, vetor in zip(servicos, vectors):
                metadata = {
                    "descricao": servico.descricao,
                    "categoria_id": servico.categoria_id,
                }
                await emb_repo.upsert(servico.id, vetor, metadata)
                total += 1

            logger.info("embedding_batch_done", count=total)

            if len(servicos) < batch_size:
                break

        return total


embedding_sync_service = EmbeddingSyncService()
