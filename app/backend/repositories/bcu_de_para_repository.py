"""Repository for BCU De/Para mapping."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bcu import DeParaTcpoBcu, BcuTableType


class BcuDeParaRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, de_para_id: UUID) -> DeParaTcpoBcu | None:
        result = await self.db.execute(select(DeParaTcpoBcu).where(DeParaTcpoBcu.id == de_para_id))
        return result.scalar_one_or_none()

    async def get_by_base_tcpo_id(self, base_tcpo_id: UUID) -> DeParaTcpoBcu | None:
        result = await self.db.execute(
            select(DeParaTcpoBcu).where(DeParaTcpoBcu.base_tcpo_id == base_tcpo_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[DeParaTcpoBcu]:
        result = await self.db.execute(select(DeParaTcpoBcu).order_by(DeParaTcpoBcu.criado_em.desc()))
        return list(result.scalars().all())

    async def create(self, de_para: DeParaTcpoBcu) -> DeParaTcpoBcu:
        self.db.add(de_para)
        await self.db.flush()
        await self.db.refresh(de_para)
        return de_para

    async def delete(self, de_para: DeParaTcpoBcu) -> None:
        await self.db.delete(de_para)
        await self.db.flush()
