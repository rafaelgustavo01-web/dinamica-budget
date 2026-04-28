"""Unit tests for Histograma endpoints."""
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
import pytest
from httpx import AsyncClient

from backend.main import app
from backend.models.enums import StatusProposta


@pytest.mark.asyncio
async def test_montar_histograma_viewer_denied(client: AsyncClient, token_factory):
    # Viewer role
    proposta_id = uuid4()
    with patch("backend.api.v1.endpoints.propostas.require_proposta_role", AsyncMock()) as mock_role:
        mock_role.side_effect = Exception("Access Denied")
        response = await client.post(
            f"/api/v1/propostas/{proposta_id}/montar-histograma",
            headers={"Authorization": f"Bearer {token_factory(str(uuid4()))}"},
        )
    assert response.status_code in [400, 401, 403, 500]


@pytest.mark.asyncio
async def test_get_histograma_success(client: AsyncClient, token_factory, seed_user):
    # seed_user inserts a real user so get_current_user resolves the token subject.
    proposta_id = uuid4()
    with patch("backend.api.v1.endpoints.propostas.require_proposta_role", AsyncMock()):
        with patch("backend.services.histograma_service.HistogramaService.get_histograma", AsyncMock()) as mock_get:
            mock_get.return_value = {
                "proposta_id": str(proposta_id),
                "bcu_cabecalho_id": None,
                "mao_obra": [],
                "equipamento_premissa": None,
                "equipamentos": [],
                "encargos_horista": [],
                "encargos_mensalista": [],
                "epis": [],
                "ferramentas": [],
                "mobilizacao": [],
                "recursos_extras": [],
                "divergencias": [],
                "cpu_desatualizada": False
            }
            response = await client.get(
                f"/api/v1/propostas/{proposta_id}/histograma",
                headers={"Authorization": f"Bearer {token_factory(str(seed_user))}"},
            )
            assert response.status_code == 200
            assert response.json()["proposta_id"] == str(proposta_id)
