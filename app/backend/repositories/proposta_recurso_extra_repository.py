"""Repository for per-proposal extra resources and allocations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.proposta_recurso_extra import PropostaRecursoExtra, PropostaRecursoAlocacao


class PropostaRecursoExtraRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaRecursoExtra]:
        result = await self.db.execute(
            select(PropostaRecursoExtra)
            .options(selectinload(PropostaRecursoExtra.alocacoes))
            .where(PropostaRecursoExtra.proposta_id == proposta_id)
            .order_by(PropostaRecursoExtra.criado_em)
        )
        return list(result.scalars().all())

    async def get_recurso(self, recurso_id: UUID) -> PropostaRecursoExtra | None:
        result = await self.db.execute(
            select(PropostaRecursoExtra)
            .options(selectinload(PropostaRecursoExtra.alocacoes))
            .where(PropostaRecursoExtra.id == recurso_id)
        )
        return result.scalar_one_or_none()

    async def list_by_composicao(self, composicao_id: UUID) -> list[PropostaRecursoAlocacao]:
        result = await self.db.execute(
            select(PropostaRecursoAlocacao)
            .options(selectinload(PropostaRecursoAlocacao.recurso_extra))
            .where(PropostaRecursoAlocacao.composicao_id == composicao_id)
        )
        return list(result.scalars().all())

    async def get_alocacao(self, alocacao_id: UUID) -> PropostaRecursoAlocacao | None:
        result = await self.db.execute(
            select(PropostaRecursoAlocacao)
            .where(PropostaRecursoAlocacao.id == alocacao_id)
        )
        return result.scalar_one_or_none()

    async def create_recurso(self, recurso: PropostaRecursoExtra) -> PropostaRecursoExtra:
        self.db.add(recurso)
        await self.db.flush()
        await self.db.refresh(recurso)
        return recurso

    async def create_alocacao(self, alocacao: PropostaRecursoAlocacao) -> PropostaRecursoAlocacao:
        self.db.add(alocacao)
        await self.db.flush()
        await self.db.refresh(alocacao)
        return alocacao

    async def delete_recurso(self, recurso: PropostaRecursoExtra) -> None:
        await self.db.delete(recurso)
        await self.db.flush()

    async def delete_alocacao(self, alocacao: PropostaRecursoAlocacao) -> None:
        await self.db.delete(alocacao)
        await self.db.flush()
