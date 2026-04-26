from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.api.v1.endpoints.proposta_export import export_excel, export_pdf


@pytest.mark.asyncio
async def test_export_excel_endpoint_retorna_stream():
    proposta = MagicMock()
    proposta.id = uuid4()
    proposta.codigo = "PROP-2026-0001"
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.proposta_export.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.proposta_export.PropostaExportService") as MockSvc,
        patch("backend.api.v1.endpoints.proposta_export.require_proposta_role", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.gerar_excel = AsyncMock(return_value=b"xlsx-bytes")
        db = MagicMock()
        user = MagicMock()
        response = await export_excel(proposta_id=proposta.id, current_user=user, db=db)
        assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_export_pdf_endpoint_retorna_stream():
    proposta = MagicMock()
    proposta.id = uuid4()
    proposta.codigo = "PROP-2026-0001"
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.proposta_export.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.proposta_export.PropostaExportService") as MockSvc,
        patch("backend.api.v1.endpoints.proposta_export.require_proposta_role", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.gerar_pdf = AsyncMock(return_value=b"pdf-bytes")
        db = MagicMock()
        user = MagicMock()
        response = await export_pdf(proposta_id=proposta.id, current_user=user, db=db)
        assert response.media_type == "application/pdf"
        assert "attachment" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_export_excel_endpoint_404_quando_proposta_nao_existe():
    from backend.core.exceptions import NotFoundError

    with (
        patch("backend.api.v1.endpoints.proposta_export.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.proposta_export.require_proposta_role", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=None)
        db = MagicMock()
        user = MagicMock()
        with pytest.raises(NotFoundError):
            await export_excel(proposta_id=uuid4(), current_user=user, db=db)


@pytest.mark.asyncio
async def test_export_pdf_endpoint_404_quando_proposta_nao_existe():
    from backend.core.exceptions import NotFoundError

    with (
        patch("backend.api.v1.endpoints.proposta_export.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.proposta_export.require_proposta_role", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=None)
        db = MagicMock()
        user = MagicMock()
        with pytest.raises(NotFoundError):
            await export_pdf(proposta_id=uuid4(), current_user=user, db=db)
