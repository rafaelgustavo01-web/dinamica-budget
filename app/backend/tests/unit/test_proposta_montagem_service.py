import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.enums import StatusProposta
from backend.models.proposta import Proposta, PropostaItem, PropostaItemComposicao
from backend.models.proposta_recurso_extra import PropostaRecursoAlocacao, PropostaRecursoExtra
from backend.services.proposta_montagem_service import PropostaMontagemService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def svc(mock_db):
    return PropostaMontagemService(mock_db)


@pytest.mark.asyncio
async def test_rebuild_updates_totals(svc, mock_db):
    proposta_id = uuid.uuid4()

    # Mock proposal
    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.status = StatusProposta.CPU_GERADA
    proposta.total_direto = None
    proposta.total_indireto = None
    proposta.total_geral = None
    proposta.cpu_desatualizada = True
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)

    # Mock items
    item = MagicMock()
    item.id = uuid.uuid4()
    item.quantidade = Decimal("2")
    item.percentual_indireto = Decimal("0.10")  # 10%
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])

    # Mock compositions
    comp = MagicMock()
    comp.id = uuid.uuid4()
    comp.custo_total_insumo = Decimal("100")
    comp.tipo_recurso = MagicMock()
    comp.tipo_recurso.value = "MO"
    svc.comp_repo.list_by_proposta_items_batch = AsyncMock(return_value={item.id: [comp]})

    # Mock extra resources (no allocations)
    svc.recurso_repo.list_by_proposta = AsyncMock(return_value=[])

    # Mock resumo repo
    svc.resumo_repo.delete_by_proposta = AsyncMock()
    svc.resumo_repo.create_batch = AsyncMock()

    resultado = await svc.rebuild(proposta_id)

    assert resultado["proposta_id"] == str(proposta_id)
    assert resultado["total_direto"] == 200.0  # 100 * 2
    assert resultado["total_indireto"] == 20.0  # 200 * 0.10
    assert resultado["total_geral"] == 220.0
    assert resultado["cpu_desatualizada"] is False
    assert resultado["itens_processados"] == 1

    # Verify proposal was updated
    assert proposta.total_direto == Decimal("200")
    assert proposta.total_indireto == Decimal("20")
    assert proposta.total_geral == Decimal("220")
    assert proposta.cpu_desatualizada is False


@pytest.mark.asyncio
async def test_rebuild_with_extra_resources(svc, mock_db):
    proposta_id = uuid.uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.status = StatusProposta.CPU_GERADA
    proposta.cpu_desatualizada = True
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)

    item = MagicMock()
    item.id = uuid.uuid4()
    item.quantidade = Decimal("1")
    item.percentual_indireto = Decimal("0")
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])

    comp = MagicMock()
    comp.id = uuid.uuid4()
    comp.custo_total_insumo = Decimal("50")
    comp.tipo_recurso = MagicMock()
    comp.tipo_recurso.value = "INSUMO"
    svc.comp_repo.list_by_proposta_items_batch = AsyncMock(return_value={item.id: [comp]})

    # Mock extra resource with allocation
    recurso = MagicMock()
    recurso.custo_unitario = Decimal("25")
    recurso.tipo_recurso = "OUTROS"
    alocacao = MagicMock()
    alocacao.composicao_id = comp.id
    alocacao.quantidade_consumo = Decimal("2")
    recurso.alocacoes = [alocacao]
    svc.recurso_repo.list_by_proposta = AsyncMock(return_value=[recurso])

    svc.resumo_repo.delete_by_proposta = AsyncMock()
    svc.resumo_repo.create_batch = AsyncMock()

    resultado = await svc.rebuild(proposta_id)

    # Base: 50 + extra: 25*2 = 50, total = 100
    assert resultado["total_direto"] == 100.0
    assert resultado["total_geral"] == 100.0


@pytest.mark.asyncio
async def test_rebuild_rejects_invalid_status(svc, mock_db):
    proposta_id = uuid.uuid4()
    proposta = MagicMock()
    proposta.status = StatusProposta.APROVADA
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)

    from backend.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await svc.rebuild(proposta_id)


@pytest.mark.asyncio
async def test_rebuild_rejects_no_items(svc, mock_db):
    proposta_id = uuid.uuid4()
    proposta = MagicMock()
    proposta.status = StatusProposta.RASCUNHO
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[])

    from backend.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        await svc.rebuild(proposta_id)
