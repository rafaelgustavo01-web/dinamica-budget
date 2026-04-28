"""Unit tests for PropostaVersionamentoService."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.models.enums import StatusProposta
from backend.models.proposta import Proposta
from backend.services.proposta_versionamento_service import PropostaVersionamentoService


def _make_proposta(**kwargs) -> Proposta:
    defaults = dict(
        id=uuid4(),
        cliente_id=uuid4(),
        criado_por_id=uuid4(),
        codigo="ORC-001",
        status=StatusProposta.RASCUNHO,
        versao_cpu=1,
        proposta_root_id=None,
        numero_versao=1,
        versao_anterior_id=None,
        is_versao_atual=True,
        is_fechada=False,
        requer_aprovacao=False,
    )
    defaults.update(kwargs)
    p = Proposta(**{k: v for k, v in defaults.items()})
    # Set proposta_root_id = id if not provided
    if p.proposta_root_id is None:
        p.proposta_root_id = p.id
    return p


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def svc(mock_db, mock_repo, monkeypatch):
    service = PropostaVersionamentoService(mock_db)
    service.repo = mock_repo
    return service


# ── nova_versao ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nova_versao_rejects_non_current(svc, mock_repo):
    p = _make_proposta(is_versao_atual=False, is_fechada=True)
    mock_repo.get_by_id.return_value = p
    with pytest.raises(UnprocessableEntityError, match="versão atual"):
        await svc.nova_versao(p.id, uuid4())


@pytest.mark.asyncio
async def test_nova_versao_rejects_closed(svc, mock_repo):
    p = _make_proposta(is_versao_atual=True, is_fechada=True)
    mock_repo.get_by_id.return_value = p
    with pytest.raises(UnprocessableEntityError, match="fechada"):
        await svc.nova_versao(p.id, uuid4())


@pytest.mark.asyncio
async def test_nova_versao_success(svc, mock_repo, mock_db):
    root_id = uuid4()
    p = _make_proposta(
        id=root_id,
        codigo="ORC-001",
        proposta_root_id=root_id,
        numero_versao=1,
        is_versao_atual=True,
        is_fechada=False,
        status=StatusProposta.CPU_GERADA,
    )
    mock_repo.get_by_id.return_value = p
    mock_repo.max_numero_versao.return_value = 1

    nova_id = uuid4()

    async def _refresh(obj):
        obj.id = nova_id

    mock_db.refresh.side_effect = _refresh

    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
    nova = await svc.nova_versao(p.id, uuid4())

    assert nova.numero_versao == 2
    assert nova.codigo == "ORC-001-v2"
    assert nova.is_versao_atual is True
    assert nova.is_fechada is False
    assert nova.status == StatusProposta.RASCUNHO
    assert nova.versao_anterior_id == root_id
    assert nova.proposta_root_id == root_id

    # anterior deve ser fechada
    assert p.is_versao_atual is False
    assert p.is_fechada is True


@pytest.mark.asyncio
async def test_nova_versao_codigo_v2_gera_v3(svc, mock_repo, mock_db):
    """ORC-001-v2 deve gerar ORC-001-v3, não ORC-001-v2-v3."""
    root_id = uuid4()
    p = _make_proposta(
        id=uuid4(),
        codigo="ORC-001-v2",
        proposta_root_id=root_id,
        numero_versao=2,
        is_versao_atual=True,
        is_fechada=False,
    )
    mock_repo.get_by_id.return_value = p
    mock_repo.max_numero_versao.return_value = 2

    mock_db.refresh.side_effect = AsyncMock()
    mock_db.execute.return_value = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
    nova = await svc.nova_versao(p.id, uuid4())

    assert nova.codigo == "ORC-001-v3"
    assert nova.numero_versao == 3


# ── enviar_aprovacao ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_enviar_aprovacao_sem_flag_requer(svc, mock_repo):
    p = _make_proposta(requer_aprovacao=False, status=StatusProposta.CPU_GERADA)
    mock_repo.get_by_id.return_value = p
    with pytest.raises(UnprocessableEntityError, match="não requer aprovação"):
        await svc.enviar_aprovacao(p.id)


@pytest.mark.asyncio
async def test_enviar_aprovacao_status_errado(svc, mock_repo):
    p = _make_proposta(requer_aprovacao=True, status=StatusProposta.RASCUNHO)
    mock_repo.get_by_id.return_value = p
    with pytest.raises(UnprocessableEntityError, match="CPU_GERADA"):
        await svc.enviar_aprovacao(p.id)


@pytest.mark.asyncio
async def test_enviar_aprovacao_sucesso(svc, mock_repo):
    p = _make_proposta(requer_aprovacao=True, status=StatusProposta.CPU_GERADA)
    mock_repo.get_by_id.return_value = p
    result = await svc.enviar_aprovacao(p.id)
    assert result.status == StatusProposta.AGUARDANDO_APROVACAO


# ── aprovar ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_aprovar_status_errado(svc, mock_repo):
    p = _make_proposta(status=StatusProposta.CPU_GERADA)
    mock_repo.get_by_id.return_value = p
    with pytest.raises(UnprocessableEntityError, match="aguardando aprovação"):
        await svc.aprovar(p.id, uuid4())


@pytest.mark.asyncio
async def test_aprovar_sucesso(svc, mock_repo):
    aprovador_id = uuid4()
    p = _make_proposta(status=StatusProposta.AGUARDANDO_APROVACAO)
    mock_repo.get_by_id.return_value = p
    result = await svc.aprovar(p.id, aprovador_id)
    assert result.status == StatusProposta.APROVADA
    assert result.aprovado_por_id == aprovador_id
    assert result.aprovado_em is not None


# ── rejeitar ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejeitar_status_errado(svc, mock_repo):
    p = _make_proposta(status=StatusProposta.APROVADA)
    mock_repo.get_by_id.return_value = p
    with pytest.raises(UnprocessableEntityError, match="aguardando aprovação"):
        await svc.rejeitar(p.id, uuid4(), "motivo qualquer")


@pytest.mark.asyncio
async def test_rejeitar_sucesso(svc, mock_repo):
    p = _make_proposta(status=StatusProposta.AGUARDANDO_APROVACAO)
    mock_repo.get_by_id.return_value = p
    result = await svc.rejeitar(p.id, uuid4(), "precisa de ajuste")
    assert result.status == StatusProposta.CPU_GERADA
    assert result.motivo_revisao == "precisa de ajuste"
    assert result.aprovado_por_id is None
    assert result.aprovado_em is None


# ── not found ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nova_versao_not_found(svc, mock_repo):
    mock_repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await svc.nova_versao(uuid4(), uuid4())
