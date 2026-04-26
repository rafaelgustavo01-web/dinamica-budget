"""Integration tests for /api/v1/clientes/{cliente_id}/pq-layout endpoints."""

import uuid

import pytest


@pytest.mark.asyncio
async def test_pq_layout_put_requires_admin(client):
    cliente_id = uuid.uuid4()
    resp = await client.put(
        f"/api/v1/clientes/{cliente_id}/pq-layout",
        json={
            "nome": "Layout Teste",
            "mapeamentos": [
                {"campo_sistema": "descricao", "coluna_planilha": "Descricao"},
                {"campo_sistema": "quantidade", "coluna_planilha": "Qtde"},
                {"campo_sistema": "unidade", "coluna_planilha": "Und"},
            ],
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_pq_layout_get_requires_auth(client):
    cliente_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/clientes/{cliente_id}/pq-layout")
    assert resp.status_code == 401
