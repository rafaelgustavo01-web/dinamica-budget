from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.pq_layout import PqLayoutCliente


class PqLayoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_cliente_id(self, cliente_id: UUID) -> PqLayoutCliente | None:
        result = await self._db.execute(
            select(PqLayoutCliente)
            .options(selectinload(PqLayoutCliente.mapeamentos))
            .where(PqLayoutCliente.cliente_id == cliente_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, layout_id: UUID) -> PqLayoutCliente | None:
        result = await self._db.execute(
            select(PqLayoutCliente)
            .options(selectinload(PqLayoutCliente.mapeamentos))
            .where(PqLayoutCliente.id == layout_id)
        )
        return result.scalar_one_or_none()

    async def create(self, layout: PqLayoutCliente) -> PqLayoutCliente:
        self._db.add(layout)
        await self._db.flush()
        return layout

    async def delete_by_cliente_id(self, cliente_id: UUID) -> None:
        await self._db.execute(
            delete(PqLayoutCliente).where(PqLayoutCliente.cliente_id == cliente_id)
        )
