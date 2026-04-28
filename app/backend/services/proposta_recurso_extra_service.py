"""Service for handling per-proposal extra resources and their allocations."""

import uuid
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.models.proposta_recurso_extra import PropostaRecursoAlocacao, PropostaRecursoExtra
from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
from backend.repositories.proposta_recurso_extra_repository import PropostaRecursoExtraRepository
from backend.repositories.proposta_repository import PropostaRepository


class PropostaRecursoExtraService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PropostaRecursoExtraRepository(db)
        self.proposta_repo = PropostaRepository(db)
        self.composicao_repo = PropostaItemComposicaoRepository(db)

    async def criar(self, proposta_id: UUID, body: dict, criador_id: UUID) -> PropostaRecursoExtra:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        recurso = PropostaRecursoExtra(
            id=uuid.uuid4(),
            proposta_id=proposta_id,
            tipo_recurso=body.get("tipo_recurso"),
            descricao=body.get("descricao"),
            unidade_medida=body.get("unidade_medida"),
            custo_unitario=Decimal(str(body.get("custo_unitario"))),
            observacao=body.get("observacao"),
            criado_por_id=criador_id,
        )
        return await self.repo.create_recurso(recurso)

    async def atualizar(self, recurso_id: UUID, body: dict) -> PropostaRecursoExtra:
        recurso = await self.repo.get_recurso(recurso_id)
        if not recurso:
            raise NotFoundError("RecursoExtra", str(recurso_id))

        if "descricao" in body:
            recurso.descricao = body["descricao"]
        if "unidade_medida" in body:
            recurso.unidade_medida = body["unidade_medida"]
        if "custo_unitario" in body:
            recurso.custo_unitario = Decimal(str(body["custo_unitario"]))
        if "observacao" in body:
            recurso.observacao = body["observacao"]

        self.db.add(recurso)
        
        if len(recurso.alocacoes) > 0:
            proposta = await self.proposta_repo.get_by_id(recurso.proposta_id)
            if proposta:
                proposta.cpu_desatualizada = True
                self.db.add(proposta)

        await self.db.flush()
        await self.db.refresh(recurso)
        return recurso

    async def deletar(self, recurso_id: UUID) -> None:
        recurso = await self.repo.get_recurso(recurso_id)
        if not recurso:
            raise NotFoundError("RecursoExtra", str(recurso_id))

        had_allocations = len(recurso.alocacoes) > 0
        proposta_id = recurso.proposta_id

        await self.repo.delete_recurso(recurso)

        if had_allocations:
            proposta = await self.proposta_repo.get_by_id(proposta_id)
            if proposta:
                proposta.cpu_desatualizada = True
                self.db.add(proposta)
                await self.db.flush()

    async def alocar(self, proposta_id: UUID, composicao_id: UUID, recurso_extra_id: UUID, quantidade_consumo: Decimal) -> PropostaRecursoAlocacao:
        recurso = await self.repo.get_recurso(recurso_extra_id)
        if not recurso:
            raise NotFoundError("RecursoExtra", str(recurso_extra_id))
        
        if recurso.proposta_id != proposta_id:
            raise UnprocessableEntityError("Recurso extra não pertence a esta proposta.")

        alocacao = PropostaRecursoAlocacao(
            id=uuid.uuid4(),
            recurso_extra_id=recurso_extra_id,
            composicao_id=composicao_id,
            quantidade_consumo=quantidade_consumo,
        )
        await self.repo.create_alocacao(alocacao)

        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if proposta:
            proposta.cpu_desatualizada = True
            self.db.add(proposta)
            await self.db.flush()

        return alocacao

    async def desalocar(self, proposta_id: UUID, alocacao_id: UUID) -> None:
        alocacao = await self.repo.get_alocacao(alocacao_id)
        if not alocacao:
            raise NotFoundError("Alocacao", str(alocacao_id))

        await self.repo.delete_alocacao(alocacao)

        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if proposta:
            proposta.cpu_desatualizada = True
            self.db.add(proposta)
            await self.db.flush()

    async def listar_por_proposta(self, proposta_id: UUID) -> list[dict]:
        recursos = await self.repo.list_by_proposta(proposta_id)
        return [
            {
                "id": r.id,
                "proposta_id": r.proposta_id,
                "tipo_recurso": r.tipo_recurso,
                "descricao": r.descricao,
                "unidade_medida": r.unidade_medida,
                "custo_unitario": r.custo_unitario,
                "observacao": r.observacao,
                "alocacoes_count": len(r.alocacoes),
            }
            for r in recursos
        ]
