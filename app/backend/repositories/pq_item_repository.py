from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.enums import StatusMatch, TipoServicoMatch
from backend.models.proposta import PqItem
from backend.repositories.base_repository import BaseRepository


class PqItemRepository(BaseRepository[PqItem]):
    model = PqItem

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_id(self, id: UUID) -> PqItem | None:  # type: ignore[override]
        result = await self.db.execute(select(PqItem).where(PqItem.id == id))
        return result.scalar_one_or_none()

    async def create_batch(self, items: list[PqItem]) -> list[PqItem]:
        self.db.add_all(items)
        await self.db.flush()
        return items

    async def list_by_proposta(
        self,
        proposta_id: UUID,
        status_match: StatusMatch | None = None,
        limit: int | None = None,
    ) -> list[PqItem]:
        stmt = (
            select(PqItem)
            .where(PqItem.proposta_id == proposta_id)
            .order_by(PqItem.linha_planilha.asc().nulls_last(), PqItem.created_at.asc())
        )
        if status_match is not None:
            stmt = stmt.where(PqItem.match_status == status_match)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_match(
        self,
        pq_item: PqItem,
        servico_match_id: UUID,
        servico_match_tipo: TipoServicoMatch,
        confidence: float,
    ) -> None:
        pq_item.servico_match_id = servico_match_id
        pq_item.servico_match_tipo = servico_match_tipo
        pq_item.match_confidence = confidence
        pq_item.match_status = StatusMatch.SUGERIDO
        await self.db.flush()

    async def update_status(self, pq_item: PqItem, status_match: StatusMatch) -> None:
        pq_item.match_status = status_match
        await self.db.flush()

