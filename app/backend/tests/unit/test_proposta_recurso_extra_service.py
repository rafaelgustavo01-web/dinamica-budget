"""Unit tests for PropostaRecursoExtraService."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal

import pytest

from backend.services.proposta_recurso_extra_service import PropostaRecursoExtraService
from backend.core.exceptions import NotFoundError, UnprocessableEntityError


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def svc(mock_db):
    service = PropostaRecursoExtraService(mock_db)
    service.repo = AsyncMock()
    service.proposta_repo = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_criar_proposta_not_found(svc):
    svc.proposta_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await svc.criar(uuid4(), {}, uuid4())


@pytest.mark.asyncio
async def test_criar_success(svc):
    proposta = MagicMock()
    svc.proposta_repo.get_by_id.return_value = proposta
    svc.repo.create_recurso.return_value = MagicMock(id=uuid4())
    
    recurso = await svc.criar(uuid4(), {"tipo_recurso": "MO", "descricao": "Teste", "custo_unitario": 10.0}, uuid4())
    
    assert recurso is not None
    assert svc.repo.create_recurso.called


@pytest.mark.asyncio
async def test_atualizar_not_found(svc):
    svc.repo.get_recurso.return_value = None
    with pytest.raises(NotFoundError):
        await svc.atualizar(uuid4(), {})


@pytest.mark.asyncio
async def test_atualizar_success(svc, mock_db):
    recurso = MagicMock()
    recurso.alocacoes = []
    svc.repo.get_recurso.return_value = recurso
    
    updated = await svc.atualizar(uuid4(), {"descricao": "Nova"})
    
    assert updated.descricao == "Nova"
    assert mock_db.add.called
    assert mock_db.flush.called


@pytest.mark.asyncio
async def test_alocar_wrong_proposta(svc):
    recurso = MagicMock(proposta_id=uuid4())
    svc.repo.get_recurso.return_value = recurso
    
    with pytest.raises(UnprocessableEntityError):
        await svc.alocar(uuid4(), uuid4(), uuid4(), Decimal("1.0"))
