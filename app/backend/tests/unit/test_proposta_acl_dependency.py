from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.exceptions import AuthorizationError
from backend.core.dependencies import require_proposta_role
from backend.models.enums import PropostaPapel


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid4()
    user.is_admin = False
    return user


@pytest.mark.asyncio
async def test_admin_bypass_retorna_owner(mock_db, mock_user):
    mock_user.is_admin = True

    result = await require_proposta_role(
        proposta_id=uuid4(),
        papel_minimo=PropostaPapel.EDITOR,
        current_user=mock_user,
        db=mock_db,
    )

    assert result == PropostaPapel.OWNER


@pytest.mark.asyncio
async def test_sem_acl_papel_minimo_none_retorna_none(mock_db, mock_user):
    svc_mock = AsyncMock()
    svc_mock.papel_efetivo.return_value = None

    with patch("backend.services.proposta_acl_service.PropostaAclService") as MockSvc:
        MockSvc.return_value = svc_mock
        result = await require_proposta_role(
            proposta_id=uuid4(),
            papel_minimo=None,
            current_user=mock_user,
            db=mock_db,
        )

    assert result is None


@pytest.mark.asyncio
async def test_sem_acl_papel_minimo_editor_levanta_authorization(mock_db, mock_user):
    svc_mock = AsyncMock()
    svc_mock.papel_efetivo.return_value = None
    svc_mock.HIERARQUIA = {
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
    }

    with pytest.raises(AuthorizationError):
        with patch("backend.services.proposta_acl_service.PropostaAclService") as MockSvc:
            MockSvc.return_value = svc_mock
            MockSvc.HIERARQUIA = {
                PropostaPapel.OWNER: 4,
                PropostaPapel.EDITOR: 3,
                PropostaPapel.APROVADOR: 2,
            }
            await require_proposta_role(
                proposta_id=uuid4(),
                papel_minimo=PropostaPapel.EDITOR,
                current_user=mock_user,
                db=mock_db,
            )


@pytest.mark.asyncio
async def test_owner_minimo_editor_ok(mock_db, mock_user):
    svc_mock = AsyncMock()
    svc_mock.papel_efetivo.return_value = PropostaPapel.OWNER
    svc_mock.HIERARQUIA = {
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
    }

    with patch("backend.services.proposta_acl_service.PropostaAclService") as MockSvc:
        MockSvc.return_value = svc_mock
        MockSvc.HIERARQUIA = {
            PropostaPapel.OWNER: 4,
            PropostaPapel.EDITOR: 3,
            PropostaPapel.APROVADOR: 2,
        }
        result = await require_proposta_role(
            proposta_id=uuid4(),
            papel_minimo=PropostaPapel.EDITOR,
            current_user=mock_user,
            db=mock_db,
        )

    assert result == PropostaPapel.OWNER


@pytest.mark.asyncio
async def test_aprovador_minimo_editor_levanta_authorization(mock_db, mock_user):
    svc_mock = AsyncMock()
    svc_mock.papel_efetivo.return_value = PropostaPapel.APROVADOR
    svc_mock.HIERARQUIA = {
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
    }

    with pytest.raises(AuthorizationError):
        with patch("backend.services.proposta_acl_service.PropostaAclService") as MockSvc:
            MockSvc.return_value = svc_mock
            MockSvc.HIERARQUIA = {
                PropostaPapel.OWNER: 4,
                PropostaPapel.EDITOR: 3,
                PropostaPapel.APROVADOR: 2,
            }
            await require_proposta_role(
                proposta_id=uuid4(),
                papel_minimo=PropostaPapel.EDITOR,
                current_user=mock_user,
                db=mock_db,
            )


@pytest.mark.asyncio
async def test_editor_minimo_aprovador_ok(mock_db, mock_user):
    svc_mock = AsyncMock()
    svc_mock.papel_efetivo.return_value = PropostaPapel.EDITOR
    svc_mock.HIERARQUIA = {
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
    }

    with patch("backend.services.proposta_acl_service.PropostaAclService") as MockSvc:
        MockSvc.return_value = svc_mock
        MockSvc.HIERARQUIA = {
            PropostaPapel.OWNER: 4,
            PropostaPapel.EDITOR: 3,
            PropostaPapel.APROVADOR: 2,
        }
        result = await require_proposta_role(
            proposta_id=uuid4(),
            papel_minimo=PropostaPapel.APROVADOR,
            current_user=mock_user,
            db=mock_db,
        )

    assert result == PropostaPapel.EDITOR


@pytest.mark.asyncio
async def test_multiplos_papeis_retorna_maior(mock_db, mock_user):
    svc_mock = AsyncMock()
    svc_mock.papel_efetivo.return_value = PropostaPapel.EDITOR
    svc_mock.HIERARQUIA = {
        PropostaPapel.OWNER: 4,
        PropostaPapel.EDITOR: 3,
        PropostaPapel.APROVADOR: 2,
    }

    with patch("backend.services.proposta_acl_service.PropostaAclService") as MockSvc:
        MockSvc.return_value = svc_mock
        MockSvc.HIERARQUIA = {
            PropostaPapel.OWNER: 4,
            PropostaPapel.EDITOR: 3,
            PropostaPapel.APROVADOR: 2,
        }
        result = await require_proposta_role(
            proposta_id=uuid4(),
            papel_minimo=PropostaPapel.APROVADOR,
            current_user=mock_user,
            db=mock_db,
        )

    assert result == PropostaPapel.EDITOR
