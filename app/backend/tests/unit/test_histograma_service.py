"""Unit tests for HistogramaService."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.services.histograma_service import HistogramaService
from backend.core.exceptions import NotFoundError, UnprocessableEntityError


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    return db


@pytest.fixture
def svc(mock_db, monkeypatch):
    service = HistogramaService(mock_db)
    service.repo = AsyncMock()
    service.proposta_repo = AsyncMock()
    service.bcu_repo = AsyncMock()
    service.de_para_repo = AsyncMock()
    service.tcpo_repo = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_montar_histograma_not_found(svc):
    svc.proposta_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await svc.montar_histograma(uuid4())


@pytest.mark.asyncio
async def test_montar_histograma_no_bcu(svc):
    svc.proposta_repo.get_by_id.return_value = MagicMock()
    svc.bcu_repo.get_cabecalho_ativo.return_value = None
    with pytest.raises(UnprocessableEntityError):
        await svc.montar_histograma(uuid4())


@pytest.mark.asyncio
async def test_montar_histograma_success(svc, mock_db):
    proposta = MagicMock()
    proposta.bcu_cabecalho_id = None
    svc.proposta_repo.get_by_id.return_value = proposta
    cabecalho = MagicMock(id=uuid4())
    svc.bcu_repo.get_cabecalho_ativo.return_value = cabecalho
    
    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
    svc.bcu_repo.list_equipamento_premissas.return_value = []
    svc.repo.list_equipamento_premissas.return_value = []
    svc.bcu_repo.list_encargos.return_value = []
    svc.bcu_repo.list_mobilizacao_items.return_value = []
    
    result = await svc.montar_histograma(uuid4())
    
    assert proposta.bcu_cabecalho_id == cabecalho.id
    assert proposta.cpu_desatualizada is True
    assert "mao_obra" in result


@pytest.mark.asyncio
async def test_get_histograma_not_found(svc):
    svc.proposta_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await svc.get_histograma(uuid4())


@pytest.mark.asyncio
async def test_editar_item_invalid_table(svc):
    with pytest.raises(Exception):
        await svc.editar_item("tabela_invalida", uuid4(), {})
