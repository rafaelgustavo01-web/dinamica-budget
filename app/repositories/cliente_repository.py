import uuid as uuid_module
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cliente import Cliente
from app.repositories.base_repository import BaseRepository


class ClienteRepository(BaseRepository[Cliente]):
    model = Cliente

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_cnpj(self, cnpj: str) -> Cliente | None:
        result = await self.db.execute(
            select(Cliente).where(Cliente.cnpj == cnpj)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> Cliente | None:  # type: ignore[override]
        result = await self.db.execute(select(Cliente).where(Cliente.id == id))
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        offset: int,
        limit: int,
        is_active: bool | None = None,
    ) -> tuple[list[Cliente], int]:
        filters = []
        if is_active is not None:
            filters.append(Cliente.is_active == is_active)

        count_result = await self.db.execute(
            select(func.count()).select_from(Cliente).where(*filters)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(Cliente)
            .where(*filters)
            .order_by(Cliente.nome_fantasia)
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def create_cliente(self, nome_fantasia: str, cnpj: str) -> Cliente:
        cliente = Cliente(
            id=uuid_module.uuid4(),
            nome_fantasia=nome_fantasia,
            cnpj=cnpj,
        )
        self.db.add(cliente)
        await self.db.flush()
        await self.db.refresh(cliente)
        return cliente
