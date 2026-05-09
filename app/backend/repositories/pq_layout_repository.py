from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.pq_layout import PqLayoutCliente, PqLayoutHistorico


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

    async def aprovar(self, layout: PqLayoutCliente, usuario_id: UUID) -> None:
        layout.is_aprovado = True
        layout.aprovado_por_id = usuario_id
        layout.aprovado_em = datetime.now(timezone.utc)
        await self._db.flush()

    async def registrar_historico(self, entry: PqLayoutHistorico) -> PqLayoutHistorico:
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def list_historico_by_layout(self, layout_id: UUID) -> list[PqLayoutHistorico]:
        result = await self._db.execute(
            select(PqLayoutHistorico)
            .where(PqLayoutHistorico.layout_id == layout_id)
            .order_by(PqLayoutHistorico.created_at.desc())
        )
        return list(result.scalars().all())
