import asyncio
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
        # Cache de snapshots do histograma (preenche em _warm_histogram_cache)
        self._hist_snapshots: dict[str, dict[UUID, Decimal]] | None = None

    async def _warm_histogram_cache(self) -> dict[str, dict[UUID, Decimal]]:
        """Prefetcha todos os snapshots do histograma da proposta em 4 queries paralelas."""
        if self._hist_snapshots is not None:
            return self._hist_snapshots

        if not self.proposta_id:
            self._hist_snapshots = {}
            return self._hist_snapshots

        mo_r, eqp_r, epi_r, fer_r = await asyncio.gather(
            self.db.execute(
                select(PropostaPcMaoObra.bcu_item_id, PropostaPcMaoObra.valor_bcu_snapshot)
                .where(PropostaPcMaoObra.proposta_id == self.proposta_id)
                .where(PropostaPcMaoObra.bcu_item_id.isnot(None))
            ),
            self.db.execute(
                select(PropostaPcEquipamento.bcu_item_id, PropostaPcEquipamento.valor_bcu_snapshot)
                .where(PropostaPcEquipamento.proposta_id == self.proposta_id)
                .where(PropostaPcEquipamento.bcu_item_id.isnot(None))
            ),
            self.db.execute(
                select(PropostaPcEpi.bcu_item_id, PropostaPcEpi.valor_bcu_snapshot)
                .where(PropostaPcEpi.proposta_id == self.proposta_id)
                .where(PropostaPcEpi.bcu_item_id.isnot(None))
            ),
            self.db.execute(
                select(PropostaPcFerramenta.bcu_item_id, PropostaPcFerramenta.valor_bcu_snapshot)
                .where(PropostaPcFerramenta.proposta_id == self.proposta_id)
                .where(PropostaPcFerramenta.bcu_item_id.isnot(None))
            ),
        )

        self._hist_snapshots = {
            "MO": {row[0]: row[1] for row in mo_r if row[1] is not None},
            "EQP": {row[0]: row[1] for row in eqp_r if row[1] is not None},
            "EPI": {row[0]: row[1] for row in epi_r if row[1] is not None},
            "FER": {row[0]: row[1] for row in fer_r if row[1] is not None},
        }
        return self._hist_snapshots

    async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
        # Warm histogram cache once per batch
        hist_cache = await self._warm_histogram_cache()

        for comp in composicoes:
            custo = comp.custo_unitario_insumo
            fonte = comp.fonte_custo or "custo_base"

            if comp.insumo_base_id:
                lookup = await self._lookup_via_de_para(comp.insumo_base_id, hist_cache)
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

    async def _lookup_via_de_para(self, insumo_base_id: UUID, hist_cache: dict[str, dict[UUID, Decimal]]) -> Decimal | None:
        mapping = await self.de_para_svc.lookup_bcu_para_base_tcpo(insumo_base_id)
        if not mapping:
            return None

        bcu_type, bcu_item_id = mapping
        type_key = bcu_type.value if hasattr(bcu_type, "value") else str(bcu_type)

        # Se temos proposta_id, tentar snapshot primeiro (agora via cache)
        if self.proposta_id and hist_cache:
            cached = hist_cache.get(type_key, {}).get(bcu_item_id)
            if cached is not None:
                return cached

        if not self.bcu_cabecalho_id:
            return None

        # Fallback para BCU Global
        if type_key == "MO":
            result = await self.db.execute(
                select(BcuMaoObraItem.custo_unitario_h)
                .where(BcuMaoObraItem.id == bcu_item_id, BcuMaoObraItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        elif type_key == "EQP":
            result = await self.db.execute(
                select(BcuEquipamentoItem.aluguel_r_h)
                .where(BcuEquipamentoItem.id == bcu_item_id, BcuEquipamentoItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        elif type_key == "EPI":
            from backend.models.bcu import BcuEpiItem
            result = await self.db.execute(
                select(BcuEpiItem.custo_unitario)
                .where(BcuEpiItem.id == bcu_item_id, BcuEpiItem.cabecalho_id == self.bcu_cabecalho_id)
            )
            return result.scalar_one_or_none()
        elif type_key == "FER":
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
