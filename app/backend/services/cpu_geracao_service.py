from decimal import Decimal
from uuid import UUID

from backend.core.exceptions import NotFoundError
from backend.models.enums import StatusMatch, StatusProposta
from backend.models.proposta import PropostaItem
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.pq_item_repository import PqItemRepository
from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.services.cpu_custo_service import CpuCustoService
from backend.services.cpu_explosao_service import CpuExplosaoService

_ELIGIBLE_MATCH_STATUS = {
    StatusMatch.SUGERIDO,
    StatusMatch.CONFIRMADO,
    StatusMatch.MANUAL,
}


class CpuGeracaoService:
    def __init__(self, db) -> None:
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.pq_item_repo = PqItemRepository(db)
        self.proposta_item_repo = PropostaItemRepository(db)
        self.comp_repo = PropostaItemComposicaoRepository(db)
        self.base_repo = BaseTcpoRepository(db)
        self.proprios_repo = ItensPropiosRepository(db)
        self.explosao_svc = CpuExplosaoService(db)

    async def gerar_cpu_para_proposta(
        self,
        proposta_id: UUID,
        pc_cabecalho_id: UUID | None = None,
        percentual_bdi: Decimal = Decimal("0"),
    ) -> dict:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        proposta_itens = await self._rebuild_proposta_itens(proposta_id, pc_cabecalho_id)
        custo_svc = CpuCustoService(self.db, pc_cabecalho_id)

        total_direto = Decimal("0")
        total_indireto = Decimal("0")
        resultados = {"processados": 0, "erros": 0}

        for item in proposta_itens:
            try:
                composicoes = await self.explosao_svc.explodir_proposta_item(item)
                await custo_svc.calcular_custos(composicoes)
                if composicoes:
                    await self.comp_repo.create_batch(composicoes)

                custos = self._agrupar_custos(composicoes)
                custo_direto_unitario = sum((c.custo_total_insumo or Decimal("0")) for c in composicoes)
                custo_indireto_unitario = custo_direto_unitario * percentual_bdi
                preco_unitario = custo_direto_unitario + custo_indireto_unitario
                preco_total = preco_unitario * item.quantidade

                item.custo_material_unitario = custos["material"]
                item.custo_mao_obra_unitario = custos["mao_obra"]
                item.custo_equipamento_unitario = custos["equipamento"]
                item.custo_direto_unitario = custo_direto_unitario
                item.percentual_indireto = percentual_bdi
                item.custo_indireto_unitario = custo_indireto_unitario
                item.preco_unitario = preco_unitario
                item.preco_total = preco_total
                item.composicao_fonte = composicoes[0].fonte_custo if composicoes else "sem_composicao"

                total_direto += custo_direto_unitario * item.quantidade
                total_indireto += custo_indireto_unitario * item.quantidade
                resultados["processados"] += 1
            except Exception:
                resultados["erros"] += 1

        proposta.total_direto = total_direto
        proposta.total_indireto = total_indireto
        proposta.total_geral = total_direto + total_indireto
        proposta.pc_cabecalho_id = pc_cabecalho_id
        proposta.status = StatusProposta.CPU_GERADA
        await self.db.flush()

        return {
            "proposta_id": str(proposta_id),
            "total_direto": float(total_direto),
            "total_indireto": float(total_indireto),
            "total_geral": float(proposta.total_geral),
            "detalhe": resultados,
        }

    async def listar_cpu_itens(self, proposta_id: UUID) -> list[PropostaItem]:
        return await self.proposta_item_repo.list_by_proposta(proposta_id)

    async def _rebuild_proposta_itens(self, proposta_id: UUID, pc_cabecalho_id: UUID | None) -> list[PropostaItem]:
        await self.proposta_item_repo.delete_by_proposta(proposta_id)
        pq_items = await self.pq_item_repo.list_by_proposta(proposta_id)

        proposta_itens: list[PropostaItem] = []
        ordem = 0
        for pq_item in pq_items:
            if (
                pq_item.servico_match_id is None
                or pq_item.servico_match_tipo is None
                or pq_item.match_status not in _ELIGIBLE_MATCH_STATUS
            ):
                continue

            snapshot = await self.base_repo.get_by_id(pq_item.servico_match_id)
            if snapshot is None:
                snapshot = await self.proprios_repo.get_active_by_id(pq_item.servico_match_id)
            if snapshot is None:
                continue

            proposta_itens.append(
                PropostaItem(
                    proposta_id=proposta_id,
                    pq_item_id=pq_item.id,
                    servico_id=snapshot.id,
                    servico_tipo=pq_item.servico_match_tipo,
                    codigo=snapshot.codigo_origem,
                    descricao=snapshot.descricao,
                    unidade_medida=snapshot.unidade_medida,
                    quantidade=pq_item.quantidade_original or Decimal("1"),
                    composicao_fonte="match_inteligente",
                    pc_cabecalho_id=pc_cabecalho_id,
                    ordem=ordem,
                )
            )
            ordem += 1

        if proposta_itens:
            await self.proposta_item_repo.create_batch(proposta_itens)
        return proposta_itens

    def _agrupar_custos(self, composicoes):
        material = Decimal("0")
        mao_obra = Decimal("0")
        equipamento = Decimal("0")

        for comp in composicoes:
            valor = comp.custo_total_insumo or Decimal("0")
            if comp.tipo_recurso and comp.tipo_recurso.value == "MO":
                mao_obra += valor
            elif comp.tipo_recurso and comp.tipo_recurso.value == "EQUIPAMENTO":
                equipamento += valor
            else:
                material += valor

        return {"material": material, "mao_obra": mao_obra, "equipamento": equipamento}

