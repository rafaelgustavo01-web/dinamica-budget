from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.schemas.proposta import (
    ComposicaoDetalheResponse,
    RecalcularBdiRequest,
    RecalcularBdiResponse,
)


def test_composicao_detalhe_response_schema():
    data = {
        "id": uuid4(),
        "proposta_item_id": uuid4(),
        "descricao_insumo": "Pedreiro",
        "unidade_medida": "h",
        "quantidade_consumo": Decimal("8.0"),
        "custo_unitario_insumo": Decimal("45.00"),
        "custo_total_insumo": Decimal("360.00"),
        "tipo_recurso": "MO",
        "nivel": 1,
        "e_composicao": False,
        "fonte_custo": "pc_tabela",
    }
    resp = ComposicaoDetalheResponse(**data)
    assert resp.descricao_insumo == "Pedreiro"
    assert resp.custo_total_insumo == Decimal("360.00")


def test_recalcular_bdi_request_schema():
    req = RecalcularBdiRequest(percentual_bdi=Decimal("28.5"))
    assert req.percentual_bdi == Decimal("28.5")


def test_recalcular_bdi_response_schema():
    resp = RecalcularBdiResponse(
        proposta_id=str(uuid4()),
        percentual_bdi=Decimal("28.5"),
        total_direto=Decimal("100000.00"),
        total_indireto=Decimal("28500.00"),
        total_geral=Decimal("128500.00"),
        itens_recalculados=15,
    )
    assert resp.itens_recalculados == 15


@pytest.mark.asyncio
async def test_list_composicoes_by_proposta_item():
    from backend.repositories.proposta_item_composicao_repository import (
        PropostaItemComposicaoRepository,
    )
    from backend.models.proposta import PropostaItemComposicao

    comp = MagicMock(spec=PropostaItemComposicao)
    comp.proposta_item_id = uuid4()

    db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [comp]
    db.execute = AsyncMock(return_value=mock_result)

    repo = PropostaItemComposicaoRepository(db)
    result = await repo.list_by_proposta_item(comp.proposta_item_id)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_recalcular_bdi_atualiza_totais():
    from backend.services.cpu_geracao_service import CpuGeracaoService
    from backend.models.proposta import Proposta, PropostaItem

    proposta = MagicMock(spec=Proposta)
    proposta.id = uuid4()
    proposta.cliente_id = uuid4()
    proposta.total_direto = Decimal("100000")
    proposta.total_indireto = Decimal("0")
    proposta.total_geral = Decimal("100000")

    item1 = MagicMock(spec=PropostaItem)
    item1.custo_direto_unitario = Decimal("500")
    item1.quantidade = Decimal("10")
    item1.percentual_indireto = Decimal("0")
    item1.custo_indireto_unitario = Decimal("0")
    item1.preco_unitario = Decimal("500")
    item1.preco_total = Decimal("5000")

    db = MagicMock()
    db.flush = AsyncMock()

    svc = CpuGeracaoService.__new__(CpuGeracaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.proposta_item_repo = MagicMock()
    svc.proposta_item_repo.list_by_proposta = AsyncMock(return_value=[item1])

    result = await svc.recalcular_bdi(proposta.id, Decimal("20"))

    assert item1.percentual_indireto == Decimal("20") / Decimal("100")
    expected_indireto = Decimal("500") * (Decimal("20") / Decimal("100")) * Decimal("10")
    assert result["total_indireto"] == float(expected_indireto)
    assert result["itens_recalculados"] == 1


@pytest.mark.asyncio
async def test_listar_composicoes_item_retorna_lista():
    from backend.services.cpu_geracao_service import CpuGeracaoService
    from backend.models.proposta import PropostaItem, PropostaItemComposicao

    item = MagicMock(spec=PropostaItem)
    item.id = uuid4()
    item.proposta_id = uuid4()

    comp = MagicMock(spec=PropostaItemComposicao)
    comp.proposta_item_id = item.id

    db = MagicMock()
    svc = CpuGeracaoService.__new__(CpuGeracaoService)
    svc.db = db
    svc.proposta_item_repo = MagicMock()
    svc.proposta_item_repo.get_by_id = AsyncMock(return_value=item)
    svc.comp_repo = MagicMock()
    svc.comp_repo.list_by_proposta_item = AsyncMock(return_value=[comp])

    result = await svc.listar_composicoes_item(item.id)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_endpoint_composicoes_retorna_lista():
    from backend.api.v1.endpoints.cpu_geracao import listar_composicoes_proposta_item
    from backend.models.proposta import PropostaItemComposicao

    proposta = MagicMock()
    proposta.cliente_id = uuid4()
    composicao = MagicMock(spec=PropostaItemComposicao)
    composicao.id = uuid4()
    composicao.proposta_item_id = uuid4()
    composicao.descricao_insumo = "Pedreiro"
    composicao.unidade_medida = "h"
    composicao.quantidade_consumo = Decimal("8")
    composicao.custo_unitario_insumo = Decimal("45")
    composicao.custo_total_insumo = Decimal("360")
    composicao.tipo_recurso = "MO"
    composicao.nivel = 1
    composicao.e_composicao = False
    composicao.fonte_custo = "pc_tabela"

    with (
        patch("backend.api.v1.endpoints.cpu_geracao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.cpu_geracao.CpuGeracaoService") as MockSvc,
        patch("backend.api.v1.endpoints.cpu_geracao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.listar_composicoes_item = AsyncMock(return_value=[composicao])
        db = MagicMock()
        user = MagicMock()
        result = await listar_composicoes_proposta_item(
            proposta_id=uuid4(),
            item_id=composicao.proposta_item_id,
            current_user=user,
            db=db,
        )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_endpoint_recalcular_bdi():
    from backend.api.v1.endpoints.cpu_geracao import recalcular_bdi_proposta
    from backend.schemas.proposta import RecalcularBdiRequest

    proposta = MagicMock()
    proposta.cliente_id = uuid4()
    proposta_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.cpu_geracao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.cpu_geracao.CpuGeracaoService") as MockSvc,
        patch("backend.api.v1.endpoints.cpu_geracao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.recalcular_bdi = AsyncMock(return_value={
            "proposta_id": str(proposta_id),
            "percentual_bdi": 25.0,
            "total_direto": 100000.0,
            "total_indireto": 25000.0,
            "total_geral": 125000.0,
            "itens_recalculados": 10,
        })
        db = MagicMock()
        db.commit = AsyncMock()
        user = MagicMock()
        req = RecalcularBdiRequest(percentual_bdi=Decimal("25"))
        result = await recalcular_bdi_proposta(
            proposta_id=proposta_id,
            body=req,
            current_user=user,
            db=db,
        )
    assert result.itens_recalculados == 10
