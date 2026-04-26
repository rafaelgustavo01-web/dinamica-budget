from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.enums import PropostaPapel
from backend.models.proposta import PropostaAcl
from backend.repositories.base_repository import BaseRepository


class PropostaAclRepository(BaseRepository[PropostaAcl]):
    model = PropostaAcl

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def list_by_proposta(self, proposta_id: UUID) -> list[PropostaAcl]:
        result = await self.db.execute(
            select(PropostaAcl)
            .where(PropostaAcl.proposta_id == proposta_id)
            .order_by(PropostaAcl.papel.asc(), PropostaAcl.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_papeis_for_user(self, proposta_id: UUID, usuario_id: UUID) -> set[PropostaPapel]:
        result = await self.db.execute(
            select(PropostaAcl.papel)
            .where(PropostaAcl.proposta_id == proposta_id, PropostaAcl.usuario_id == usuario_id)
        )
        return {row[0] for row in result.fetchall()}

    async def get_papeis_bulk(self, proposta_ids: list[UUID], usuario_id: UUID) -> dict[UUID, PropostaPapel]:
        if not proposta_ids:
            return {}
        result = await self.db.execute(
            select(PropostaAcl.proposta_id, PropostaAcl.papel)
            .where(PropostaAcl.proposta_id.in_(proposta_ids), PropostaAcl.usuario_id == usuario_id)
        )
        # Retorna o MAIOR papel por proposta
        from backend.services.proposta_acl_service import PropostaAclService

        hierarquia = PropostaAclService.HIERARQUIA
        papeis_map: dict[UUID, list[PropostaPapel]] = {}
        for proposta_id, papel in result.fetchall():
            papeis_map.setdefault(proposta_id, []).append(papel)
        return {
            pid: max(papeis, key=lambda p: hierarquia.get(p, 1))
            for pid, papeis in papeis_map.items()
        }

    async def add_papel(self, proposta_id: UUID, usuario_id: UUID, papel: PropostaPapel, created_by: UUID) -> PropostaAcl:
        acl = PropostaAcl(
            proposta_id=proposta_id,
            usuario_id=usuario_id,
            papel=papel,
            created_by=created_by,
        )
        self.db.add(acl)
        await self.db.flush()
        await self.db.refresh(acl)
        return acl

    async def remove_papel(self, proposta_id: UUID, usuario_id: UUID, papel: PropostaPapel) -> bool:
        result = await self.db.execute(
            delete(PropostaAcl)
            .where(
                PropostaAcl.proposta_id == proposta_id,
                PropostaAcl.usuario_id == usuario_id,
                PropostaAcl.papel == papel,
            )
        )
        await self.db.flush()
        return result.rowcount > 0

    async def count_owners(self, proposta_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(PropostaAcl)
            .where(PropostaAcl.proposta_id == proposta_id, PropostaAcl.papel == PropostaPapel.OWNER)
        )
        return result.scalar_one()
