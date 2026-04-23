from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.enums import StatusMatch, StatusProposta, TipoServicoMatch
from app.models.proposta import PqItem
from app.services.cpu_geracao_service import CpuGeracaoService


@pytest.mark.asyncio
async def test_gerar_cpu_sem_composicao():
    svc = CpuGeracaoService(AsyncMock())

    proposta_id = uuid4()
    proposta = MagicMock()
    proposta.id = proposta_id

    pq_item = PqItem(
        id=uuid4(),
        proposta_id=proposta_id,
        descricao_original="Escavacao",
        quantidade_original=Decimal("1"),
        match_status=StatusMatch.CONFIRMADO,
        servico_match_id=uuid4(),
        servico_match_tipo=TipoServicoMatch.BASE_TCPO,
    )

    snapshot = MagicMock()
    snapshot.id = pq_item.servico_match_id
    snapshot.codigo_origem = "001"
    snapshot.descricao = "Escavacao"
    snapshot.unidade_medida = "m2"

    with patch.object(svc.proposta_repo, "get_by_id", AsyncMock(return_value=proposta)):
        with patch.object(svc.pq_item_repo, "list_by_proposta", AsyncMock(return_value=[pq_item])):
            with patch.object(svc.proposta_item_repo, "delete_by_proposta", AsyncMock()):
                with patch.object(svc.proposta_item_repo, "create_batch", AsyncMock(side_effect=lambda items: items)):
                    with patch.object(svc.base_repo, "get_by_id", AsyncMock(return_value=snapshot)):
                        with patch.object(svc.explosao_svc, "explodir_proposta_item", AsyncMock(return_value=[])):
                            resultado = await svc.gerar_cpu_para_proposta(proposta_id)

    assert resultado["detalhe"]["processados"] == 1
    assert proposta.status == StatusProposta.CPU_GERADA
    assert resultado["total_geral"] == 0.0


@pytest.mark.asyncio
async def test_gerar_cpu_com_composicao_aplica_bdi():
    svc = CpuGeracaoService(AsyncMock())

    proposta_id = uuid4()
    proposta = MagicMock()
    proposta.id = proposta_id

    pq_item = PqItem(
        id=uuid4(),
        proposta_id=proposta_id,
        descricao_original="Concreto",
        quantidade_original=Decimal("2"),
        match_status=StatusMatch.MANUAL,
        servico_match_id=uuid4(),
        servico_match_tipo=TipoServicoMatch.BASE_TCPO,
    )

    snapshot = MagicMock()
    snapshot.id = pq_item.servico_match_id
    snapshot.codigo_origem = "002"
    snapshot.descricao = "Concreto"
    snapshot.unidade_medida = "m3"

    comp = MagicMock()
    comp.custo_total_insumo = Decimal("100")
    comp.tipo_recurso = None
    comp.fonte_custo = "custo_base"

    with patch.object(svc.proposta_repo, "get_by_id", AsyncMock(return_value=proposta)):
        with patch.object(svc.pq_item_repo, "list_by_proposta", AsyncMock(return_value=[pq_item])):
            with patch.object(svc.proposta_item_repo, "delete_by_proposta", AsyncMock()):
                with patch.object(svc.proposta_item_repo, "create_batch", AsyncMock(side_effect=lambda items: items)):
                    with patch.object(svc.base_repo, "get_by_id", AsyncMock(return_value=snapshot)):
                        with patch.object(svc.explosao_svc, "explodir_proposta_item", AsyncMock(return_value=[comp])):
                            with patch("app.services.cpu_geracao_service.CpuCustoService.calcular_custos", new=AsyncMock()):
                                with patch.object(svc.comp_repo, "create_batch", AsyncMock()):
                                    resultado = await svc.gerar_cpu_para_proposta(
                                        proposta_id,
                                        percentual_bdi=Decimal("0.1"),
                                    )

    assert resultado["detalhe"]["processados"] == 1
    assert resultado["total_geral"] == 220.0
