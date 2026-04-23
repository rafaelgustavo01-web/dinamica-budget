import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import text

@pytest.mark.asyncio
async def test_health_check_healthy():
    """Testa endpoint de health com banco operando normalmente."""
    from app.api.v1.endpoints.health import health_check

    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    response = await health_check(db=mock_db)

    assert response["status"] == "healthy"
    assert response["database"] == "healthy"
    assert response["version"] == "2.2.0"
    mock_db.execute.assert_awaited_once()

@pytest.mark.asyncio
async def test_health_check_unhealthy():
    """Testa endpoint de health com falha no banco."""
    from app.api.v1.endpoints.health import health_check

    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB Connection Error")

    response = await health_check(db=mock_db)

    assert response["status"] == "degraded"
    assert response["database"] == "unhealthy"
    assert response["version"] == "2.2.0"
