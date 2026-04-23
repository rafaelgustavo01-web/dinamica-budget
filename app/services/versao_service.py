from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_cliente_perfil
from app.core.exceptions import NotFoundError
from app.models.composicao_cliente import ComposicaoCliente
from app.models.versao_composicao import VersaoComposicao
from app.repositories.itens_proprios_repository import ItensPropiosRepository
from app.repositories.versao_composicao_repository import VersaoComposicaoRepository

_PERFIS_EDICAO = ["APROVADOR", "ADMIN"]


class VersaoService:
    def __init__(
        self,
        versao_repo: VersaoComposicaoRepository,
        propria_repo: ItensPropiosRepository,
    ) -> None:
        self.versao_repo = versao_repo
        self.propria_repo = propria_repo

    async def assert_edit_permission(
        self, item_id: UUID, current_user, db: AsyncSession
    ) -> None:
        """Raise if current_user lacks edit permission on item's client."""
        item = await self.propria_repo.get_active_by_id(item_id)
        if not item:
            raise NotFoundError("ItemProprio", str(item_id))
        await require_cliente_perfil(
            item.cliente_id, _PERFIS_EDICAO, current_user, db
        )

    async def list_versoes(self, item_id: UUID) -> list[VersaoComposicao]:
        """List all versions for an item."""
        item = await self.propria_repo.get_active_by_id(item_id)
        if not item:
            raise NotFoundError("ItemProprio", str(item_id))
        return await self.versao_repo.list_versoes(item_id)

    async def criar_versao(
        self, item_id: UUID, current_user_id: UUID, db: AsyncSession
    ) -> VersaoComposicao:
        """Create new version (clone of active)."""
        item = await self.propria_repo.get_active_by_id(item_id)
        if not item:
            raise NotFoundError("ItemProprio", str(item_id))

        versoes_existentes = await self.versao_repo.list_versoes(item_id)
        next_numero = max((v.numero_versao for v in versoes_existentes), default=0) + 1

        nova_versao = VersaoComposicao(
            item_proprio_id=item_id,
            numero_versao=next_numero,
            is_ativa=False,
            criado_por_id=current_user_id,
        )
        db.add(nova_versao)
        await db.flush()

        # Clone ComposicaoCliente from active version
        versao_ativa = await self.versao_repo.get_versao_ativa(item_id)
        if versao_ativa:
            result = await db.execute(
                select(ComposicaoCliente).where(ComposicaoCliente.versao_id == versao_ativa.id)
            )
            for comp in result.scalars().all():
                db.add(
                    ComposicaoCliente(
                        versao_id=nova_versao.id,
                        insumo_base_id=comp.insumo_base_id,
                        insumo_proprio_id=comp.insumo_proprio_id,
                        quantidade_consumo=comp.quantidade_consumo,
                        unidade_medida=comp.unidade_medida,
                    )
                )

        await db.flush()
        await db.refresh(nova_versao)
        return nova_versao

    async def ativar_versao(
        self, versao_id: UUID, current_user_id: UUID, db: AsyncSession
    ) -> VersaoComposicao:
        """Activate a version, deactivate others for the same item."""
        versao = await self.versao_repo.get_by_id(versao_id)
        if not versao:
            raise NotFoundError("VersaoComposicao", str(versao_id))

        await self.versao_repo.deactivate_all(versao.item_proprio_id)
        versao.is_ativa = True
        await db.flush()
        await db.refresh(versao)
        return versao
