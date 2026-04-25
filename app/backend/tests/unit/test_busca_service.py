"""
Unit tests for the 4-phase search cascade and normalize_text.
Fixed: correct import path for normalize_text, correct return type of _fase1_associacao.
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# normalize_text lives in associacao_repository, not busca_service
from backend.repositories.associacao_repository import normalize_text


# ─── normalize_text ───────────────────────────────────────────────────────────

def test_normalize_strips_and_lowercases():
    # Accents are removed by the NFD pipeline
    result = normalize_text("  Escavação   MANUAL  ")
    assert result == "escavacao manual"


def test_normalize_collapses_whitespace():
    # normalize_text deduplicates and sorts tokens (canonical form)
    assert normalize_text("concreto   fck  25") == "25 concreto fck"


def test_normalize_removes_accents():
    assert normalize_text("Ação de Fundação") == "acao fundacao"  # "de" is a stopword


def test_normalize_already_clean():
    assert normalize_text("escavacao manual") == "escavacao manual"


# ─── _fase1_associacao ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fase1_returns_result_and_assoc_when_association_found():
    """_fase1_associacao returns (list[ResultadoBusca], assoc) when found."""
    from backend.models.enums import StatusHomologacao, StatusValidacaoAssociacao
    from backend.services.busca_service import BuscaService

    mock_assoc = MagicMock()
    mock_assoc.item_referencia_id = uuid.uuid4()
    mock_assoc.status_validacao = StatusValidacaoAssociacao.VALIDADA
    mock_assoc.confiabilidade_score = Decimal("1.00")

    mock_servico = MagicMock()
    mock_servico.id = mock_assoc.item_referencia_id
    mock_servico.codigo_origem = "01.001.001"
    mock_servico.descricao = "Escavação manual de valas"
    mock_servico.unidade_medida = "m³"
    mock_servico.custo_base = Decimal("45.50")
    mock_servico.status_homologacao = StatusHomologacao.APROVADO

    assoc_repo = AsyncMock()
    assoc_repo.find_by_cliente_and_text = AsyncMock(return_value=mock_assoc)

    base_repo = AsyncMock()
    base_repo.get_by_id = AsyncMock(return_value=mock_servico)

    svc = BuscaService()
    resultados, assoc = await svc._fase1_associacao(
        cliente_id=uuid.uuid4(),
        texto_norm="escavacao manual de valas",
        assoc_repo=assoc_repo,
        base_repo=base_repo,
    )

    assert resultados is not None
    assert len(resultados) == 1
    assert resultados[0].score == 1.0
    assert resultados[0].origem_match == "ASSOCIACAO_DIRETA"
    assert assoc is mock_assoc


@pytest.mark.asyncio
async def test_fase1_returns_none_when_no_association():
    """_fase1_associacao returns (None, None) when no association found."""
    from backend.services.busca_service import BuscaService

    assoc_repo = AsyncMock()
    assoc_repo.find_by_cliente_and_text = AsyncMock(return_value=None)

    svc = BuscaService()
    resultados, assoc = await svc._fase1_associacao(
        cliente_id=uuid.uuid4(),
        texto_norm="texto sem associacao",
        assoc_repo=assoc_repo,
        base_repo=AsyncMock(),
    )

    assert resultados is None
    assert assoc is None


@pytest.mark.asyncio
async def test_fase1_returns_none_when_servico_inactive():
    """_fase1_associacao returns (None, None) when association exists but service is soft-deleted."""
    from backend.services.busca_service import BuscaService

    mock_assoc = MagicMock()
    mock_assoc.item_referencia_id = uuid.uuid4()

    assoc_repo = AsyncMock()
    assoc_repo.find_by_cliente_and_text = AsyncMock(return_value=mock_assoc)

    base_repo = AsyncMock()
    base_repo.get_by_id = AsyncMock(return_value=None)  # soft deleted

    svc = BuscaService()
    resultados, assoc = await svc._fase1_associacao(
        cliente_id=uuid.uuid4(),
        texto_norm="servico deletado",
        assoc_repo=assoc_repo,
        base_repo=base_repo,
    )

    assert resultados is None
    assert assoc is None


# ─── Fase 3 N+1 fix ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fase3_uses_batch_load_not_n_plus_1():
    """
    Fase 3 must call get_active_by_ids (single batch query) instead of
    get_active_by_id N times per candidate.
    """
    from backend.models.enums import StatusHomologacao
    from backend.services.busca_service import BuscaService
    from backend.ml.embedder import embedder

    svc = BuscaService()

    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    mock_servicos = {}
    for sid in ids:
        m = MagicMock()
        m.id = sid
        m.codigo_origem = "XX.001"
        m.descricao = "Serviço X"
        m.unidade_medida = "m²"
        m.custo_unitario = Decimal("10.00")
        m.status_homologacao = StatusHomologacao.APROVADO
        mock_servicos[sid] = m

    candidates = [(sid, 0.90, {}) for sid in ids]

    base_repo = AsyncMock()
    base_repo.get_by_ids = AsyncMock(return_value=mock_servicos)
    # get_by_id must NOT be called — that would be N+1
    base_repo.get_by_id = AsyncMock(side_effect=AssertionError("N+1 detected!"))

    mock_db = AsyncMock()

    with (
        patch("app.services.busca_service.embedder") as mock_embedder,
        patch("app.services.busca_service.vector_searcher") as mock_searcher,
    ):
        mock_embedder.ready = True
        mock_embedder.encode = MagicMock(return_value=[0.1] * 384)
        mock_searcher.search = AsyncMock(return_value=candidates)

        results = await svc._fase3_semantica(
            texto_busca="qualquer coisa",
            threshold=0.65,
            limit=5,
            db=mock_db,
            base_repo=base_repo,
        )

    # Verify batch call was made, N+1 was NOT (get_by_id not called)
    base_repo.get_by_ids.assert_called_once_with(ids)
    base_repo.get_by_id.assert_not_called()
    assert len(results) == 3
    assert all(r.origem_match == "IA_SEMANTICA" for r in results)

