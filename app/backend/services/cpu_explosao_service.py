from decimal import Decimal
from uuid import UUID

from backend.models.base_tcpo import BaseTcpo
from backend.models.itens_proprios import ItemProprio
from backend.models.proposta import PropostaItem, PropostaItemComposicao
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
from backend.services.servico_catalog_service import servico_catalog_service


class CpuExplosaoService:
    def __init__(self, db) -> None:
        self.db = db
        self.base_repo = BaseTcpoRepository(db)
        self.proprios_repo = ItensPropiosRepository(db)

    def _assert_nivel_permitido(self, nivel: int) -> None:
        if nivel > 5:
            raise ValueError(
                f"Profundidade maxima de explosao atingida (nivel {nivel}). Limite: 5."
            )

    async def _verificar_e_marcar_sub_composicao(
        self, composicao: PropostaItemComposicao
    ) -> None:
        if not composicao.insumo_base_id:
            return
        try:
            resultado = await servico_catalog_service.explode_composicao(
                servico_id=composicao.insumo_base_id,
                db=self.db,
            )
            if resultado.itens:
                composicao.e_composicao = True
        except Exception:
            pass

    async def explodir_proposta_item(self, proposta_item: PropostaItem) -> list[PropostaItemComposicao]:
        resultado = await servico_catalog_service.explode_composicao(
            servico_id=proposta_item.servico_id,
            db=self.db,
        )

        composicoes: list[PropostaItemComposicao] = []
        for item in resultado.itens:
            snapshot = await self._resolve_snapshot(item.insumo_filho_id)
            if snapshot is None:
                continue
            composicao = self._build_composicao(
                proposta_item_id=proposta_item.id,
                snapshot=snapshot,
                quantidade_consumo=item.quantidade_consumo,
                unidade_medida=item.unidade_medida,
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
            quantidade_consumo=Decimal("1"),
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
            pai_composicao_id=None,
            nivel=0,
            e_composicao=False,
            composicao_explodida=False,
        )

    async def explodir_sub_composicao(
        self,
        proposta_id: UUID,
        composicao_id: UUID,
    ) -> list[PropostaItemComposicao]:
        import uuid as uuid_mod

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

        resultado = await servico_catalog_service.explode_composicao(
            servico_id=composicao.insumo_base_id,
            db=self.db,
        )

        filhos: list[PropostaItemComposicao] = []
        for insumo in resultado.itens:
            filho = PropostaItemComposicao(
                id=uuid_mod.uuid4(),
                proposta_item_id=composicao.proposta_item_id,
                insumo_base_id=insumo.insumo_filho_id,
                insumo_proprio_id=None,
                descricao_insumo=insumo.descricao_filho or "",
                unidade_medida=insumo.unidade_medida or "UN",
                quantidade_consumo=insumo.quantidade_consumo * composicao.quantidade_consumo,
                tipo_recurso=None,
                fonte_custo="base_tcpo",
                pai_composicao_id=composicao.id,
                nivel=proximo_nivel,
                e_composicao=False,
                composicao_explodida=False,
            )
            await self._verificar_e_marcar_sub_composicao(filho)
            self.db.add(filho)
            filhos.append(filho)

        composicao.composicao_explodida = True
        await self.db.flush()
        return filhos

