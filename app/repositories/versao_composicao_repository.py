"""
Repository for operacional.versao_composicao — versioned BOM for client items.
Only PROPRIA items (ItemProprio) are versioned.
TCPO items use the immutable composicao_base instead.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.composicao_cliente import ComposicaoCliente
from app.models.versao_composicao import VersaoComposicao
from app.repositories.base_repository import BaseRepository


class VersaoComposicaoRepository(BaseRepository[VersaoComposicao]):
    model = VersaoComposicao

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_versao_ativa(self, item_proprio_id: UUID) -> VersaoComposicao | None:
        """
        Returns the active version for a PROPRIA item.
        Eagerly loads itens with both insumo_base (TCPO) and insumo_proprio (PROPRIA).
        """
        result = await self.db.execute(
            select(VersaoComposicao)
            .options(
                selectinload(VersaoComposicao.itens).selectinload(
                    ComposicaoCliente.insumo_base
                ),
                selectinload(VersaoComposicao.itens).selectinload(
                    ComposicaoCliente.insumo_proprio
                ),
            )
            .where(
                VersaoComposicao.item_proprio_id == item_proprio_id,
                VersaoComposicao.is_ativa.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_versoes(self, item_proprio_id: UUID) -> list[VersaoComposicao]:
        """Returns all versions for a PROPRIA item, newest first."""
        result = await self.db.execute(
            select(VersaoComposicao)
            .where(VersaoComposicao.item_proprio_id == item_proprio_id)
            .order_by(VersaoComposicao.numero_versao.desc())
        )
        return list(result.scalars().all())

    async def get_with_itens(self, versao_id: UUID) -> VersaoComposicao | None:
        """
        Load a version with full ComposicaoCliente items and their insumos.
        Used by recalcular_custo_pai and explode_composicao.
        """
        result = await self.db.execute(
            select(VersaoComposicao)
            .options(
                selectinload(VersaoComposicao.itens).selectinload(
                    ComposicaoCliente.insumo_base
                ),
                selectinload(VersaoComposicao.itens).selectinload(
                    ComposicaoCliente.insumo_proprio
                ),
            )
            .where(VersaoComposicao.id == versao_id)
        )
        return result.scalar_one_or_none()

    async def deactivate_all(self, item_proprio_id: UUID) -> None:
        """
        Deactivates all versions for a given item before activating a new one.
        Caller must commit the transaction.
        """
        result = await self.db.execute(
            select(VersaoComposicao).where(
                VersaoComposicao.item_proprio_id == item_proprio_id,
                VersaoComposicao.is_ativa.is_(True),
            )
        )
        for versao in result.scalars().all():
            versao.is_ativa = False
        await self.db.flush()
