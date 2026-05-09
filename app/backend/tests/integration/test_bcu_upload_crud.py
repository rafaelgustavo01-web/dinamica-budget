"""Integration tests for BCU upload individual + CRUD endpoints."""

import uuid
from io import BytesIO

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import hash_password
from backend.models.bcu import BcuCabecalho, BcuMaoObraItem
from backend.models.usuario import Usuario


def _make_xlsx(rows: list[list]):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.read()


@pytest.fixture
async def cabecalho(db_session: AsyncSession):
    cab = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="test.xlsx", is_ativo=False)
    db_session.add(cab)
    await db_session.commit()
    return cab


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    user = Usuario(
        id=uuid.uuid4(),
        nome="Admin Test",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.invalid",
        hashed_password=hash_password("adminpass123!"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_preview_upload_individual(client: AsyncClient, token_factory, admin_user):
    token = token_factory(str(admin_user.id))
    payload = _make_xlsx([
        ["codigo", "descricao", "salario"],
        [None, "Eletricista", 5000],
    ])
    resp = await client.post(
        "/api/v1/bcu/upload-individual/mo/preview",
        files={"file": ("mo.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "mo"
    assert data["valid_rows"] == 1
    assert data["invalid_rows"] == 0


@pytest.mark.asyncio
async def test_confirmar_upload_individual(client: AsyncClient, token_factory, cabecalho, admin_user):
    token = token_factory(str(admin_user.id))
    payload = _make_xlsx([
        ["codigo", "descricao", "salario"],
        [None, "Eletricista", 5000],
    ])
    resp = await client.post(
        f"/api/v1/bcu/upload-individual/mo/confirmar?cabecalho_id={cabecalho.id}",
        files={"file": ("mo.xlsx", payload, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported_rows"] == 1


@pytest.mark.asyncio
async def test_crud_mao_obra(client: AsyncClient, token_factory, cabecalho, admin_user):
    token = token_factory(str(admin_user.id))
    # create
    resp = await client.post(
        f"/api/v1/bcu/{cabecalho.id}/mao-obra",
        json={"descricao_funcao": "Soldador", "salario": 4500},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # update
    resp = await client.patch(
        f"/api/v1/bcu/{cabecalho.id}/mao-obra/{item_id}",
        json={"descricao_funcao": "Soldador Avançado"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["descricao_funcao"] == "Soldador Avançado"

    # delete
    resp = await client.delete(
        f"/api/v1/bcu/{cabecalho.id}/mao-obra/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    # verify deletion
    resp = await client.get(
        f"/api/v1/bcu/{cabecalho.id}/mao-obra",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0
