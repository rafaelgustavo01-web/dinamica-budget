from io import BytesIO

import openpyxl
import pytest

from backend.core.exceptions import ValidationError
from backend.services.smart_import.extractor import FileExtractor, SheetData


def _make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_extract_xlsx_returns_sheet_data():
    content = _make_xlsx([
        ["ITEM", "DESCRICAO", "UND", "QTD"],
        ["1.1", "Mobilização", "vb", 1],
    ])
    sd = FileExtractor.from_bytes("test.xlsx", content)
    assert isinstance(sd, SheetData)
    assert sd.sheet_name is not None
    assert len(sd.rows) == 2
    assert sd.rows[0] == ["ITEM", "DESCRICAO", "UND", "QTD"]
    assert sd.rows[1][0] == "1.1"


def test_extract_xlsx_strips_none_trailing_columns():
    content = _make_xlsx([
        ["ITEM", "DESC", None, None],
        ["1", "Obra", None, None],
    ])
    sd = FileExtractor.from_bytes("test.xlsx", content)
    assert sd.rows[0] == ["ITEM", "DESC"]


def test_extract_csv_returns_sheet_data():
    csv_bytes = b"codigo,descricao,unidade,quantidade\n001,Escavacao,m2,10\n"
    sd = FileExtractor.from_bytes("test.csv", csv_bytes)
    assert sd.rows[0] == ["codigo", "descricao", "unidade", "quantidade"]
    assert sd.rows[1][2] == "m2"


def test_extract_rejects_oversized_file():
    big = b"x" * (11 * 1024 * 1024)
    with pytest.raises(ValidationError, match="limite"):
        FileExtractor.from_bytes("big.xlsx", big)


def test_extract_rejects_fake_xlsx():
    fake = b"not a zip file at all"
    with pytest.raises(ValidationError, match="válido"):
        FileExtractor.from_bytes("bad.xlsx", fake)


def test_extract_rejects_unsupported_extension():
    with pytest.raises(ValidationError, match=r"\.pdf"):
        FileExtractor.from_bytes("report.pdf", b"data")
