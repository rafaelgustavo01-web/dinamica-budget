from uuid import UUID

from backend.core.exceptions import UnprocessableEntityError
from backend.models.enums import PropostaPapel
from backend.models.proposta import PropostaAcl
from backend.repositories.proposta_acl_repository import PropostaAclRepository


class PropostaAclService:
    HIERARQUIA = {
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
    }

    def __init__(self, db) -> None:
        self.repo = PropostaAclRepository(db)

    async def conceder(self, proposta_id: UUID, usuario_id: UUID, papel: PropostaPapel, created_by: UUID) -> PropostaAcl:
        # Idempotente: se já existe, retorna existente
        papeis = await self.repo.get_papeis_for_user(proposta_id, usuario_id)
        if papel in papeis:
            result = await self.repo.list_by_proposta(proposta_id)
            for item in result:
                if item.usuario_id == usuario_id and item.papel == papel:
                    return item
        return await self.repo.add_papel(proposta_id, usuario_id, papel, created_by)

    async def revogar(self, proposta_id: UUID, usuario_id: UUID, papel: PropostaPapel) -> None:
        if papel == PropostaPapel.OWNER:
            count = await self.repo.count_owners(proposta_id)
            if count <= 1:
                raise UnprocessableEntityError("Proposta nao pode ficar sem OWNER.")
        await self.repo.remove_papel(proposta_id, usuario_id, papel)

    async def listar(self, proposta_id: UUID) -> list[PropostaAcl]:
        return await self.repo.list_by_proposta(proposta_id)

    async def papel_efetivo(self, proposta_id: UUID, usuario_id: UUID) -> PropostaPapel | None:
        papeis = await self.repo.get_papeis_for_user(proposta_id, usuario_id)
        if not papeis:
            return None
        return max(papeis, key=lambda p: self.HIERARQUIA.get(p, 1))
