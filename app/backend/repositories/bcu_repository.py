"""Repository for BCU schema tables."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bcu import (
    BcuCabecalho,
    BcuEncargoItem,
    BcuEquipamentoItem,
    BcuEquipamentoPremissa,
    BcuEpiItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuMobilizacaoItem,
)


class BcuRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_cabecalho_by_id(self, cabecalho_id: UUID) -> BcuCabecalho | None:
        result = await self.db.execute(select(BcuCabecalho).where(BcuCabecalho.id == cabecalho_id))
        return result.scalar_one_or_none()

    async def list_cabecalhos(self) -> list[BcuCabecalho]:
        result = await self.db.execute(select(BcuCabecalho).order_by(BcuCabecalho.criado_em.desc()))
        return list(result.scalars().all())

    async def get_cabecalho_ativo(self) -> BcuCabecalho | None:
        result = await self.db.execute(
            select(BcuCabecalho).where(BcuCabecalho.is_ativo == True).limit(1)
        )
        return result.scalar_one_or_none()

    async def desativar_todos_cabecalhos(self) -> None:
        await self.db.execute(
            BcuCabecalho.__table__.update().values(is_ativo=False)
        )

    async def list_mao_obra(self, cabecalho_id: UUID) -> list[BcuMaoObraItem]:
        result = await self.db.execute(
            select(BcuMaoObraItem)
            .where(BcuMaoObraItem.cabecalho_id == cabecalho_id)
            .order_by(BcuMaoObraItem.descricao_funcao)
        )
        return list(result.scalars().all())

    async def list_equipamento_premissas(self, cabecalho_id: UUID) -> list[BcuEquipamentoPremissa]:
        result = await self.db.execute(
            select(BcuEquipamentoPremissa).where(BcuEquipamentoPremissa.cabecalho_id == cabecalho_id)
        )
        return list(result.scalars().all())

    async def list_equipamento_items(self, cabecalho_id: UUID) -> list[BcuEquipamentoItem]:
        result = await self.db.execute(
            select(BcuEquipamentoItem)
            .where(BcuEquipamentoItem.cabecalho_id == cabecalho_id)
            .order_by(BcuEquipamentoItem.equipamento)
        )
        return list(result.scalars().all())

    async def list_encargos(self, cabecalho_id: UUID) -> list[BcuEncargoItem]:
        result = await self.db.execute(
            select(BcuEncargoItem)
            .where(BcuEncargoItem.cabecalho_id == cabecalho_id)
            .order_by(BcuEncargoItem.tipo_encargo, BcuEncargoItem.discriminacao_encargo)
        )
        return list(result.scalars().all())

    async def list_epi_items(self, cabecalho_id: UUID) -> list[BcuEpiItem]:
        result = await self.db.execute(
            select(BcuEpiItem)
            .where(BcuEpiItem.cabecalho_id == cabecalho_id)
            .order_by(BcuEpiItem.epi)
        )
        return list(result.scalars().all())

    async def list_ferramenta_items(self, cabecalho_id: UUID) -> list[BcuFerramentaItem]:
        result = await self.db.execute(
            select(BcuFerramentaItem)
            .where(BcuFerramentaItem.cabecalho_id == cabecalho_id)
            .order_by(BcuFerramentaItem.descricao)
        )
        return list(result.scalars().all())

    async def list_mobilizacao_items(self, cabecalho_id: UUID) -> list[BcuMobilizacaoItem]:
        result = await self.db.execute(
            select(BcuMobilizacaoItem)
            .where(BcuMobilizacaoItem.cabecalho_id == cabecalho_id)
            .order_by(BcuMobilizacaoItem.descricao)
        )
        return list(result.scalars().all())
