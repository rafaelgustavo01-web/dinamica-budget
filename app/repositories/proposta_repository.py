from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposta import Proposta
from app.repositories.base_repository import BaseRepository


class PropostaRepository(BaseRepository[Proposta]):
    model = Proposta

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_id(self, id: UUID) -> Proposta | None:  # type: ignore[override]
        result = await self.db.execute(
            select(Proposta).where(
                Proposta.id == id,
                Proposta.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_cliente(
        self,
        cliente_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Proposta], int]:
        filters = (
            Proposta.cliente_id == cliente_id,
            Proposta.deleted_at.is_(None),
        )
        total = await self.count(*filters)
        result = await self.db.execute(
            select(Proposta)
            .where(*filters)
            .order_by(Proposta.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def count_by_code_prefix(self, prefix: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Proposta).where(Proposta.codigo.like(f"{prefix}%"))
        )
        return result.scalar_one()

    async def soft_delete(self, proposta: Proposta) -> None:
        proposta.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
