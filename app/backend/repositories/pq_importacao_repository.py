from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.proposta import PqImportacao
from backend.repositories.base_repository import BaseRepository


class PqImportacaoRepository(BaseRepository[PqImportacao]):
    model = PqImportacao

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_id(self, id: UUID) -> PqImportacao | None:  # type: ignore[override]
        result = await self.db.execute(select(PqImportacao).where(PqImportacao.id == id))
        return result.scalar_one_or_none()

