"""Repository for per-proposal cost snapshot (Histograma) tables."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from backend.models.proposta_pc import (
    PropostaPcMaoObra,
    PropostaPcEquipamentoPremissa,
    PropostaPcEquipamento,
    PropostaPcEncargo,
    PropostaPcEpi,
    PropostaPcFerramenta,
    PropostaPcMobilizacao,
)


class ProposalPcRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_mao_obra(self, proposta_id: UUID) -> list[PropostaPcMaoObra]:
        result = await self.db.execute(
            select(PropostaPcMaoObra)
            .where(PropostaPcMaoObra.proposta_id == proposta_id)
            .order_by(PropostaPcMaoObra.descricao_funcao)
        )
        return list(result.scalars().all())

    async def list_equipamento_premissas(self, proposta_id: UUID) -> list[PropostaPcEquipamentoPremissa]:
        result = await self.db.execute(
            select(PropostaPcEquipamentoPremissa).where(PropostaPcEquipamentoPremissa.proposta_id == proposta_id)
        )
        return list(result.scalars().all())

    async def list_equipamentos(self, proposta_id: UUID) -> list[PropostaPcEquipamento]:
        result = await self.db.execute(
            select(PropostaPcEquipamento)
            .where(PropostaPcEquipamento.proposta_id == proposta_id)
            .order_by(PropostaPcEquipamento.equipamento)
        )
        return list(result.scalars().all())

    async def list_encargos(self, proposta_id: UUID) -> list[PropostaPcEncargo]:
        result = await self.db.execute(
            select(PropostaPcEncargo)
            .where(PropostaPcEncargo.proposta_id == proposta_id)
            .order_by(PropostaPcEncargo.tipo_encargo, PropostaPcEncargo.discriminacao_encargo)
        )
        return list(result.scalars().all())

    async def list_epi(self, proposta_id: UUID) -> list[PropostaPcEpi]:
        result = await self.db.execute(
            select(PropostaPcEpi)
            .where(PropostaPcEpi.proposta_id == proposta_id)
            .order_by(PropostaPcEpi.epi)
        )
        return list(result.scalars().all())

    async def list_ferramentas(self, proposta_id: UUID) -> list[PropostaPcFerramenta]:
        result = await self.db.execute(
            select(PropostaPcFerramenta)
            .where(PropostaPcFerramenta.proposta_id == proposta_id)
            .order_by(PropostaPcFerramenta.descricao)
        )
        return list(result.scalars().all())

    async def list_mobilizacao(self, proposta_id: UUID) -> list[PropostaPcMobilizacao]:
        result = await self.db.execute(
            select(PropostaPcMobilizacao)
            .where(PropostaPcMobilizacao.proposta_id == proposta_id)
            .order_by(PropostaPcMobilizacao.descricao)
        )
        return list(result.scalars().all())

    async def bulk_upsert(self, model: type[Any], items: list[dict], index_elements: list[str]) -> None:
        """Upsert items based on unique constraint (e.g. proposta_id, bcu_item_id)."""
        if not items:
            return
        stmt = insert(model).values(items)
        update_dict = {k: getattr(stmt.excluded, k) for k in items[0].keys() if k not in index_elements}
        
        # We don't overwrite user-edited fields if editado_manualmente is True
        # For simplicity and given the requirements: we will explicitly preserve editado_manualmente=True items
        # in the service level by excluding them from the `items` list or using a complex CASE statement.
        # It's better to handle in the service layer: if the item exists and editado_manualmente=True, don't update.
        # But for new items or items not manually edited, we can update.
        
        if update_dict:
            # Only update if editado_manualmente == False in the target row.
            # In PostgreSQL: SET col1 = excluded.col1 WHERE target.editado_manualmente = False
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict,
                where=(model.editado_manualmente == False)
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
            
        await self.db.execute(stmt)

    async def bulk_insert(self, model: type[Any], items: list[dict]) -> None:
        if not items:
            return
        await self.db.execute(insert(model).values(items))

    async def clear_encargos(self, proposta_id: UUID) -> None:
        await self.db.execute(delete(PropostaPcEncargo).where(PropostaPcEncargo.proposta_id == proposta_id))

    async def clear_mobilizacao(self, proposta_id: UUID) -> None:
        await self.db.execute(delete(PropostaPcMobilizacao).where(PropostaPcMobilizacao.proposta_id == proposta_id))

    async def get_item(self, model: type[Any], item_id: UUID) -> Any | None:
        result = await self.db.execute(select(model).where(model.id == item_id))
        return result.scalar_one_or_none()
