"""Tests for PropostaItemService."""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.enums import StatusProposta
from backend.services.proposta_item_service import PropostaItemService


@pytest.mark.asyncio
async def test_adicionar_item_success():
    """Test adding an item successfully."""
    proposta_id = uuid4()
    item_id = uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.status = StatusProposta.RASCUNHO

    db = MagicMock()
    db.flush = AsyncMock()

    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[])

    resultado = await svc.adicionar_item(
        proposta_id,
        codigo="01",
        descricao="Escavação",
        unidade_medida="m³",
        quantidade=Decimal("100"),
    )

    assert resultado["codigo"] == "01"
    assert resultado["descricao"] == "Escavação"
    assert resultado["quantidade"] == 100.0
    assert db.add.called


@pytest.mark.asyncio
async def test_adicionar_item_proposta_not_found():
    """Test error when proposta not found."""
    proposta_id = uuid4()

    db = MagicMock()
    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await svc.adicionar_item(
            proposta_id,
            codigo="01",
            descricao="Item",
            unidade_medida="un",
            quantidade=Decimal("1"),
        )


@pytest.mark.asyncio
async def test_adicionar_item_invalid_status():
    """Test error when proposta is in invalid status."""
    proposta_id = uuid4()

    proposta = MagicMock()
    proposta.status = StatusProposta.APROVADA

    db = MagicMock()
    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)

    with pytest.raises(ValidationError):
        await svc.adicionar_item(
            proposta_id,
            codigo="01",
            descricao="Item",
            unidade_medida="un",
            quantidade=Decimal("1"),
        )


@pytest.mark.asyncio
async def test_adicionar_item_quantidade_invalida():
    """Test error when quantity is invalid."""
    proposta_id = uuid4()

    proposta = MagicMock()
    proposta.status = StatusProposta.RASCUNHO

    db = MagicMock()
    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)

    with pytest.raises(ValidationError):
        await svc.adicionar_item(
            proposta_id,
            codigo="01",
            descricao="Item",
            unidade_medida="un",
            quantidade=Decimal("0"),
        )


@pytest.mark.asyncio
async def test_adicionar_item_codigo_duplicado():
    """Test error when codigo already exists."""
    proposta_id = uuid4()
    item_id = uuid4()

    proposta = MagicMock()
    proposta.status = StatusProposta.RASCUNHO

    item_existente = MagicMock()
    item_existente.codigo = "01"

    db = MagicMock()
    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item_existente])

    with pytest.raises(ValidationError):
        await svc.adicionar_item(
            proposta_id,
            codigo="01",
            descricao="Item",
            unidade_medida="un",
            quantidade=Decimal("1"),
        )


@pytest.mark.asyncio
async def test_remover_item_success():
    """Test removing an item successfully."""
    proposta_id = uuid4()
    item_id = uuid4()

    proposta = MagicMock()
    proposta.status = StatusProposta.RASCUNHO

    item = MagicMock()
    item.proposta_id = proposta_id
    item.codigo = "01"

    db = MagicMock()
    db.flush = AsyncMock()

    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.get_by_id = AsyncMock(return_value=item)
    svc.item_repo.delete = AsyncMock()

    await svc.remover_item(proposta_id, item_id)

    assert svc.item_repo.delete.called
    assert db.add.called


@pytest.mark.asyncio
async def test_remover_item_invalid_status():
    """Test error when removing from non-RASCUNHO proposal."""
    proposta_id = uuid4()
    item_id = uuid4()

    proposta = MagicMock()
    proposta.status = StatusProposta.CPU_GERADA

    item = MagicMock()
    item.proposta_id = proposta_id

    db = MagicMock()
    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.get_by_id = AsyncMock(return_value=item)

    with pytest.raises(ValidationError):
        await svc.remover_item(proposta_id, item_id)


@pytest.mark.asyncio
async def test_listar_items_success():
    """Test listing items successfully."""
    proposta_id = uuid4()
    item_id = uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id

    item = MagicMock()
    item.id = item_id
    item.codigo = "01"
    item.descricao = "Item"
    item.quantidade = Decimal("100")
    item.custo_direto_unitario = Decimal("50")
    item.preco_total = Decimal("5000")
    item.composicoes = []

    db = MagicMock()
    svc = PropostaItemService.__new__(PropostaItemService)
    svc.db = db
    svc.proposta_repo = MagicMock()
    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.item_repo = MagicMock()
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])

    resultado = await svc.listar_items(proposta_id)

    assert len(resultado) == 1
    assert resultado[0]["codigo"] == "01"
