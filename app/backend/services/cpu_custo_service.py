from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from backend.core.logging import get_logger
from backend.models.base_tcpo import BaseTcpo
from backend.models.bcu import BcuEquipamentoItem, BcuMaoObraItem
from backend.models.enums import TipoRecurso
from backend.models.proposta import PropostaItemComposicao
from backend.services.bcu_de_para_service import BcuDeParaService
from backend.models.proposta_pc import (
    PropostaPcMaoObra,
    PropostaPcEquipamento,
    PropostaPcEpi,
    PropostaPcFerramenta,
)

logger = get_logger(__name__)


class CpuCustoService:
    def __init__(self, db, bcu_cabecalho_id: UUID | None = None, proposta_id: UUID | None = None) -> None:
        self.db = db
        self.bcu_cabecalho_id = bcu_cabecalho_id
        self.proposta_id = proposta_id
        self.de_para_svc = BcuDeParaService(db)

    async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
        for comp in composicoes:
            custo = comp.custo_unitario_insumo
            fonte = comp.fonte_custo or "custo_base"

            if comp.insumo_base_id:
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

            # Somar alocações de recursos extras
            custo_extra = await self._sum_recursos_extras(comp.id)

            comp.custo_unitario_insumo = custo
            comp.fonte_custo = fonte
            
            if custo is not None or custo_extra > 0:
                base = custo or Decimal("0")
                comp.custo_total_insumo = (base * comp.quantidade_consumo) + custo_extra
            else:
                comp.custo_total_insumo = None

    async def _sum_recursos_extras(self, composicao_id: UUID) -> Decimal:
        if not composicao_id:
            return Decimal("0")
        from backend.models.proposta_recurso_extra import PropostaRecursoAlocacao, PropostaRecursoExtra
        result = await self.db.execute(
            select(PropostaRecursoAlocacao.quantidade_consumo, PropostaRecursoExtra.custo_unitario)
            .join(PropostaRecursoExtra, PropostaRecursoAlocacao.recurso_extra_id == PropostaRecursoExtra.id)
            .where(PropostaRecursoAlocacao.composicao_id == composicao_id)
        )
        total = sum((qtd * custo) for qtd, custo in result.all())
        return Decimal(str(total))

    async def _lookup_via_de_para(self, insumo_base_id: UUID) -> Decimal | None:
        mapping = await self.de_para_svc.lookup_bcu_para_base_tcpo(insumo_base_id)
        if not mapping:
            return None

        bcu_type, bcu_item_id = mapping

        # Se temos proposta_id, tentar snapshot primeiro
        if self.proposta_id:
            if bcu_type.value == "MO":
                r = await self.db.execute(
                    select(PropostaPcMaoObra.valor_bcu_snapshot)
                    .where(PropostaPcMaoObra.proposta_id == self.proposta_id, PropostaPcMaoObra.bcu_item_id == bcu_item_id)
                )
                val = r.scalar_one_or_none()
                if val is not None:
                    return val
            elif bcu_type.value == "EQP":
                r = await self.db.execute(
                    select(PropostaPcEquipamento.valor_bcu_snapshot)
                    .where(PropostaPcEquipamento.proposta_id == self.proposta_id, PropostaPcEquipamento.bcu_item_id == bcu_item_id)
                )
                val = r.scalar_one_or_none()
                if val is not None:
                    return val
            elif bcu_type.value == "EPI":
                r = await self.db.execute(
                    select(PropostaPcEpi.valor_bcu_snapshot)
                    .where(PropostaPcEpi.proposta_id == self.proposta_id, PropostaPcEpi.bcu_item_id == bcu_item_id)
                )
                val = r.scalar_one_or_none()
                if val is not None:
                    return val
            elif bcu_type.value == "FER":
                r = await self.db.execute(
                    select(PropostaPcFerramenta.valor_bcu_snapshot)
                    .where(PropostaPcFerramenta.proposta_id == self.proposta_id, PropostaPcFerramenta.bcu_item_id == bcu_item_id)
                )
                val = r.scalar_one_or_none()
                if val is not None:
                    return val

        if not self.bcu_cabecalho_id:
            return None

        # Fallback para BCU Global
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
