from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from backend.core.logging import get_logger
from backend.models.base_tcpo import BaseTcpo
from backend.models.bcu import BcuEquipamentoItem, BcuMaoObraItem
from backend.models.enums import TipoRecurso
from backend.models.proposta import PropostaItemComposicao
from backend.services.bcu_de_para_service import BcuDeParaService

logger = get_logger(__name__)


class CpuCustoService:
    def __init__(self, db, bcu_cabecalho_id: UUID | None = None) -> None:
        self.db = db
        self.bcu_cabecalho_id = bcu_cabecalho_id
        self.de_para_svc = BcuDeParaService(db)

    async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
        for comp in composicoes:
            custo = comp.custo_unitario_insumo
            fonte = comp.fonte_custo or "custo_base"

            if self.bcu_cabecalho_id and comp.insumo_base_id:
                lookup = await self._lookup_via_de_para(comp.insumo_base_id)
                if lookup is not None:
                    custo = lookup
                    fonte = "bcu_de_para"
                else:
                    # Fallback para BaseTcpo.custo_base
                    fallback = await self._fallback_base_tcpo(comp.insumo_base_id)
                    if fallback is not None:
                        custo = fallback
                        fonte = "base_tcpo_fallback"
                        logger.warning(
                            "cpu_custo.fallback",
                            insumo_id=str(comp.insumo_base_id),
                            descricao=comp.descricao_insumo,
                            custo_base=float(fallback),
                        )

            comp.custo_unitario_insumo = custo
            comp.fonte_custo = fonte
            if custo is not None:
                comp.custo_total_insumo = custo * comp.quantidade_consumo
            else:
                comp.custo_total_insumo = None

    async def _lookup_via_de_para(self, insumo_base_id: UUID) -> Decimal | None:
        mapping = await self.de_para_svc.lookup_bcu_para_base_tcpo(insumo_base_id)
        if not mapping:
            return None

        bcu_type, bcu_item_id = mapping

        if bcu_type.value == "MO":
            result = await self.db.execute(
                select(BcuMaoObraItem.custo_unitario_h)
                .where(BcuMaoObraItem.id == bcu_item_id, BcuMaoObraItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        elif bcu_type.value == "EQP":
            result = await self.db.execute(
                select(BcuEquipamentoItem.aluguel_r_h)
                .where(BcuEquipamentoItem.id == bcu_item_id, BcuEquipamentoItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        elif bcu_type.value == "EPI":
            from backend.models.bcu import BcuEpiItem
            result = await self.db.execute(
                select(BcuEpiItem.custo_unitario)
                .where(BcuEpiItem.id == bcu_item_id, BcuEpiItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        elif bcu_type.value == "FER":
            from backend.models.bcu import BcuFerramentaItem
            result = await self.db.execute(
                select(BcuFerramentaItem.preco)
                .where(BcuFerramentaItem.id == bcu_item_id, BcuFerramentaItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        return None

    async def _fallback_base_tcpo(self, insumo_base_id: UUID) -> Decimal | None:
        result = await self.db.execute(select(BaseTcpo.custo_base).where(BaseTcpo.id == insumo_base_id))
        return result.scalar_one_or_none()
