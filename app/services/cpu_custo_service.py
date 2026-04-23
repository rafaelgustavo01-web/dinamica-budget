from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select

from app.models.enums import TipoRecurso
from app.models.pc_tabelas import PcEquipamentoItem, PcMaoObraItem
from app.models.proposta import PropostaItemComposicao


class CpuCustoService:
    def __init__(self, db, pc_cabecalho_id: UUID | None = None) -> None:
        self.db = db
        self.pc_cabecalho_id = pc_cabecalho_id

    async def calcular_custos(self, composicoes: list[PropostaItemComposicao]) -> None:
        for comp in composicoes:
            custo = comp.custo_unitario_insumo
            fonte = comp.fonte_custo or "custo_base"

            if self.pc_cabecalho_id and comp.tipo_recurso == TipoRecurso.MO:
                lookup = await self._lookup_mao_obra(comp.descricao_insumo)
                if lookup is not None:
                    custo = lookup
                    fonte = "pc_mao_obra"
            elif self.pc_cabecalho_id and comp.tipo_recurso == TipoRecurso.EQUIPAMENTO:
                lookup = await self._lookup_equipamento(comp.descricao_insumo)
                if lookup is not None:
                    custo = lookup
                    fonte = "pc_equipamento"

            comp.custo_unitario_insumo = custo
            comp.fonte_custo = fonte
            if custo is not None:
                comp.custo_total_insumo = custo * comp.quantidade_consumo
            else:
                comp.custo_total_insumo = None

    async def _lookup_mao_obra(self, descricao: str) -> Decimal | None:
        normalized = descricao.strip().lower()
        result = await self.db.execute(
            select(PcMaoObraItem.custo_unitario_h)
            .where(
                PcMaoObraItem.pc_cabecalho_id == self.pc_cabecalho_id,
                func.lower(PcMaoObraItem.descricao_funcao) == normalized,
            )
            .limit(1)
        )
        value = result.scalar_one_or_none()
        if value is not None:
            return value

        fallback = await self.db.execute(
            select(PcMaoObraItem.custo_unitario_h)
            .where(
                PcMaoObraItem.pc_cabecalho_id == self.pc_cabecalho_id,
                PcMaoObraItem.descricao_funcao.ilike(f"%{descricao.strip()}%"),
            )
            .limit(1)
        )
        return fallback.scalar_one_or_none()

    async def _lookup_equipamento(self, descricao: str) -> Decimal | None:
        normalized = descricao.strip().lower()
        cost_expr = (
            func.coalesce(PcEquipamentoItem.aluguel_r_h, 0)
            + func.coalesce(PcEquipamentoItem.combustivel_r_h, 0)
            + func.coalesce(PcEquipamentoItem.mao_obra_r_h, 0)
        )
        result = await self.db.execute(
            select(cost_expr)
            .where(
                PcEquipamentoItem.pc_cabecalho_id == self.pc_cabecalho_id,
                func.lower(PcEquipamentoItem.equipamento) == normalized,
            )
            .limit(1)
        )
        value = result.scalar_one_or_none()
        if value is not None:
            return value

        fallback = await self.db.execute(
            select(cost_expr)
            .where(
                PcEquipamentoItem.pc_cabecalho_id == self.pc_cabecalho_id,
                PcEquipamentoItem.equipamento.ilike(f"%{descricao.strip()}%"),
            )
            .limit(1)
        )
        return fallback.scalar_one_or_none()
