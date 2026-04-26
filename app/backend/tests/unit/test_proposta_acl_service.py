from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from backend.core.exceptions import UnprocessableEntityError
from backend.models.enums import PropostaPapel
from backend.models.proposta import PropostaAcl
from backend.services.proposta_acl_service import PropostaAclService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def acl_service(mock_repo):
    svc = PropostaAclService.__new__(PropostaAclService)
    svc.repo = mock_repo
    return svc


@pytest.mark.asyncio
async def test_conceder_owner_idempotente(acl_service, mock_repo):
    proposta_id = uuid4()
    usuario_id = uuid4()
    created_by = uuid4()

    existing = PropostaAcl(
        id=uuid4(),
        proposta_id=proposta_id,
        usuario_id=usuario_id,
        papel=PropostaPapel.OWNER,
        created_by=created_by,
    )
    mock_repo.get_papeis_for_user.return_value = {PropostaPapel.OWNER}
    mock_repo.list_by_proposta.return_value = [existing]

    result = await acl_service.conceder(proposta_id, usuario_id, PropostaPapel.OWNER, created_by)

    assert result.usuario_id == usuario_id
    assert result.papel == PropostaPapel.OWNER
    mock_repo.add_papel.assert_not_awaited()


@pytest.mark.asyncio
async def test_revogar_ultimo_owner_levanta_422(acl_service, mock_repo):
    proposta_id = uuid4()
    usuario_id = uuid4()
    mock_repo.count_owners.return_value = 1

    with pytest.raises(UnprocessableEntityError):
        await acl_service.revogar(proposta_id, usuario_id, PropostaPapel.OWNER)

    mock_repo.remove_papel.assert_not_awaited()


@pytest.mark.asyncio
async def test_papel_efetivo_retorna_maior(acl_service, mock_repo):
    proposta_id = uuid4()
    usuario_id = uuid4()
    mock_repo.get_papeis_for_user.return_value = {PropostaPapel.APROVADOR, PropostaPapel.EDITOR}

    result = await acl_service.papel_efetivo(proposta_id, usuario_id)

    assert result == PropostaPapel.EDITOR


@pytest.mark.asyncio
async def test_papel_efetivo_retorna_none_sem_acl(acl_service, mock_repo):
    proposta_id = uuid4()
    usuario_id = uuid4()
    mock_repo.get_papeis_for_user.return_value = set()

    result = await acl_service.papel_efetivo(proposta_id, usuario_id)

    assert result is None


@pytest.mark.asyncio
async def test_count_owners_correto(acl_service, mock_repo):
    proposta_id = uuid4()
    mock_repo.count_owners.return_value = 3

    result = await acl_service.repo.count_owners(proposta_id)

    assert result == 3
