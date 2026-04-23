import uuid
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.versao_service import VersaoService
from app.core.exceptions import NotFoundError


@pytest.fixture
def mock_versao_repo():
    return AsyncMock()


@pytest.fixture
def mock_propria_repo():
    return AsyncMock()


@pytest.fixture
def versao_service(mock_versao_repo, mock_propria_repo):
    return VersaoService(mock_versao_repo, mock_propria_repo)


@pytest.mark.asyncio
async def test_list_versoes_success(versao_service, mock_propria_repo, mock_versao_repo):
    mock_propria_repo.get_active_by_id.return_value = MagicMock(id=uuid.uuid4())
    mock_versao_repo.list_versoes.return_value = []

    result = await versao_service.list_versoes(uuid.uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_list_versoes_item_not_found(versao_service, mock_propria_repo):
    mock_propria_repo.get_active_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await versao_service.list_versoes(uuid.uuid4())


@pytest.mark.asyncio
async def test_criar_versao_success(versao_service, mock_propria_repo, mock_versao_repo):
    from app.models.versao_composicao import VersaoComposicao

    item_id = uuid.uuid4()
    mock_propria_repo.get_active_by_id.return_value = MagicMock(id=item_id)
    mock_versao_repo.list_versoes.return_value = []
    mock_versao_repo.get_versao_ativa.return_value = None

    db = AsyncMock()
    db.add = MagicMock()  # add is synchronous in SQLAlchemy
    result = await versao_service.criar_versao(item_id, uuid.uuid4(), db)

    assert isinstance(result, VersaoComposicao)
    assert result.numero_versao == 1


@pytest.mark.asyncio
async def test_ativar_versao_success(versao_service, mock_versao_repo):
    from app.models.versao_composicao import VersaoComposicao

    versao = VersaoComposicao(id=uuid.uuid4(), item_proprio_id=uuid.uuid4(), is_ativa=False)
    mock_versao_repo.get_by_id.return_value = versao

    db = AsyncMock()
    db.add = MagicMock()
    result = await versao_service.ativar_versao(versao.id, uuid.uuid4(), db)

    assert result.is_ativa is True
    mock_versao_repo.deactivate_all.assert_awaited_once_with(versao.item_proprio_id)


@pytest.mark.asyncio
async def test_ativar_versao_not_found(versao_service, mock_versao_repo):
    mock_versao_repo.get_by_id.return_value = None

    db = AsyncMock()
    with pytest.raises(NotFoundError):
        await versao_service.ativar_versao(uuid.uuid4(), uuid.uuid4(), db)
