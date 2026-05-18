from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import openpyxl
import pytest

from backend.models.smart_import import SmartImportStatus
from backend.services.smart_import.row_classifier import RowClass
from backend.services.smart_import_service import SmartImportService


def _make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_create_job_extracts_and_classifies_rows(db):
    content = _make_xlsx([
        ["ITEM", "DESCRICAO", "UNID.", "QUANT.", "PRECO UNITARIO", "VALOR TOTAL"],
        ["1", "SERVICOS PRELIMINARES", "", "", "", ""],
        ["1.1.1", "Mobilizacao de equipe", "vb", 1, 5200, 5200],
        ["1.1.2", "Desmobilizacao", "vb", 1, 2800, 2800],
        ["", "SUBTOTAL", "", "", "", 8000],
    ])
    svc = SmartImportService()
    cliente_id = uuid4()

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value.get_by_cliente_id = AsyncMock(return_value=None)
        await svc.create_job(
            cliente_id=cliente_id,
            filename="test.xlsx",
            content=content,
            db=db,
        )

    assert db.add.called
    added_job = db.add.call_args[0][0]
    assert added_job.status in (SmartImportStatus.REVIEW_REQUIRED, SmartImportStatus.COMPLETED)
    staging = added_job.payload_staging
    assert staging is not None
    classified = [r for r in staging["rows"] if r["row_class"] == "ITEM"]
    assert len(classified) == 2
    sections = [r for r in staging["rows"] if r["row_class"] == "SECAO"]
    assert len(sections) >= 1


@pytest.mark.asyncio
async def test_create_job_staged_clean_is_review_required_until_commit(db):
    content = _make_xlsx([
        ["ITEM", "DESCRICAO", "UNID.", "QUANT."],
        ["1.1", "Escavacao manual", "m2", 10],
        ["1.2", "Aterro compactado", "m3", 5],
    ])
    svc = SmartImportService()
    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value.get_by_cliente_id = AsyncMock(return_value=None)
        await svc.create_job(uuid4(), "clean.xlsx", content, db)
    added_job = db.add.call_args[0][0]
    assert added_job.status == SmartImportStatus.REVIEW_REQUIRED
    assert added_job.mapping_metadata["has_warnings"] is False


@pytest.mark.asyncio
async def test_patch_row_updates_staging(db):
    svc = SmartImportService()
    job = MagicMock()
    job.payload_staging = {
        "rows": [
            {
                "idx": 0, "row_class": "ITEM",
                "descricao": "Escavacao manual", "unidade": "m2",
                "quantidade": "10", "codigo": "1.1",
                "preco": None, "valor": None,
            }
        ]
    }
    svc.patch_row(job, row_idx=0, patch={"descricao": "Escavacao manual CORRIGIDA", "quantidade": "12"})
    assert job.payload_staging["rows"][0]["descricao"] == "Escavacao manual CORRIGIDA"
    assert job.payload_staging["rows"][0]["quantidade"] == "12"


@pytest.mark.asyncio
async def test_create_job_preserves_payload_raw(db):
    content = _make_xlsx([
        ["ITEM", "DESCRICAO", "UNID.", "QUANT."],
        ["1.1", "Escavacao manual", "m2", 10],
    ])
    svc = SmartImportService()
    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value.get_by_cliente_id = AsyncMock(return_value=None)
        job = await svc.create_job(uuid4(), "raw.xlsx", content, db)
    assert job.payload_raw is not None
    assert job.payload_raw["rows"] == job.payload_staging["rows"]
    # Mutate staging; raw should stay intact
    original_raw = job.payload_raw["rows"][0]["descricao"]
    job.payload_staging["rows"][0]["descricao"] = "CHANGED"
    assert job.payload_raw["rows"][0]["descricao"] == original_raw


def test_staging_mutations_are_marked_dirty():
    svc = SmartImportService()
    job = MagicMock()
    job.payload_staging = {
        "rows": [
            {
                "idx": 0,
                "row_class": "ITEM",
                "descricao": "Escavacao manual",
                "unidade": "m2",
                "quantidade": "10",
                "codigo": "1.1",
                "preco": None,
                "valor": None,
            }
        ]
    }

    with patch("backend.services.smart_import_service.flag_modified") as mark_dirty:
        svc.patch_row(job, 0, {"descricao": "Escavacao revisada"})
        svc.add_row(job, {"descricao": "Aterro", "unidade": "m3", "quantidade": "2"})
        svc.reclassify_row(job, 1, RowClass.SECAO)
        svc.delete_row(job, 1)

    assert mark_dirty.call_count == 4
    mark_dirty.assert_called_with(job, "payload_staging")
