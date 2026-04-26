from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.models.enums import StatusMatch, TipoServicoMatch
from backend.models.proposta import PqItem
from backend.schemas.proposta import PqItemResponse, PqMatchConfirmarRequest


def _make_pq_item(**kwargs) -> PqItem:
    item = MagicMock(spec=PqItem)
    item.id = kwargs.get("id", uuid4())
    item.proposta_id = kwargs.get("proposta_id", uuid4())
    item.pq_importacao_id = None
    item.codigo_original = kwargs.get("codigo_original", "001")
    item.descricao_original = kwargs.get("descricao_original", "Escavacao manual")
    item.unidade_medida_original = kwargs.get("unidade_medida_original", "m3")
    item.quantidade_original = kwargs.get("quantidade_original", Decimal("10"))
    item.match_status = kwargs.get("match_status", StatusMatch.SUGERIDO)
    item.match_confidence = kwargs.get("match_confidence", Decimal("0.92"))
    item.servico_match_id = kwargs.get("servico_match_id", uuid4())
    item.servico_match_tipo = kwargs.get("servico_match_tipo", TipoServicoMatch.BASE_TCPO)
    item.linha_planilha = kwargs.get("linha_planilha", 2)
    item.observacao = None
    from datetime import datetime, timezone
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)
    return item


def test_pq_item_response_schema_from_model():
    item = _make_pq_item()
    response = PqItemResponse.model_validate(item)
    assert response.descricao_original == "Escavacao manual"
    assert response.match_status == StatusMatch.SUGERIDO
    assert response.match_confidence == Decimal("0.92")


def test_pq_match_confirmar_request_confirmar():
    req = PqMatchConfirmarRequest(acao="confirmar")
    assert req.acao == "confirmar"
    assert req.servico_match_id is None


def test_pq_match_confirmar_request_rejeitar():
    req = PqMatchConfirmarRequest(acao="rejeitar")
    assert req.acao == "rejeitar"


def test_pq_match_confirmar_request_substituir_requer_servico_id():
    from pydantic import ValidationError as PydanticValidationError
    with pytest.raises(PydanticValidationError):
        PqMatchConfirmarRequest(
            acao="substituir",
            # servico_match_id ausente — deve falhar
        )


@pytest.mark.asyncio
async def test_listar_pq_itens_retorna_lista():
    from unittest.mock import patch
    from backend.api.v1.endpoints.pq_importacao import listar_pq_itens

    item = _make_pq_item()
    proposta = MagicMock()
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.pq_importacao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.pq_importacao.PqItemRepository") as MockIR,
        patch("backend.api.v1.endpoints.pq_importacao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockIR.return_value.list_by_proposta = AsyncMock(return_value=[item])
        db = MagicMock()
        user = MagicMock()
        result = await listar_pq_itens(proposta_id=proposta.id, status_match=None, current_user=user, db=db)
        assert len(result) == 1
        assert result[0].descricao_original == "Escavacao manual"


@pytest.mark.asyncio
async def test_atualizar_match_confirmar():
    from unittest.mock import patch
    from backend.api.v1.endpoints.pq_importacao import atualizar_match_item
    from backend.schemas.proposta import PqMatchConfirmarRequest

    item = _make_pq_item()
    proposta = MagicMock()
    proposta.id = item.proposta_id
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.pq_importacao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.pq_importacao.PqItemRepository") as MockIR,
        patch("backend.api.v1.endpoints.pq_importacao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockIR.return_value.get_by_id = AsyncMock(return_value=item)
        MockIR.return_value.update_status = AsyncMock()
        db = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        user = MagicMock()
        req = PqMatchConfirmarRequest(acao="confirmar")
        result = await atualizar_match_item(
            proposta_id=proposta.id,
            item_id=item.id,
            body=req,
            current_user=user,
            db=db,
        )
        assert result is not None
