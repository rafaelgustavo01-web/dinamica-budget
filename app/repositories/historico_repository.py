import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.historico_busca_cliente import HistoricoBuscaCliente
from app.repositories.base_repository import BaseRepository


class HistoricoRepository(BaseRepository[HistoricoBuscaCliente]):
    model = HistoricoBuscaCliente

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def create_registro(
        self,
        cliente_id: UUID | None,
        usuario_id: UUID,
        texto_busca: str,
    ) -> HistoricoBuscaCliente:
        registro = HistoricoBuscaCliente(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            texto_busca=texto_busca,
        )
        self.db.add(registro)
        await self.db.flush()
        await self.db.refresh(registro)
        return registro

    async def get_by_id(self, id: UUID) -> HistoricoBuscaCliente | None:  # type: ignore[override]
        result = await self.db.execute(
            select(HistoricoBuscaCliente).where(HistoricoBuscaCliente.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_cliente(
        self, id: UUID, cliente_id: UUID
    ) -> HistoricoBuscaCliente | None:
        """Fetch historico validating it belongs to the given client."""
        result = await self.db.execute(
            select(HistoricoBuscaCliente).where(
                HistoricoBuscaCliente.id == id,
                HistoricoBuscaCliente.cliente_id == cliente_id,
            )
        )
        return result.scalar_one_or_none()
