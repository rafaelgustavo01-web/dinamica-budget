from uuid import UUID

from collections import defaultdict
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.proposta import PropostaItemComposicao
from backend.repositories.base_repository import BaseRepository


class PropostaItemComposicaoRepository(BaseRepository[PropostaItemComposicao]):
    model = PropostaItemComposicao

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def list_by_proposta_item(self, proposta_item_id: UUID) -> list[PropostaItemComposicao]:
        result = await self.db.execute(
            select(PropostaItemComposicao)
            .where(PropostaItemComposicao.proposta_item_id == proposta_item_id)
            .order_by(PropostaItemComposicao.nivel.asc())
        )
        return list(result.scalars().all())

    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaItemComposicao]:
        from backend.models.proposta import PropostaItem
        result = await self.db.execute(
            select(PropostaItemComposicao)
            .join(PropostaItem, PropostaItem.id == PropostaItemComposicao.proposta_item_id)
            .where(PropostaItem.proposta_id == proposta_id)
        )
        return list(result.scalars().all())

    async def list_by_proposta_items_batch(
        self, proposta_id: UUID
    ) -> dict[UUID, list[PropostaItemComposicao]]:
        from backend.models.proposta import PropostaItem

        result = await self.db.execute(
            select(PropostaItemComposicao)
            .join(PropostaItem, PropostaItem.id == PropostaItemComposicao.proposta_item_id)
            .where(PropostaItem.proposta_id == proposta_id)
            .order_by(PropostaItemComposicao.proposta_item_id, PropostaItemComposicao.nivel.asc())
        )
        grouped: dict[UUID, list[PropostaItemComposicao]] = defaultdict(list)
        for composicao in result.scalars().all():
            grouped[composicao.proposta_item_id].append(composicao)
        return dict(grouped)

    async def create_batch(self, items: list[PropostaItemComposicao]) -> list[PropostaItemComposicao]:
        self.db.add_all(items)
        await self.db.flush()
        return items

    async def delete_by_proposta_item(self, proposta_item_id: UUID) -> None:
        await self.db.execute(
            delete(PropostaItemComposicao).where(PropostaItemComposicao.proposta_item_id == proposta_item_id)
        )
