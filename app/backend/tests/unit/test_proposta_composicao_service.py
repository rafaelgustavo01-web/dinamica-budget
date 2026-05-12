"""Tests for PropostaComposicaoService."""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.enums import StatusProposta, TipoRecurso
from backend.services.proposta_composicao_service import PropostaComposicaoService


@pytest.mark.asyncio
async def test_buscar_valores_proposta_success():
    """Test successful value search for a proposal."""
    proposta_id = uuid4()
    item_id = uuid4()
    comp_id = uuid4()

    # Mock proposta
    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.codigo = "PROP-001"
    proposta.status = StatusProposta.CPU_GERADA
    proposta.total_direto = Decimal("1000")
    proposta.total_indireto = Decimal("285")
    proposta.total_geral = Decimal("1285")

    # Mock item
    item = MagicMock()
    item.id = item_id
    item.codigo = "01"
    item.descricao = "Escavação"
    item.quantidade = Decimal("100")
    item.custo_direto_unitario = Decimal("10")
    item.custo_indireto_unitario = Decimal("2.85")
    item.preco_unitario = Decimal("12.85")
    item.preco_total = Decimal("1285")
    item.percentual_indireto = Decimal("0.285")

    # Mock composição
    comp = MagicMock()
    comp.id = comp_id
    comp.descricao_insumo = "Retroescavadeira"
    comp.tipo_recurso = TipoRecurso.EQUIPAMENTO
    comp.custo_total_insumo = Decimal("10")

    db = MagicMock()
    db.flush = AsyncMock()

    svc = PropostaComposicaoService.__new__(PropostaComposicaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])
    svc.comp_repo = MagicMock()
    svc.comp_repo.list_by_proposta_items_batch = AsyncMock(return_value={item_id: [comp]})
    svc.recurso_repo = MagicMock()
    svc.recurso_repo.list_by_proposta = AsyncMock(return_value=[])
    svc.resumo_repo = MagicMock()
    svc.resumo_repo.list_by_proposta = AsyncMock(return_value=[])

    resultado = await svc.buscar_valores_proposta(proposta_id)

    assert resultado["proposta_id"] == str(proposta_id)
    assert resultado["codigo"] == "PROP-001"
    assert len(resultado["items"]) == 1
    assert resultado["items"][0]["codigo"] == "01"
    assert resultado["totais"]["total_direto"] == 1000.0


@pytest.mark.asyncio
async def test_buscar_valores_proposta_not_found():
    """Test error when proposta not found."""
    proposta_id = uuid4()

    db = MagicMock()
    svc = PropostaComposicaoService.__new__(PropostaComposicaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await svc.buscar_valores_proposta(proposta_id)


@pytest.mark.asyncio
async def test_buscar_valores_proposta_no_items():
    """Test error when proposta has no items."""
    proposta_id = uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id

    db = MagicMock()
    svc = PropostaComposicaoService.__new__(PropostaComposicaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[])

    with pytest.raises(ValidationError):
        await svc.buscar_valores_proposta(proposta_id)


@pytest.mark.asyncio
async def test_validar_valores_composicao_valido():
    """Test validation of valid composition values."""
    proposta_id = uuid4()
    item_id = uuid4()
    comp_id = uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.codigo = "PROP-001"

    item = MagicMock()
    item.id = item_id
    item.codigo = "01"
    item.descricao = "Item 1"
    item.custo_direto_unitario = Decimal("100")
    item.percentual_indireto = Decimal("0.285")
    item.preco_unitario = Decimal("128.5")

    comp = MagicMock()
    comp.id = comp_id
    comp.custo_total_insumo = Decimal("100")

    db = MagicMock()
    svc = PropostaComposicaoService.__new__(PropostaComposicaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])
    svc.comp_repo = MagicMock()
    svc.comp_repo.list_by_proposta_items_batch = AsyncMock(return_value={item_id: [comp]})
    svc.recurso_repo = MagicMock()
    svc.recurso_repo.list_by_proposta = AsyncMock(return_value=[])

    resultado = await svc.validar_valores_composicao(proposta_id)

    assert resultado["valido"] is True
    assert len(resultado["erros"]) == 0
    assert resultado["items_com_composicao"] == 1


@pytest.mark.asyncio
async def test_validar_valores_composicao_items_vazios():
    """Test validation with empty items."""
    proposta_id = uuid4()
    item_id = uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id

    item = MagicMock()
    item.id = item_id
    item.codigo = "01"
    item.descricao = "Item sem composição"

    db = MagicMock()
    svc = PropostaComposicaoService.__new__(PropostaComposicaoService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])
    svc.comp_repo = MagicMock()
    svc.comp_repo.list_by_proposta_items_batch = AsyncMock(return_value={})
    svc.recurso_repo = MagicMock()
    svc.recurso_repo.list_by_proposta = AsyncMock(return_value=[])

    resultado = await svc.validar_valores_composicao(proposta_id)

    assert resultado["valido"] is False
    assert len(resultado["erros"]) > 0
    assert "Items sem composição" in resultado["erros"][0]
