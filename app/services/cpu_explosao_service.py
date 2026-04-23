from decimal import Decimal

from app.models.base_tcpo import BaseTcpo
from app.models.itens_proprios import ItemProprio
from app.models.proposta import PropostaItem, PropostaItemComposicao
from app.repositories.base_tcpo_repository import BaseTcpoRepository
from app.repositories.itens_proprios_repository import ItensPropiosRepository
from app.services.servico_catalog_service import servico_catalog_service


class CpuExplosaoService:
    def __init__(self, db) -> None:
        self.db = db
        self.base_repo = BaseTcpoRepository(db)
        self.proprios_repo = ItensPropiosRepository(db)

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
            composicoes.append(
                self._build_composicao(
                    proposta_item_id=proposta_item.id,
                    snapshot=snapshot,
                    quantidade_consumo=item.quantidade_consumo,
                    unidade_medida=item.unidade_medida,
                )
            )

        if composicoes:
            return composicoes

        snapshot = await self._resolve_root_snapshot(proposta_item)
        if snapshot is None:
            return []

        return [
            self._build_composicao(
                proposta_item_id=proposta_item.id,
                snapshot=snapshot,
                quantidade_consumo=Decimal("1"),
                unidade_medida=proposta_item.unidade_medida,
            )
        ]

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
        )
