"""Integration tests for /api/v1/busca endpoints."""

import pytest


@pytest.mark.asyncio
async def test_busca_requires_auth(client):
    resp = await client.post(
        "/api/v1/busca/servicos",
        json={"cliente_id": "00000000-0000-0000-0000-000000000001", "texto_busca": "escavação"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"
