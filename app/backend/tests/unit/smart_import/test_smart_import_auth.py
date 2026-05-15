import uuid
from io import BytesIO

import openpyxl
import pytest

from backend.models.cliente import Cliente
from backend.models.smart_import import SmartImportJob, SmartImportStatus
from backend.models.usuario import Usuario, UsuarioPerfil


def _make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
async def smart_import_setup(db_session):
    """Create a user with ADMIN access to a client and another user without access."""
    from backend.core.security import hash_password

    cliente = Cliente(
        id=uuid.uuid4(),
        nome_fantasia="Test Client",
        cnpj="12345678000195",
    )
    db_session.add(cliente)

    user_with_access = Usuario(
        id=uuid.uuid4(),
        nome="User With Access",
        email=f"user-{uuid.uuid4().hex[:8]}@test.invalid",
        hashed_password=hash_password("pass123!"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user_with_access)

    user_no_access = Usuario(
        id=uuid.uuid4(),
        nome="User No Access",
        email=f"nouser-{uuid.uuid4().hex[:8]}@test.invalid",
        hashed_password=hash_password("pass123!"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user_no_access)

    perfil = UsuarioPerfil(
        usuario_id=user_with_access.id,
        cliente_id=cliente.id,
        perfil="ADMIN",
    )
    db_session.add(perfil)
    await db_session.commit()

    # Create a job
    job = SmartImportJob(
        id=uuid.uuid4(),
        cliente_id=cliente.id,
        arquivo_origem="test.xlsx",
        status=SmartImportStatus.COMPLETED,
        payload_staging={"rows": []},
    )
    db_session.add(job)
    await db_session.commit()

    return {
        "cliente_id": cliente.id,
        "user_with_access": user_with_access,
        "user_no_access": user_no_access,
        "job_id": job.id,
    }


@pytest.mark.asyncio
async def test_upload_rejects_unauthorized_client(client, db_session, token_factory, smart_import_setup):
    other_user = smart_import_setup["user_no_access"]
    token = token_factory(str(other_user.id))
    files = {"file": ("test.xlsx", _make_xlsx([["DESC"], ["Item 1"]]))}
    resp = await client.post(
        "/api/v1/smart-import",
        data={"cliente_id": str(smart_import_setup["cliente_id"])},
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_upload_allows_authorized_client(client, db_session, token_factory, smart_import_setup):
    user = smart_import_setup["user_with_access"]
    token = token_factory(str(user.id))
    files = {"file": ("test.xlsx", _make_xlsx([["DESC"], ["Item 1"]]))}
    resp = await client.post(
        "/api/v1/smart-import",
        data={"cliente_id": str(smart_import_setup["cliente_id"])},
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    # Upload may fail validation (no descricao/qtd header) but should not be 403
    assert resp.status_code != 403


@pytest.mark.asyncio
async def test_get_job_rejects_unauthorized(client, db_session, token_factory, smart_import_setup):
    other_user = smart_import_setup["user_no_access"]
    token = token_factory(str(other_user.id))
    resp = await client.get(
        f"/api/v1/smart-import/{smart_import_setup['job_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_job_allows_authorized(client, db_session, token_factory, smart_import_setup):
    user = smart_import_setup["user_with_access"]
    token = token_factory(str(user.id))
    resp = await client.get(
        f"/api/v1/smart-import/{smart_import_setup['job_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_patch_row_rejects_unauthorized(client, db_session, token_factory, smart_import_setup):
    other_user = smart_import_setup["user_no_access"]
    token = token_factory(str(other_user.id))
    resp = await client.patch(
        f"/api/v1/smart-import/{smart_import_setup['job_id']}/rows/0",
        json={"descricao": "New"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_row_rejects_unauthorized(client, db_session, token_factory, smart_import_setup):
    other_user = smart_import_setup["user_no_access"]
    token = token_factory(str(other_user.id))
    resp = await client.delete(
        f"/api/v1/smart-import/{smart_import_setup['job_id']}/rows/0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_commit_job_rejects_unauthorized(client, db_session, token_factory, smart_import_setup):
    other_user = smart_import_setup["user_no_access"]
    token = token_factory(str(other_user.id))
    resp = await client.post(
        f"/api/v1/smart-import/{smart_import_setup['job_id']}/commit",
        json={"corrections": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
