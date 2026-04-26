import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.enums import TipoRecurso, StatusMatch, StatusHomologacao
from backend.models.proposta import PropostaItemComposicao, PropostaResumoRecurso, PropostaItem
from backend.services.busca_service import BuscaService
from backend.services.cpu_geracao_service import CpuGeracaoService
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.proposta_resumo_recurso_repository import PropostaResumoRecursoRepository

@pytest.mark.asyncio
async def test_busca_fase0_1_codigo_exato_proprio_hit():
    mock_db = AsyncMock()
    svc = BuscaService()
    
    cliente_id = uuid.uuid4()
    item_p = MagicMock()
    item_p.id = uuid.uuid4()
    item_p.codigo_origem = "PROP001"
    item_p.descricao = "Item Proprio"
    item_p.unidade_medida = "UN"
    item_p.custo_unitario = Decimal("150.00")
    item_p.status_homologacao = StatusHomologacao.APROVADO

    with patch.object(ItensPropiosRepository, "get_by_codigo_scoped", return_value=item_p):
        result = await svc._fase0_codigo_exato("PROP001", cliente_id, AsyncMock(), ItensPropiosRepository(mock_db))
        
    assert result is not None
    assert len(result) == 1
    assert result[0].origem_match == "CODIGO_EXATO_PROPRIO"
    assert result[0].codigo_origem == "PROP001"
    assert result[0].custo_unitario == 150.0

@pytest.mark.asyncio
async def test_busca_fase0_1_codigo_exato_tcpo_hit():
    mock_db = AsyncMock()
    svc = BuscaService()
    
    item_b = MagicMock()
    item_b.id = uuid.uuid4()
    item_b.codigo_origem = "TCPO001"
    item_b.descricao = "Item TCPO"
    item_b.unidade_medida = "m2"
    item_b.custo_base = Decimal("80.00")

    with patch.object(ItensPropiosRepository, "get_by_codigo_scoped", return_value=None):
        with patch.object(BaseTcpoRepository, "get_by_codigo", return_value=item_b):
            result = await svc._fase0_codigo_exato("TCPO001", uuid.uuid4(), BaseTcpoRepository(mock_db), ItensPropiosRepository(mock_db))
            
    assert result is not None
    assert len(result) == 1
    assert result[0].origem_match == "CODIGO_EXATO_TCPO"
    assert result[0].custo_unitario == 80.0

@pytest.mark.asyncio
async def test_cpu_atualizar_resumo_recursos_agregacao():
    mock_db = AsyncMock()
    svc = CpuGeracaoService(mock_db)
    
    proposta_id = uuid.uuid4()
    
    item1 = PropostaItem(quantidade=Decimal("10"))
    item2 = PropostaItem(quantidade=Decimal("5"))
    
    comp1 = PropostaItemComposicao(
        tipo_recurso=TipoRecurso.MO,
        custo_total_insumo=Decimal("50.00") # unitario na composicao
    )
    comp1.proposta_item = item1
    
    comp2 = PropostaItemComposicao(
        tipo_recurso=TipoRecurso.INSUMO,
        custo_total_insumo=Decimal("20.00")
    )
    comp2.proposta_item = item1
    
    comp3 = PropostaItemComposicao(
        tipo_recurso=TipoRecurso.MO,
        custo_total_insumo=Decimal("100.00")
    )
    comp3.proposta_item = item2
    
    composicoes = [comp1, comp2, comp3]
    percentual_bdi = Decimal("20") # 20%
    
    with patch.object(PropostaResumoRecursoRepository, "delete_by_proposta", return_value=None):
        with patch.object(PropostaResumoRecursoRepository, "create_batch", side_effect=lambda x: x) as mock_create:
            await svc._atualizar_resumo_recursos(proposta_id, composicoes, percentual_bdi)
            
            resumos = mock_create.call_args[0][0]
            
    assert len(resumos) == 2
    
    mo_resumo = next(r for r in resumos if r.tipo_recurso == "MO")
    # MO Total Direto: (50 * 10) + (100 * 5) = 500 + 500 = 1000
    assert mo_resumo.total_direto == Decimal("1000.00")
    assert mo_resumo.total_indireto == Decimal("200.00") # 20% of 1000
    assert mo_resumo.total_geral == Decimal("1200.00")
    
    insumo_resumo = next(r for r in resumos if r.tipo_recurso == "INSUMO")
    # INSUMO Total Direto: (20 * 10) = 200
    assert insumo_resumo.total_direto == Decimal("200.00")
    assert insumo_resumo.total_indireto == Decimal("40.00")
    assert insumo_resumo.total_geral == Decimal("240.00")
