from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from backend.api.v1.endpoints.proposta_acl import conceder_papel, listar_acl, revogar_papel
from backend.core.exceptions import AuthorizationError, UnprocessableEntityError
from backend.models.enums import PropostaPapel
from backend.schemas.proposta import PropostaAclCreate


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid4()
    user.is_admin = False
    return user


@pytest.fixture
def mock_acl():
    a = MagicMock()
    a.id = uuid4()
    a.proposta_id = uuid4()
    a.usuario_id = uuid4()
    a.papel = PropostaPapel.EDITOR
    a.created_at = "2026-01-01T00:00:00"
    a.created_by = uuid4()
    return a


@pytest.fixture
def mock_proposta():
    p = MagicMock()
    p.id = uuid4()
    p.cliente_id = uuid4()
    return p


@pytest.mark.asyncio
async def test_get_acl_como_viewer_retorna_200(mock_db, mock_user, mock_acl, mock_proposta):
    acl_repo_mock = MagicMock()
    acl_repo_mock.list_by_proposta = AsyncMock(return_value=[mock_acl])

    user_repo_mock = MagicMock()
    user_repo_mock.get_by_id = AsyncMock(return_value=MagicMock(nome="Joao", email="joao@test.com"))

    with (
        patch(
            "backend.api.v1.endpoints.proposta_acl.require_proposta_role",
            new_callable=AsyncMock,
        ),
        patch(
            "backend.api.v1.endpoints.proposta_acl.PropostaAclRepository",
            return_value=acl_repo_mock,
        ),
        patch(
            "backend.api.v1.endpoints.proposta_acl.UsuarioRepository",
            return_value=user_repo_mock,
        ),
    ):
        response = await listar_acl(
            proposta_id=mock_proposta.id,
            current_user=mock_user,
            db=mock_db,
        )

    assert len(response) == 1
    assert response[0].papel == PropostaPapel.EDITOR


@pytest.mark.asyncio
async def test_post_acl_como_editor_retorna_403(mock_db, mock_user, mock_proposta):
    with (
        patch(
            "backend.api.v1.endpoints.proposta_acl.require_proposta_role",
            new_callable=AsyncMock,
            side_effect=AuthorizationError("Papel insuficiente."),
        ),
    ):
        with pytest.raises(AuthorizationError):
            await conceder_papel(
                proposta_id=mock_proposta.id,
                body=PropostaAclCreate(usuario_id=uuid4(), papel=PropostaPapel.EDITOR),
                current_user=mock_user,
                db=mock_db,
            )


@pytest.mark.asyncio
async def test_post_acl_como_owner_retorna_201(mock_db, mock_user, mock_acl, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.conceder = AsyncMock(return_value=mock_acl)

    user_repo_mock = MagicMock()
    user_repo_mock.get_by_id = AsyncMock(return_value=MagicMock(nome="Joao", email="joao@test.com"))

    with (
        patch(
            "backend.api.v1.endpoints.proposta_acl.require_proposta_role",
            new_callable=AsyncMock,
        ),
        patch(
            "backend.api.v1.endpoints.proposta_acl.PropostaAclService",
            return_value=svc_mock,
        ),
        patch(
            "backend.api.v1.endpoints.proposta_acl.UsuarioRepository",
            return_value=user_repo_mock,
        ),
    ):
        response = await conceder_papel(
            proposta_id=mock_proposta.id,
            body=PropostaAclCreate(usuario_id=mock_acl.usuario_id, papel=PropostaPapel.EDITOR),
            current_user=mock_user,
            db=mock_db,
        )

    assert response.papel == PropostaPapel.EDITOR
    assert response.proposta_id == mock_acl.proposta_id


@pytest.mark.asyncio
async def test_delete_acl_revogar_unico_owner_retorna_422(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.revogar = AsyncMock(side_effect=UnprocessableEntityError("Proposta nao pode ficar sem OWNER."))

    with (
        patch(
            "backend.api.v1.endpoints.proposta_acl.require_proposta_role",
            new_callable=AsyncMock,
        ),
        patch(
            "backend.api.v1.endpoints.proposta_acl.PropostaAclService",
            return_value=svc_mock,
        ),
    ):
        with pytest.raises(UnprocessableEntityError):
            await revogar_papel(
                proposta_id=mock_proposta.id,
                usuario_id=uuid4(),
                papel=PropostaPapel.OWNER,
                current_user=mock_user,
                db=mock_db,
            )


@pytest.mark.asyncio
async def test_post_acl_papel_invalido_retorna_422(mock_db, mock_user, mock_proposta):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PropostaAclCreate(usuario_id=uuid4(), papel="INVALIDO")
