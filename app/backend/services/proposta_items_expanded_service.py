"""
Service para gerenciar items de propostas com suporte a múltiplos tipos
(EPI, Mão de Obra, Equipamentos, Ferramentas).

Regra de negócio do valor unitário (valor "completo" do item):
- Mão de Obra: salário (ou reajuste) + encargos + benefícios mensais
- EPI:        custo unitário (preço da peça)
- Equipamento: aluguel/h + combustível/h + mão de obra/h
- Ferramenta: preço unitário
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.proposta_pc import (
    PropostaPcEpi,
    PropostaPcEquipamento,
    PropostaPcFerramenta,
    PropostaPcMaoObra,
)
from backend.models.bcu import (
    BcuEpiItem,
    BcuEquipamentoItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
)
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_repository import PropostaRepository


def _d(v) -> Decimal:
    """Decimal seguro (None → 0)."""
    return Decimal(str(v)) if v is not None else Decimal(0)


def _total_mao_obra(item: BcuMaoObraItem) -> Decimal:
    """Custo mensal total: salário ajustado + encargos + benefícios."""
    if item.custo_mensal:
        return _d(item.custo_mensal)
    base = _d(item.previsao_reajuste) if item.previsao_reajuste else _d(item.salario)
    encargos_pct = _d(item.encargos_percent)
    encargos = base * encargos_pct if encargos_pct else Decimal(0)
    beneficios = (
        _d(item.refeicao)
        + _d(item.agua_potavel)
        + _d(item.vale_alimentacao)
        + _d(item.plano_saude)
        + _d(item.seguro_vida)
        + _d(item.abono_ferias)
        + _d(item.ferramentas_val)
        + _d(item.uniforme_val)
        + _d(item.epi_val)
        + _d(item.periculosidade_insalubridade)
        + _d(item.mobilizacao)
    )
    return base + encargos + beneficios


def _total_equipamento(item: BcuEquipamentoItem) -> Decimal:
    """Custo R$/h: aluguel/h + combustível/h + mão de obra/h."""
    if item.hora_produtiva:
        return _d(item.hora_produtiva)
    return _d(item.aluguel_r_h) + _d(item.combustivel_r_h) + _d(item.mao_obra_r_h)


def _total_epi(item: BcuEpiItem) -> Decimal:
    return _d(item.custo_unitario)


def _total_ferramenta(item: BcuFerramentaItem) -> Decimal:
    return _d(item.preco)


class PropostaItemsExpandedService:
    """Serviço expandido de items com suporte a múltiplos tipos."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.item_repo = PropostaItemRepository(db)

    async def listar_tipos_disponiveis(self, proposta_id: UUID) -> dict:
        return {
            "tipos": [
                {"id": "mao_obra", "label": "Mão de Obra", "descricao": "Selecione da base de custos", "campos": ["bcu_item_id", "quantidade"]},
                {"id": "epi", "label": "EPI (Equipamento de Proteção)", "descricao": "Selecione equipamento de proteção", "campos": ["bcu_item_id", "quantidade"]},
                {"id": "equipamento", "label": "Equipamento", "descricao": "Selecione equipamento", "campos": ["bcu_item_id", "quantidade"]},
                {"id": "ferramenta", "label": "Ferramenta", "descricao": "Selecione ferramenta", "campos": ["bcu_item_id", "quantidade"]},
            ]
        }

    # ── Catálogo BCU (valor já é o TOTAL agregado) ────────────────────────

    async def listar_bcu_mao_obra(self) -> list[dict]:
        items = (await self.db.execute(select(BcuMaoObraItem).limit(500))).scalars().all()
        return [
            {"id": str(it.id), "codigo": it.codigo_origem, "descricao": it.descricao_funcao, "valor": float(_total_mao_obra(it))}
            for it in items
        ]

    async def listar_bcu_epi(self) -> list[dict]:
        items = (await self.db.execute(select(BcuEpiItem).limit(500))).scalars().all()
        return [
            {"id": str(it.id), "codigo": it.codigo_origem, "descricao": it.epi, "valor": float(_total_epi(it))}
            for it in items
        ]

    async def listar_bcu_equipamento(self) -> list[dict]:
        items = (await self.db.execute(select(BcuEquipamentoItem).limit(500))).scalars().all()
        return [
            {"id": str(it.id), "codigo": it.codigo_origem, "descricao": it.equipamento, "valor": float(_total_equipamento(it))}
            for it in items
        ]

    async def listar_bcu_ferramenta(self) -> list[dict]:
        items = (await self.db.execute(select(BcuFerramentaItem).limit(500))).scalars().all()
        return [
            {"id": str(it.id), "codigo": it.codigo_origem, "descricao": it.descricao, "valor": float(_total_ferramenta(it))}
            for it in items
        ]

    # ── Listagem unificada da proposta ───────────────────────────────────

    async def listar_items_unificados(self, proposta_id: UUID) -> list[dict]:
        """Agrega items das 4 tabelas PC com formato uniforme."""
        out: list[dict] = []
        ordem = 1

        mo_rows = (
            await self.db.execute(
                select(PropostaPcMaoObra, BcuMaoObraItem)
                .outerjoin(BcuMaoObraItem, PropostaPcMaoObra.bcu_item_id == BcuMaoObraItem.id)
                .where(PropostaPcMaoObra.proposta_id == proposta_id)
                .order_by(PropostaPcMaoObra.criado_em.asc())
            )
        ).all()
        for pc, bcu in mo_rows:
            valor_un = _d(pc.valor_bcu_snapshot) or _d(pc.custo_mensal)
            if not valor_un and bcu:
                valor_un = _total_mao_obra(bcu)
            if not valor_un:
                valor_un = _d(pc.salario)
            qtd = _d(pc.quantidade)
            out.append({
                "id": str(pc.id),
                "proposta_id": str(proposta_id),
                "tipo": "mao_obra",
                "codigo": pc.codigo_origem or "",
                "descricao": pc.descricao_funcao,
                "unidade_medida": "mês",
                "quantidade": int(qtd),
                "valor_unitario": float(valor_un),
                "valor_total": float(valor_un * qtd),
                "ordem": ordem,
            })
            ordem += 1

        epi_rows = (
            await self.db.execute(
                select(PropostaPcEpi, BcuEpiItem)
                .outerjoin(BcuEpiItem, PropostaPcEpi.bcu_item_id == BcuEpiItem.id)
                .where(PropostaPcEpi.proposta_id == proposta_id)
                .order_by(PropostaPcEpi.criado_em.asc())
            )
        ).all()
        for pc, bcu in epi_rows:
            valor_un = _d(pc.valor_bcu_snapshot) or _d(pc.custo_unitario)
            if not valor_un and bcu:
                valor_un = _total_epi(bcu)
            qtd = _d(pc.quantidade)
            out.append({
                "id": str(pc.id),
                "proposta_id": str(proposta_id),
                "tipo": "epi",
                "codigo": pc.codigo_origem or "",
                "descricao": pc.epi,
                "unidade_medida": pc.unidade or "un",
                "quantidade": int(qtd),
                "valor_unitario": float(valor_un),
                "valor_total": float(valor_un * qtd),
                "ordem": ordem,
            })
            ordem += 1

        eqp_rows = (
            await self.db.execute(
                select(PropostaPcEquipamento, BcuEquipamentoItem)
                .outerjoin(BcuEquipamentoItem, PropostaPcEquipamento.bcu_item_id == BcuEquipamentoItem.id)
                .where(PropostaPcEquipamento.proposta_id == proposta_id)
                .order_by(PropostaPcEquipamento.criado_em.asc())
            )
        ).all()
        for pc, bcu in eqp_rows:
            valor_un = _d(pc.valor_bcu_snapshot) or _d(pc.hora_produtiva)
            if not valor_un and bcu:
                valor_un = _total_equipamento(bcu)
            qtd = _d(pc.quantidade)
            out.append({
                "id": str(pc.id),
                "proposta_id": str(proposta_id),
                "tipo": "equipamento",
                "codigo": pc.codigo_origem or "",
                "descricao": pc.equipamento,
                "unidade_medida": "h",
                "quantidade": int(qtd),
                "valor_unitario": float(valor_un),
                "valor_total": float(valor_un * qtd),
                "ordem": ordem,
            })
            ordem += 1

        fer_rows = (
            await self.db.execute(
                select(PropostaPcFerramenta, BcuFerramentaItem)
                .outerjoin(BcuFerramentaItem, PropostaPcFerramenta.bcu_item_id == BcuFerramentaItem.id)
                .where(PropostaPcFerramenta.proposta_id == proposta_id)
                .order_by(PropostaPcFerramenta.criado_em.asc())
            )
        ).all()
        for pc, bcu in fer_rows:
            valor_un = _d(pc.valor_bcu_snapshot) or _d(pc.preco)
            if not valor_un and bcu:
                valor_un = _total_ferramenta(bcu)
            qtd = _d(pc.quantidade)
            out.append({
                "id": str(pc.id),
                "proposta_id": str(proposta_id),
                "tipo": "ferramenta",
                "codigo": pc.codigo_origem or "",
                "descricao": pc.descricao,
                "unidade_medida": pc.unidade or "un",
                "quantidade": int(qtd),
                "valor_unitario": float(valor_un),
                "valor_total": float(valor_un * qtd),
                "ordem": ordem,
            })
            ordem += 1

        return out

    # ── Adicionar ────────────────────────────────────────────────────────

    async def adicionar_mao_obra(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: int,
    ) -> dict:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        bcu_item = (
            await self.db.execute(select(BcuMaoObraItem).where(BcuMaoObraItem.id == bcu_item_id))
        ).scalar_one_or_none()
        if not bcu_item:
            raise ValueError("Item de mão de obra não encontrado na base")

        total = _total_mao_obra(bcu_item)
        qtd = max(1, int(quantidade))
        pc_item = PropostaPcMaoObra(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            descricao_funcao=bcu_item.descricao_funcao,
            codigo_origem=bcu_item.codigo_origem,
            quantidade=qtd,
            salario=bcu_item.salario,
            previsao_reajuste=bcu_item.previsao_reajuste,
            encargos_percent=bcu_item.encargos_percent,
            refeicao=bcu_item.refeicao,
            agua_potavel=bcu_item.agua_potavel,
            vale_alimentacao=bcu_item.vale_alimentacao,
            plano_saude=bcu_item.plano_saude,
            ferramentas_val=bcu_item.ferramentas_val,
            seguro_vida=bcu_item.seguro_vida,
            abono_ferias=bcu_item.abono_ferias,
            uniforme_val=bcu_item.uniforme_val,
            epi_val=bcu_item.epi_val,
            periculosidade_insalubridade=bcu_item.periculosidade_insalubridade,
            mobilizacao=bcu_item.mobilizacao,
            custo_mensal=total,
            valor_bcu_snapshot=total,
        )
        self.db.add(pc_item)
        await self.db.flush()
        return {
            "id": str(pc_item.id),
            "tipo": "mao_obra",
            "codigo": pc_item.codigo_origem or "",
            "descricao": pc_item.descricao_funcao,
            "unidade_medida": "mês",
            "quantidade": int(qtd),
            "valor_unitario": float(total),
            "valor_total": float(total * qtd),
        }

    async def adicionar_epi(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: int,
    ) -> dict:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        bcu_item = (
            await self.db.execute(select(BcuEpiItem).where(BcuEpiItem.id == bcu_item_id))
        ).scalar_one_or_none()
        if not bcu_item:
            raise ValueError("EPI não encontrado na base")

        total = _total_epi(bcu_item)
        qtd = max(1, int(quantidade))
        pc_item = PropostaPcEpi(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            epi=bcu_item.epi,
            codigo_origem=bcu_item.codigo_origem,
            unidade=bcu_item.unidade,
            quantidade=qtd,
            custo_unitario=bcu_item.custo_unitario,
            vida_util_meses=bcu_item.vida_util_meses,
            valor_bcu_snapshot=total,
        )
        self.db.add(pc_item)
        await self.db.flush()
        return {
            "id": str(pc_item.id),
            "tipo": "epi",
            "codigo": pc_item.codigo_origem or "",
            "descricao": pc_item.epi,
            "unidade_medida": pc_item.unidade or "un",
            "quantidade": int(qtd),
            "valor_unitario": float(total),
            "valor_total": float(total * qtd),
        }

    async def adicionar_equipamento(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: int,
    ) -> dict:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        bcu_item = (
            await self.db.execute(select(BcuEquipamentoItem).where(BcuEquipamentoItem.id == bcu_item_id))
        ).scalar_one_or_none()
        if not bcu_item:
            raise ValueError("Equipamento não encontrado na base")

        total = _total_equipamento(bcu_item)
        qtd = max(1, int(quantidade))
        pc_item = PropostaPcEquipamento(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            equipamento=bcu_item.equipamento,
            codigo=bcu_item.codigo,
            codigo_origem=bcu_item.codigo_origem,
            combustivel_utilizado=bcu_item.combustivel_utilizado,
            consumo_l_h=bcu_item.consumo_l_h,
            aluguel_r_h=bcu_item.aluguel_r_h,
            combustivel_r_h=bcu_item.combustivel_r_h,
            mao_obra_r_h=bcu_item.mao_obra_r_h,
            hora_produtiva=total,
            hora_improdutiva=bcu_item.hora_improdutiva,
            mes=bcu_item.mes,
            aluguel_mensal=bcu_item.aluguel_mensal,
            quantidade=qtd,
            valor_bcu_snapshot=total,
        )
        self.db.add(pc_item)
        await self.db.flush()
        return {
            "id": str(pc_item.id),
            "tipo": "equipamento",
            "codigo": pc_item.codigo_origem or "",
            "descricao": pc_item.equipamento,
            "unidade_medida": "h",
            "quantidade": int(qtd),
            "valor_unitario": float(total),
            "valor_total": float(total * qtd),
        }

    async def adicionar_ferramenta(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: int,
    ) -> dict:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        bcu_item = (
            await self.db.execute(select(BcuFerramentaItem).where(BcuFerramentaItem.id == bcu_item_id))
        ).scalar_one_or_none()
        if not bcu_item:
            raise ValueError("Ferramenta não encontrada na base")

        total = _total_ferramenta(bcu_item)
        qtd = max(1, int(quantidade))
        pc_item = PropostaPcFerramenta(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            descricao=bcu_item.descricao,
            codigo_origem=bcu_item.codigo_origem,
            item=bcu_item.item,
            unidade=bcu_item.unidade,
            quantidade=qtd,
            preco=bcu_item.preco,
            preco_total=total * qtd,
            valor_bcu_snapshot=total,
        )
        self.db.add(pc_item)
        await self.db.flush()
        return {
            "id": str(pc_item.id),
            "tipo": "ferramenta",
            "codigo": pc_item.codigo_origem or "",
            "descricao": pc_item.descricao,
            "unidade_medida": pc_item.unidade or "un",
            "quantidade": int(qtd),
            "valor_unitario": float(total),
            "valor_total": float(total * qtd),
        }

    # ── Remover ──────────────────────────────────────────────────────────

    async def remover_item_unificado(self, proposta_id: UUID, item_id: UUID) -> bool:
        """Remove um item BCU detectando automaticamente em qual tabela PC ele está."""
        for model in (PropostaPcMaoObra, PropostaPcEpi, PropostaPcEquipamento, PropostaPcFerramenta):
            obj = (
                await self.db.execute(
                    select(model).where(model.id == item_id, model.proposta_id == proposta_id)
                )
            ).scalar_one_or_none()
            if obj:
                await self.db.delete(obj)
                await self.db.flush()
                return True
        return False
