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


class PropostaPcRepository:
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
        exclude_from_update = set(index_elements + ["id", "criado_em", "editado_manualmente"])
        update_dict = {k: getattr(stmt.excluded, k) for k in items[0].keys() if k not in exclude_from_update}
        
        if update_dict:
            # Only update if editado_manualmente == False in the target row.
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict,
                where=(model.editado_manualmente.is_(False))
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


# Backwards-compat alias: old name kept so external callers survive the rename
ProposalPcRepository = PropostaPcRepository
