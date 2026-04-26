from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from backend.models.base_tcpo import BaseTcpo
from backend.models.composicao_base import ComposicaoBase
from backend.models.itens_proprios import ItemProprio
from backend.models.proposta import PropostaItem, PropostaItemComposicao
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
from backend.repositories.versao_composicao_repository import VersaoComposicaoRepository


class CpuExplosaoService:
    def __init__(self, db) -> None:
        self.db = db
        self.base_repo = BaseTcpoRepository(db)
        self.proprios_repo = ItensPropiosRepository(db)
        self.versao_repo = VersaoComposicaoRepository(db)

    def _assert_nivel_permitido(self, nivel: int) -> None:
        if nivel > 5:
            raise ValueError(
                f"Profundidade maxima de explosao atingida (nivel {nivel}). Limite: 5."
            )

    async def _listar_filhos_diretos(
        self, servico_id: UUID
    ) -> list[dict]:
        """Retorna apenas os filhos diretos (nível 1) de um serviço."""
        snapshot = await self.base_repo.get_by_id(servico_id)
        is_tcpo = snapshot is not None

        if not is_tcpo:
            snapshot = await self.proprios_repo.get_active_by_id(servico_id)

        if snapshot is None:
            return []

        filhos: list[dict] = []

        if is_tcpo:
            result = await self.db.execute(
                select(ComposicaoBase).where(ComposicaoBase.servico_pai_id == servico_id)
            )
            for comp in result.scalars().all():
                filhos.append({
                    "insumo_id": comp.insumo_filho_id,
                    "quantidade_consumo": comp.quantidade_consumo,
                    "unidade_medida": comp.unidade_medida,
                    "is_base": True,
                })
        else:
            versao = await self.versao_repo.get_versao_ativa(servico_id)
            if versao:
                for comp in versao.itens:
                    if comp.insumo_base_id is not None:
                        filhos.append({
                            "insumo_id": comp.insumo_base_id,
                            "quantidade_consumo": comp.quantidade_consumo,
                            "unidade_medida": comp.unidade_medida,
                            "is_base": True,
                        })
                    elif comp.insumo_proprio_id is not None:
                        filhos.append({
                            "insumo_id": comp.insumo_proprio_id,
                            "quantidade_consumo": comp.quantidade_consumo,
                            "unidade_medida": comp.unidade_medida,
                            "is_base": False,
                        })

        return filhos

    async def _verificar_e_marcar_sub_composicao(
        self, composicao: PropostaItemComposicao
    ) -> None:
        insumo_id = composicao.insumo_base_id or composicao.insumo_proprio_id
        if not insumo_id:
            return
        filhos = await self._listar_filhos_diretos(insumo_id)
        if filhos:
            composicao.e_composicao = True

    async def explodir_proposta_item(self, proposta_item: PropostaItem) -> list[PropostaItemComposicao]:
        filhos_diretos = await self._listar_filhos_diretos(proposta_item.servico_id)

        composicoes: list[PropostaItemComposicao] = []
        for filho in filhos_diretos:
            snapshot = await self._resolve_snapshot(filho["insumo_id"])
            if snapshot is None:
                continue
            composicao = self._build_composicao(
                proposta_item_id=proposta_item.id,
                snapshot=snapshot,
                quantidade_consumo=filho["quantidade_consumo"] * proposta_item.quantidade,
                unidade_medida=filho["unidade_medida"],
            )
            await self._verificar_e_marcar_sub_composicao(composicao)
            composicoes.append(composicao)

        if composicoes:
            return composicoes

        snapshot = await self._resolve_root_snapshot(proposta_item)
        if snapshot is None:
            return []

        composicao = self._build_composicao(
            proposta_item_id=proposta_item.id,
            snapshot=snapshot,
            quantidade_consumo=Decimal("1") * proposta_item.quantidade,
            unidade_medida=proposta_item.unidade_medida,
        )
        await self._verificar_e_marcar_sub_composicao(composicao)
        return [composicao]

    async def _resolve_root_snapshot(self, proposta_item: PropostaItem) -> BaseTcpo | ItemProprio | None:
        snapshot = await self.base_repo.get_by_id(proposta_item.servico_id)
        if snapshot is not None:
            return snapshot
        return await self.proprios_repo.get_active_by_id(proposta_item.servico_id)

    async def _resolve_snapshot(self, insumo_id):
        snapshot = await self.base_repo.get_by_id(insumo_id)
        if snapshot is not None:
            return snapshot
        return await self.proprios_repo.get_active_by_id(insumo_id)

    def _build_composicao(
        self,
        proposta_item_id,
        snapshot: BaseTcpo | ItemProprio,
        quantidade_consumo: Decimal,
        unidade_medida: str,
        pai_composicao_id=None,
        nivel=0,
    ) -> PropostaItemComposicao:
        is_base = isinstance(snapshot, BaseTcpo)
        custo_unitario = snapshot.custo_base if is_base else snapshot.custo_unitario
        fonte_custo = "custo_base" if is_base else "custo_item_proprio"
        return PropostaItemComposicao(
            proposta_item_id=proposta_item_id,
            insumo_base_id=snapshot.id if is_base else None,
            insumo_proprio_id=None if is_base else snapshot.id,
            descricao_insumo=snapshot.descricao,
            unidade_medida=unidade_medida or snapshot.unidade_medida,
            quantidade_consumo=quantidade_consumo,
            custo_unitario_insumo=custo_unitario,
            custo_total_insumo=(custo_unitario or Decimal("0")) * quantidade_consumo,
            tipo_recurso=snapshot.tipo_recurso,
            fonte_custo=fonte_custo,
            pai_composicao_id=pai_composicao_id,
            nivel=nivel,
            e_composicao=False,
            composicao_explodida=False,
        )

    async def explodir_sub_composicao(
        self,
        proposta_id: UUID,
        composicao_id: UUID,
    ) -> list[PropostaItemComposicao]:
        repo = PropostaItemComposicaoRepository(self.db)
        composicao = await repo.get_by_id(composicao_id)

        if composicao is None:
            raise ValueError(f"Composicao {composicao_id} nao encontrada.")
        if composicao.composicao_explodida:
            raise ValueError("Sub-composicao ja foi explodida.")
        if not composicao.e_composicao:
            raise ValueError("Este insumo nao possui composicao propria.")

        proximo_nivel = composicao.nivel + 1
        self._assert_nivel_permitido(proximo_nivel)

        insumo_id = composicao.insumo_base_id or composicao.insumo_proprio_id
        if not insumo_id:
            raise ValueError("Composicao nao possui insumo associado.")

        filhos_diretos = await self._listar_filhos_diretos(insumo_id)

        filhos: list[PropostaItemComposicao] = []
        for filho in filhos_diretos:
            snapshot = await self._resolve_snapshot(filho["insumo_id"])
            if snapshot is None:
                continue
            child = self._build_composicao(
                proposta_item_id=composicao.proposta_item_id,
                snapshot=snapshot,
                quantidade_consumo=filho["quantidade_consumo"] * composicao.quantidade_consumo,
                unidade_medida=filho["unidade_medida"],
                pai_composicao_id=composicao.id,
                nivel=proximo_nivel,
            )
            await self._verificar_e_marcar_sub_composicao(child)
            self.db.add(child)
            filhos.append(child)

        composicao.composicao_explodida = True
        await self.db.flush()
        return filhos
