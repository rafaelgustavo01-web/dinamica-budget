from math import ceil
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.api.v1.endpoints.propostas import (
    atualizar_proposta,
    criar_proposta,
    deletar_proposta,
    listar_propostas,
)
from backend.core.exceptions import AuthorizationError
from backend.models.enums import PropostaPapel
from backend.schemas.proposta import PropostaCreate, PropostaUpdate


class _FakeProposta:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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
def mock_proposta():
    return _FakeProposta(
        id=uuid4(),
        cliente_id=uuid4(),
        criado_por_id=uuid4(),
        codigo="PROP-2026-0001",
        titulo="Teste",
        descricao=None,
        status="RASCUNHO",
        versao_cpu=1,
        bcu_cabecalho_id=None,
        total_direto=None,
        total_indireto=None,
        total_geral=None,
        data_finalizacao=None,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
    )


@pytest.mark.asyncio
async def test_post_criar_proposta_sem_dono_cliente_retorna_201(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.criar_proposta = AsyncMock(return_value=mock_proposta)
    data = PropostaCreate(cliente_id=mock_proposta.cliente_id, titulo="Teste")

    with patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock):
        response = await criar_proposta(data=data, current_user=mock_user, db=mock_db, svc=svc_mock)

    assert response.id == mock_proposta.id
    svc_mock.criar_proposta.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_como_viewer_retorna_403(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.obter_por_id = AsyncMock(return_value=mock_proposta)
    svc_mock.atualizar_metadados = AsyncMock(return_value=mock_proposta)

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.require_proposta_role",
            new_callable=AsyncMock,
            side_effect=AuthorizationError("Papel insuficiente."),
        ),
    ):
        with pytest.raises(AuthorizationError):
            await atualizar_proposta(
                proposta_id=mock_proposta.id,
                data=PropostaUpdate(titulo="Novo"),
                current_user=mock_user,
                db=mock_db,
                svc=svc_mock,
            )


@pytest.mark.asyncio
async def test_patch_como_editor_retorna_200(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.obter_por_id = AsyncMock(return_value=mock_proposta)
    svc_mock.atualizar_metadados = AsyncMock(return_value=mock_proposta)

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.require_proposta_role",
            new_callable=AsyncMock,
        ),
    ):
        response = await atualizar_proposta(
            proposta_id=mock_proposta.id,
            data=PropostaUpdate(titulo="Novo"),
            current_user=mock_user,
            db=mock_db,
            svc=svc_mock,
        )

    assert response.id == mock_proposta.id


@pytest.mark.asyncio
async def test_delete_como_editor_retorna_403(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.obter_por_id = AsyncMock(return_value=mock_proposta)
    svc_mock.soft_delete = AsyncMock()

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.require_proposta_role",
            new_callable=AsyncMock,
            side_effect=AuthorizationError("Papel insuficiente."),
        ),
    ):
        with pytest.raises(AuthorizationError):
            await deletar_proposta(
                proposta_id=mock_proposta.id,
                current_user=mock_user,
                db=mock_db,
                svc=svc_mock,
            )


@pytest.mark.asyncio
async def test_delete_como_owner_retorna_204(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.obter_por_id = AsyncMock(return_value=mock_proposta)
    svc_mock.soft_delete = AsyncMock()

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.require_proposta_role",
            new_callable=AsyncMock,
        ),
    ):
        response = await deletar_proposta(
            proposta_id=mock_proposta.id,
            current_user=mock_user,
            db=mock_db,
            svc=svc_mock,
        )

    assert response is None


@pytest.mark.asyncio
async def test_delete_como_admin_retorna_204(mock_db, mock_user, mock_proposta):
    mock_user.is_admin = True
    svc_mock = MagicMock()
    svc_mock.obter_por_id = AsyncMock(return_value=mock_proposta)
    svc_mock.soft_delete = AsyncMock()

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.require_proposta_role",
            new_callable=AsyncMock,
        ),
    ):
        response = await deletar_proposta(
            proposta_id=mock_proposta.id,
            current_user=mock_user,
            db=mock_db,
            svc=svc_mock,
        )

    assert response is None


@pytest.mark.asyncio
async def test_get_lista_sem_cliente_id_retorna_200(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.listar_propostas = AsyncMock(return_value=([mock_proposta], 1))

    acl_repo_mock = MagicMock()
    acl_repo_mock.get_papeis_bulk = AsyncMock(return_value={mock_proposta.id: PropostaPapel.OWNER})

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.PropostaAclRepository",
            return_value=acl_repo_mock,
        ),
    ):
        response = await listar_propostas(
            cliente_id=None,
            page=1,
            page_size=20,
            current_user=mock_user,
            db=mock_db,
            svc=svc_mock,
        )

    assert response.total == 1
    assert len(response.items) == 1


@pytest.mark.asyncio
async def test_get_lista_contem_meu_papel(mock_db, mock_user, mock_proposta):
    svc_mock = MagicMock()
    svc_mock.listar_propostas = AsyncMock(return_value=([mock_proposta], 1))

    acl_repo_mock = MagicMock()
    acl_repo_mock.get_papeis_bulk = AsyncMock(return_value={mock_proposta.id: PropostaPapel.EDITOR})

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaService", return_value=svc_mock),
        patch(
            "backend.api.v1.endpoints.propostas.PropostaAclRepository",
            return_value=acl_repo_mock,
        ),
    ):
        response = await listar_propostas(
            cliente_id=None,
            page=1,
            page_size=20,
            current_user=mock_user,
            db=mock_db,
            svc=svc_mock,
        )

    assert response.items[0].meu_papel == PropostaPapel.EDITOR
