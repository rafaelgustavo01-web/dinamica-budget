from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.proposta import PropostaResumoRecurso
from backend.repositories.base_repository import BaseRepository

class PropostaResumoRecursoRepository(BaseRepository[PropostaResumoRecurso]):
    model = PropostaResumoRecurso

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaResumoRecurso]:
        result = await self.db.execute(
            select(PropostaResumoRecurso)
            .where(PropostaResumoRecurso.proposta_id == proposta_id)
            .order_by(PropostaResumoRecurso.tipo_recurso.asc())
        )
        return list(result.scalars().all())

    async def delete_by_proposta(self, proposta_id: UUID) -> None:
        await self.db.execute(
            delete(PropostaResumoRecurso).where(PropostaResumoRecurso.proposta_id == proposta_id)
        )

    async def create_batch(self, items: list[PropostaResumoRecurso]) -> list[PropostaResumoRecurso]:
        self.db.add_all(items)
        await self.db.flush()
        return items
