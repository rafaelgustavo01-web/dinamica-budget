from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.enums import StatusProposta
from backend.models.proposta import Proposta
from backend.schemas.proposta import PropostaCreate, PropostaUpdate
from backend.services.proposta_service import PropostaService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def proposta_service(mock_repo):
    return PropostaService(mock_repo)


@pytest.mark.asyncio
async def test_criar_proposta_defaults_to_rascunho(proposta_service, mock_repo):
    cliente_id = uuid4()
    usuario_id = uuid4()
    payload = PropostaCreate(cliente_id=cliente_id, titulo="Teste", descricao="Desc")

    mock_repo.count_by_code_prefix.return_value = 0

    async def _create(proposta):
        return proposta

    mock_repo.create.side_effect = _create

    proposta = await proposta_service.criar_proposta(cliente_id, usuario_id, payload)

    assert proposta.cliente_id == cliente_id
    assert proposta.criado_por_id == usuario_id
    assert proposta.status == StatusProposta.RASCUNHO
    assert proposta.codigo.startswith("PROP-")


@pytest.mark.asyncio
async def test_listar_propostas_uses_pagination(proposta_service, mock_repo):
    cliente_id = uuid4()
    mock_repo.list_by_cliente.return_value = ([], 0)

    items, total = await proposta_service.listar_propostas(cliente_id, page=2, page_size=10)

    assert items == []
    assert total == 0
    mock_repo.list_by_cliente.assert_awaited_once_with(cliente_id, offset=10, limit=10)


@pytest.mark.asyncio
async def test_obter_detalhe_blocks_cross_cliente(proposta_service, mock_repo):
    proposta_id = uuid4()
    proposta = Proposta(
        id=proposta_id,
        cliente_id=uuid4(),
        criado_por_id=uuid4(),
        codigo="PROP-2026-0001",
        status=StatusProposta.RASCUNHO,
        versao_cpu=1,
    )
    mock_repo.get_by_id.return_value = proposta

    with pytest.raises(NotFoundError):
        await proposta_service.obter_detalhe(proposta_id, uuid4())


@pytest.mark.asyncio
async def test_atualizar_metadados_updates_fields(proposta_service, mock_repo):
    proposta_id = uuid4()
    cliente_id = uuid4()
    proposta = Proposta(
        id=proposta_id,
        cliente_id=cliente_id,
        criado_por_id=uuid4(),
        codigo="PROP-2026-0001",
        titulo="Antes",
        descricao="Antes",
        status=StatusProposta.RASCUNHO,
        versao_cpu=1,
    )
    mock_repo.get_by_id.return_value = proposta
    mock_repo.update.side_effect = lambda obj: obj

    updated = await proposta_service.atualizar_metadados(
        proposta_id,
        cliente_id,
        PropostaUpdate(titulo="Depois", descricao="Nova"),
    )

    assert updated.titulo == "Depois"
    assert updated.descricao == "Nova"


@pytest.mark.asyncio
async def test_atualizar_metadados_rejects_approved(proposta_service, mock_repo):
    proposta = Proposta(
        id=uuid4(),
        cliente_id=uuid4(),
        criado_por_id=uuid4(),
        codigo="PROP-2026-0001",
        status=StatusProposta.APROVADA,
        versao_cpu=1,
    )
    mock_repo.get_by_id.return_value = proposta

    with pytest.raises(ValidationError):
        await proposta_service.atualizar_metadados(
            proposta.id,
            proposta.cliente_id,
            PropostaUpdate(titulo="Nao pode"),
        )

