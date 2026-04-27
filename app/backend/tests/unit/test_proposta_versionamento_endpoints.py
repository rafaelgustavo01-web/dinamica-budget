"""Unit tests for versioning and approval endpoints."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.api.v1.endpoints.propostas import (
    aprovar_proposta,
    enviar_aprovacao,
    fila_aprovacoes,
    listar_versoes,
    nova_versao,
    rejeitar_proposta,
)
from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.models.enums import PropostaPapel, StatusProposta
from backend.schemas.proposta import PropostaNovaVersaoRequest, PropostaRejeitarRequest


def _make_proposta_mock(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", uuid4())
    p.cliente_id = kwargs.get("cliente_id", uuid4())
    p.criado_por_id = kwargs.get("criado_por_id", uuid4())
    p.codigo = kwargs.get("codigo", "ORC-001")
    p.titulo = kwargs.get("titulo", "Teste")
    p.descricao = kwargs.get("descricao", None)
    p.status = kwargs.get("status", StatusProposta.RASCUNHO)
    p.versao_cpu = kwargs.get("versao_cpu", 1)
    p.bcu_cabecalho_id = kwargs.get("bcu_cabecalho_id", None)
    p.total_direto = kwargs.get("total_direto", None)
    p.total_indireto = kwargs.get("total_indireto", None)
    p.total_geral = kwargs.get("total_geral", None)
    p.data_finalizacao = kwargs.get("data_finalizacao", None)
    p.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    p.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))
    p.meu_papel = kwargs.get("meu_papel", None)
    p.proposta_root_id = kwargs.get("proposta_root_id", p.id)
    p.numero_versao = kwargs.get("numero_versao", 1)
    p.versao_anterior_id = kwargs.get("versao_anterior_id", None)
    p.is_versao_atual = kwargs.get("is_versao_atual", True)
    p.is_fechada = kwargs.get("is_fechada", False)
    p.requer_aprovacao = kwargs.get("requer_aprovacao", False)
    p.aprovado_por_id = kwargs.get("aprovado_por_id", None)
    p.aprovado_em = kwargs.get("aprovado_em", None)
    p.motivo_revisao = kwargs.get("motivo_revisao", None)
    return p


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id = uuid4()
    u.is_admin = True  # admin bypasses all ACL in tests
    return u


# ── nova_versao ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_nova_versao_returns_201(mock_db, mock_user):
    proposta_id = uuid4()
    nova_p = _make_proposta_mock(numero_versao=2, codigo="ORC-001-v2")

    with (
        patch("backend.api.v1.endpoints.propostas.require_proposta_role", new_callable=AsyncMock),
        patch("backend.api.v1.endpoints.propostas.PropostaVersionamentoService") as MockSvc,
    ):
        svc_instance = MockSvc.return_value
        svc_instance.nova_versao = AsyncMock(return_value=nova_p)
        mock_db.commit = AsyncMock()

        result = await nova_versao(
            proposta_id=proposta_id,
            body=PropostaNovaVersaoRequest(motivo_revisao="revisão 2"),
            current_user=mock_user,
            db=mock_db,
        )

    assert result.numero_versao == 2
    assert result.codigo == "ORC-001-v2"
    svc_instance.nova_versao.assert_awaited_once_with(proposta_id, mock_user.id, "revisão 2")


@pytest.mark.asyncio
async def test_nova_versao_not_current_raises(mock_db, mock_user):
    proposta_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.propostas.require_proposta_role", new_callable=AsyncMock),
        patch("backend.api.v1.endpoints.propostas.PropostaVersionamentoService") as MockSvc,
    ):
        svc_instance = MockSvc.return_value
        svc_instance.nova_versao = AsyncMock(
            side_effect=UnprocessableEntityError("versão atual")
        )

        with pytest.raises(UnprocessableEntityError):
            await nova_versao(
                proposta_id=proposta_id,
                body=PropostaNovaVersaoRequest(),
                current_user=mock_user,
                db=mock_db,
            )


# ── enviar_aprovacao ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_enviar_aprovacao_changes_status(mock_db, mock_user):
    proposta_id = uuid4()
    p = _make_proposta_mock(status=StatusProposta.AGUARDANDO_APROVACAO, requer_aprovacao=True)

    with (
        patch("backend.api.v1.endpoints.propostas.require_proposta_role", new_callable=AsyncMock),
        patch("backend.api.v1.endpoints.propostas.PropostaVersionamentoService") as MockSvc,
    ):
        svc_instance = MockSvc.return_value
        svc_instance.enviar_aprovacao = AsyncMock(return_value=p)
        mock_db.commit = AsyncMock()

        result = await enviar_aprovacao(
            proposta_id=proposta_id,
            current_user=mock_user,
            db=mock_db,
        )

    assert result.status == StatusProposta.AGUARDANDO_APROVACAO


# ── aprovar ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_aprovar_returns_approved_status(mock_db, mock_user):
    proposta_id = uuid4()
    p = _make_proposta_mock(status=StatusProposta.APROVADA, aprovado_por_id=mock_user.id)

    with (
        patch("backend.api.v1.endpoints.propostas.require_proposta_role", new_callable=AsyncMock),
        patch("backend.api.v1.endpoints.propostas.PropostaVersionamentoService") as MockSvc,
    ):
        svc_instance = MockSvc.return_value
        svc_instance.aprovar = AsyncMock(return_value=p)
        mock_db.commit = AsyncMock()

        result = await aprovar_proposta(
            proposta_id=proposta_id,
            current_user=mock_user,
            db=mock_db,
        )

    assert result.status == StatusProposta.APROVADA
    svc_instance.aprovar.assert_awaited_once_with(proposta_id, mock_user.id)


# ── rejeitar ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rejeitar_returns_cpu_gerada(mock_db, mock_user):
    proposta_id = uuid4()
    p = _make_proposta_mock(status=StatusProposta.CPU_GERADA, motivo_revisao="precisa ajuste")

    with (
        patch("backend.api.v1.endpoints.propostas.require_proposta_role", new_callable=AsyncMock),
        patch("backend.api.v1.endpoints.propostas.PropostaVersionamentoService") as MockSvc,
    ):
        svc_instance = MockSvc.return_value
        svc_instance.rejeitar = AsyncMock(return_value=p)
        mock_db.commit = AsyncMock()

        result = await rejeitar_proposta(
            proposta_id=proposta_id,
            body=PropostaRejeitarRequest(motivo="precisa ajuste"),
            current_user=mock_user,
            db=mock_db,
        )

    assert result.status == StatusProposta.CPU_GERADA
    assert result.motivo_revisao == "precisa ajuste"
    svc_instance.rejeitar.assert_awaited_once_with(proposta_id, mock_user.id, "precisa ajuste")


# ── fila_aprovacoes ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fila_aprovacoes_admin_sees_all(mock_db, mock_user):
    p = _make_proposta_mock(status=StatusProposta.AGUARDANDO_APROVACAO)
    mock_user.is_admin = True

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaRepository") as MockRepo,
        patch("backend.api.v1.endpoints.propostas.PropostaAclRepository") as MockAclRepo,
    ):
        MockRepo.return_value.list_aguardando_aprovacao = AsyncMock(return_value=[p])
        MockAclRepo.return_value.get_papeis_bulk = AsyncMock(return_value={p.proposta_root_id: PropostaPapel.OWNER})

        result = await fila_aprovacoes(current_user=mock_user, db=mock_db)

    assert len(result) == 1
    assert result[0].status == StatusProposta.AGUARDANDO_APROVACAO


@pytest.mark.asyncio
async def test_fila_aprovacoes_non_aprovador_excluded(mock_db, mock_user):
    p = _make_proposta_mock(status=StatusProposta.AGUARDANDO_APROVACAO)
    mock_user.is_admin = False

    with (
        patch("backend.api.v1.endpoints.propostas.PropostaRepository") as MockRepo,
        patch("backend.api.v1.endpoints.propostas.PropostaAclRepository") as MockAclRepo,
    ):
        MockRepo.return_value.list_aguardando_aprovacao = AsyncMock(return_value=[p])
        # user has EDITOR role, not APROVADOR or OWNER
        MockAclRepo.return_value.get_papeis_bulk = AsyncMock(return_value={p.proposta_root_id: PropostaPapel.EDITOR})

        result = await fila_aprovacoes(current_user=mock_user, db=mock_db)

    assert len(result) == 0


# ── listar_versoes ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_versoes_returns_all(mock_db, mock_user):
    root_id = uuid4()
    v1 = _make_proposta_mock(numero_versao=1, proposta_root_id=root_id)
    v2 = _make_proposta_mock(numero_versao=2, proposta_root_id=root_id)

    with (
        patch("backend.api.v1.endpoints.propostas.require_proposta_role", new_callable=AsyncMock),
        patch("backend.api.v1.endpoints.propostas.PropostaVersionamentoService") as MockSvc,
    ):
        svc_instance = MockSvc.return_value
        svc_instance.listar_versoes = AsyncMock(return_value=[v1, v2])

        result = await listar_versoes(root_id=root_id, current_user=mock_user, db=mock_db)

    assert len(result) == 2
    assert result[0].numero_versao == 1
    assert result[1].numero_versao == 2
