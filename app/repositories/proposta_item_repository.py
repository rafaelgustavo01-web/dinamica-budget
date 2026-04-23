from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposta import PropostaItem
from app.repositories.base_repository import BaseRepository


class PropostaItemRepository(BaseRepository[PropostaItem]):
    model = PropostaItem

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_id(self, id: UUID) -> PropostaItem | None:  # type: ignore[override]
        result = await self.db.execute(select(PropostaItem).where(PropostaItem.id == id))
        return result.scalar_one_or_none()

    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaItem]:
        result = await self.db.execute(
            select(PropostaItem)
            .where(PropostaItem.proposta_id == proposta_id)
            .order_by(PropostaItem.ordem.asc(), PropostaItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_batch(self, items: list[PropostaItem]) -> list[PropostaItem]:
        self.db.add_all(items)
        await self.db.flush()
        return items

    async def delete_by_proposta(self, proposta_id: UUID) -> None:
        await self.db.execute(delete(PropostaItem).where(PropostaItem.proposta_id == proposta_id))
