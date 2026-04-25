from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.core import database
from backend.models.base_tcpo import BaseTcpo
from backend.models.enums import TipoRecurso
from backend.models.versao_composicao import VersaoComposicao
from backend.services.servico_catalog_service import ServicoCatalogService
from backend.services.versao_service import VersaoService


class _FakeSession:
    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.rollback = AsyncMock()


class _FakeSessionContext:
    def __init__(self, session: _FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> _FakeSession:
        return self.session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


@pytest.mark.asyncio
async def test_request_session_commits_once_on_success(monkeypatch):
    session = _FakeSession()
    monkeypatch.setattr(
        database,
        "async_session_factory",
        lambda: _FakeSessionContext(session),
    )

    generator = database.get_db_session()
    yielded = await generator.__anext__()
    assert yielded is session

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_request_session_rolls_back_on_exception(monkeypatch):
    session = _FakeSession()
    monkeypatch.setattr(
        database,
        "async_session_factory",
        lambda: _FakeSessionContext(session),
    )

    generator = database.get_db_session()
    await generator.__anext__()

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_session_factory_disables_autocommit_and_autoflush():
    assert database.async_session_factory.kw["autocommit"] is False
    assert database.async_session_factory.kw["autoflush"] is False


@pytest.mark.asyncio
async def test_versao_service_flushes_without_commit_when_creating_version():
    item_id = uuid4()
    versao_repo = AsyncMock()
    versao_repo.list_versoes.return_value = []
    versao_repo.get_versao_ativa.return_value = None

    propria_repo = AsyncMock()
    propria_repo.get_active_by_id.return_value = MagicMock(id=item_id)

    db = AsyncMock()
    db.add = MagicMock()

    service = VersaoService(versao_repo, propria_repo)
    result = await service.criar_versao(item_id, uuid4(), db)

    assert isinstance(result, VersaoComposicao)
    assert db.flush.await_count == 2
    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_versao_service_read_path_does_not_flush_or_commit():
    item_id = uuid4()
    versao_repo = AsyncMock()
    versao_repo.list_versoes.return_value = []

    propria_repo = AsyncMock()
    propria_repo.get_active_by_id.return_value = MagicMock(id=item_id)

    service = VersaoService(versao_repo, propria_repo)
    result = await service.list_versoes(item_id)

    assert result == []
    versao_repo.list_versoes.assert_awaited_once_with(item_id)


@pytest.mark.asyncio
async def test_servico_catalog_read_path_does_not_flush_or_commit(monkeypatch):
    service = ServicoCatalogService()
    servico_id = uuid4()
    servico = BaseTcpo(
        id=servico_id,
        codigo_origem="TCPO-1",
        descricao="Servico teste",
        unidade_medida="UN",
        custo_base=Decimal("10.00"),
        tipo_recurso=TipoRecurso.SERVICO,
        descricao_tokens="servico teste",
    )

    base_repo = AsyncMock()
    base_repo.get_by_id.return_value = servico
    monkeypatch.setattr(
        "app.services.servico_catalog_service.BaseTcpoRepository",
        MagicMock(return_value=base_repo),
    )

    db = AsyncMock()
    result = await service.get_servico(servico_id, db)

    assert result.id == servico_id
    db.flush.assert_not_awaited()
    db.commit.assert_not_awaited()

