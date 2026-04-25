"""
Unit tests for S-04 security/RBAC hardening.

Tests covered:
  - GET /busca/associacoes requires cliente access
  - GET /servicos/{item_id}/versoes requires cliente access
  - GET /servicos/ validates cliente_id access when provided
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_list_associacoes_requires_cliente_access():
    """GET /busca/associacoes must call require_cliente_access."""
    from backend.api.v1.endpoints.busca import list_associacoes

    client_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    mock_db = AsyncMock()
    repo = AsyncMock()
    repo.list_by_cliente = AsyncMock(return_value=([], 0))

    with patch("app.api.v1.endpoints.busca.AssociacaoRepository", return_value=repo):
        with patch("app.api.v1.endpoints.busca.require_cliente_access", AsyncMock()) as mock_require:
            result = await list_associacoes(
                cliente_id=client_id,
                page=1,
                page_size=20,
                current_user=user,
                db=mock_db,
            )
            assert result.total == 0
            mock_require.assert_awaited_once_with(client_id, user, mock_db)


@pytest.mark.asyncio
async def test_list_versoes_requires_cliente_access():
    """GET /servicos/{item_id}/versoes must call require_cliente_access."""
    from backend.api.v1.endpoints.versoes import list_versoes
    from datetime import UTC, datetime

    item_id = uuid.uuid4()
    client_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    item = MagicMock()
    item.id = item_id
    item.cliente_id = client_id

    versao = MagicMock()
    versao.id = uuid.uuid4()
    versao.numero_versao = 1
    versao.is_ativa = True
    versao.criado_em = datetime.now(UTC)
    versao.origem = None
    versao.cliente_id = None

    mock_db = AsyncMock()
    propria_repo = AsyncMock()
    propria_repo.get_active_by_id = AsyncMock(return_value=item)
    versao_repo = AsyncMock()
    versao_repo.list_versoes = AsyncMock(return_value=[versao])

    with patch("app.api.v1.endpoints.versoes.ItensPropiosRepository", return_value=propria_repo):
        with patch("app.api.v1.endpoints.versoes.VersaoComposicaoRepository", return_value=versao_repo):
            with patch("app.api.v1.endpoints.versoes.require_cliente_access", AsyncMock()) as mock_require:
                with patch("app.api.v1.endpoints.versoes.VersaoService.list_versoes", AsyncMock(return_value=[versao])):
                    result = await list_versoes(
                        item_id=item_id,
                        current_user=user,
                        db=mock_db,
                    )
                    assert len(result) == 1
                    mock_require.assert_awaited_once_with(client_id, user, mock_db)


@pytest.mark.asyncio
async def test_list_servicos_validates_cliente_id_access_when_present():
    """GET /servicos/ validates access only if cliente_id is provided."""
    from backend.api.v1.endpoints.servicos import list_servicos

    client_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_admin = False
    user.is_active = True

    mock_db = AsyncMock()
    mock_response = MagicMock(items=[], total=0, page=1, page_size=20, pages=0)
    mock_service = AsyncMock()
    mock_service.list_servicos = AsyncMock(return_value=mock_response)

    with patch("app.api.v1.endpoints.servicos.servico_catalog_service", mock_service):
        with patch("app.api.v1.endpoints.servicos.require_cliente_access", AsyncMock()) as mock_require:
            # Scenario 1: cliente_id provided
            await list_servicos(
                q=None,
                categoria_id=None,
                cliente_id=client_id,
                page=1,
                page_size=20,
                current_user=user,
                db=mock_db,
            )
            mock_require.assert_awaited_once_with(client_id, user, mock_db)
            mock_require.reset_mock()

            # Scenario 2: no cliente_id
            await list_servicos(
                q=None,
                categoria_id=None,
                cliente_id=None,
                page=1,
                page_size=20,
                current_user=user,
                db=mock_db,
            )
            mock_require.assert_not_awaited()

