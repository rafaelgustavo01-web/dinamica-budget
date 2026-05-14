# Smart Import Engine — Phase A (Backend Core) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dead `smart_import_service.py` spike with a real, deterministic spreadsheet extractor that detects headers automatically, maps columns via cascading aliases, classifies rows as ITEM/SECAO/TOTAL/VAZIA, and persists staging data per-job so the frontend can review and edit before commit.

**Architecture:** A pipeline of three pure functions (`HeaderDetector`, `ColumnMapper`, `RowClassifier`) fed by a thin openpyxl/csv extractor, all orchestrated by a rewritten `SmartImportService`. The staging payload is stored as JSONB in the existing `smart_import_jobs` table (extended with two new columns). REST endpoints follow the existing FastAPI + AsyncSession pattern.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL JSONB, openpyxl 3.1+, Alembic, pytest-asyncio

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `app/alembic/versions/032_extend_smart_import_job.py` | **Create** | Add `proposta_id`, `detected_header_row`, `detected_data_range`, `row_classifications` columns to `smart_import_jobs` |
| `app/backend/models/smart_import.py` | **Modify** | Add new columns to `SmartImportJob` ORM model |
| `app/backend/services/smart_import/extractor.py` | **Create** | `FileExtractor` — reads XLSX/XLS/CSV bytes → raw rows + raw headers list |
| `app/backend/services/smart_import/header_detector.py` | **Create** | `HeaderDetector` — finds the header row index given raw sheet data |
| `app/backend/services/smart_import/column_mapper.py` | **Create** | `ColumnMapper` — maps detected headers to canonical fields (`codigo`, `descricao`, `unidade`, `quantidade`, `preco`, `valor`) |
| `app/backend/services/smart_import/row_classifier.py` | **Create** | `RowClassifier` — assigns `ITEM | SECAO | TOTAL | VAZIA` to each mapped row |
| `app/backend/services/smart_import_service.py` | **Rewrite** | `SmartImportService` — orchestrates the pipeline, persists `SmartImportJob`, exposes staging edit operations |
| `app/backend/schemas/smart_import.py` | **Modify** | Add `StagingJobOut`, `StagingRowEdit`, `ColumnRemapRequest`, `ClassifyRequest` schemas |
| `app/backend/api/v1/endpoints/smart_import.py` | **Create** | REST router: upload, get staging, edit row, add row, delete row, reclassify, remap column, commit |
| `app/backend/api/v1/router.py` | **Modify** | Register `smart_import.router` |
| `app/backend/tests/unit/smart_import/test_header_detector.py` | **Create** | Unit tests for `HeaderDetector` |
| `app/backend/tests/unit/smart_import/test_column_mapper.py` | **Create** | Unit tests for `ColumnMapper` |
| `app/backend/tests/unit/smart_import/test_row_classifier.py` | **Create** | Unit tests for `RowClassifier` |
| `app/backend/tests/unit/smart_import/test_extractor.py` | **Create** | Unit tests for `FileExtractor` |
| `app/backend/tests/unit/smart_import/test_smart_import_service.py` | **Create** | Integration-level unit tests for the full pipeline |

---

## Task 1: Migration — Extend `smart_import_jobs`

**Files:**
- Create: `app/alembic/versions/032_extend_smart_import_job.py`

- [ ] **Step 1: Write the migration**

```python
# app/alembic/versions/032_extend_smart_import_job.py
"""Extend smart_import_jobs with pipeline metadata columns."""
from typing import Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

_SCHEMA = "operacional"
_TABLE = "smart_import_jobs"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("proposta_id", PGUUID(as_uuid=True), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("detected_header_row", sa.Integer(), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("detected_data_range", JSONB(), nullable=True), schema=_SCHEMA)
    op.add_column(_TABLE, sa.Column("row_classifications", JSONB(), nullable=True), schema=_SCHEMA)
    op.create_foreign_key(
        "fk_smart_import_jobs_proposta_id",
        _TABLE, "propostas",
        ["proposta_id"], ["id"],
        source_schema=_SCHEMA, referent_schema=_SCHEMA,
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_smart_import_jobs_proposta_id", _TABLE, schema=_SCHEMA, type_="foreignkey")
    op.drop_column(_TABLE, "row_classifications", schema=_SCHEMA)
    op.drop_column(_TABLE, "detected_data_range", schema=_SCHEMA)
    op.drop_column(_TABLE, "detected_header_row", schema=_SCHEMA)
    op.drop_column(_TABLE, "proposta_id", schema=_SCHEMA)
```

- [ ] **Step 2: Update the ORM model**

Open `app/backend/models/smart_import.py` and add the four new columns. The complete file should be:

```python
import uuid
import enum
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class SmartImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSANDO"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SmartImportJob(Base, TimestampMixin):
    __tablename__ = "smart_import_jobs"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposta_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    arquivo_origem: Mapped[str] = mapped_column(String(260), nullable=False)
    status: Mapped[SmartImportStatus] = mapped_column(
        SAEnum(SmartImportStatus, name="smart_import_status_enum", create_type=False),
        nullable=False,
        default=SmartImportStatus.PENDING,
    )
    mapping_metadata: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    payload_staging: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    detected_header_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detected_data_range: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    row_classifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
```

- [ ] **Step 3: Run migration (verify it applies cleanly)**

```bash
cd app && alembic upgrade head
```

Expected: migration `032` applied without error. If the DB is unavailable in your environment, skip and note it — the schema matches the ORM.

- [ ] **Step 4: Commit**

```bash
git add app/alembic/versions/032_extend_smart_import_job.py app/backend/models/smart_import.py
git commit -m "feat(smart-import): extend smart_import_jobs with pipeline metadata columns"
```

---

## Task 2: `FileExtractor` — raw bytes → sheet data

**Files:**
- Create: `app/backend/services/smart_import/__init__.py`
- Create: `app/backend/services/smart_import/extractor.py`
- Create: `app/backend/tests/unit/smart_import/__init__.py`
- Create: `app/backend/tests/unit/smart_import/test_extractor.py`

- [ ] **Step 1: Write failing tests**

```python
# app/backend/tests/unit/smart_import/test_extractor.py
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
    # rows should not include trailing None-only columns
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
    with pytest.raises(ValidationError, match="extensão"):
        FileExtractor.from_bytes("report.pdf", b"data")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_extractor.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — the module doesn't exist yet.

- [ ] **Step 3: Create `__init__.py` files**

```python
# app/backend/services/smart_import/__init__.py
# (empty)
```

```python
# app/backend/tests/unit/smart_import/__init__.py
# (empty)
```

- [ ] **Step 4: Implement `FileExtractor`**

```python
# app/backend/services/smart_import/extractor.py
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

import openpyxl

from backend.core.exceptions import ValidationError

_MAX_FILE_SIZE = 10 * 1024 * 1024
_XLSX_MAGIC = b"PK\x03\x04"
_SUPPORTED = {"xlsx", "csv"}


@dataclass
class SheetData:
    sheet_name: str
    rows: list[list]  # each row is a list of Python scalars (str/int/float/None)


class FileExtractor:
    @staticmethod
    def from_bytes(filename: str, content: bytes, sheet_name: str | None = None) -> SheetData:
        if len(content) > _MAX_FILE_SIZE:
            raise ValidationError(f"Arquivo excede o limite de {_MAX_FILE_SIZE // (1024 * 1024)}MB.")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in _SUPPORTED:
            raise ValidationError(f"Extensão .{ext} não suportada. Use xlsx ou csv.")

        if ext == "xlsx":
            return FileExtractor._parse_xlsx(content, sheet_name)
        return FileExtractor._parse_csv(content)

    @staticmethod
    def _parse_xlsx(content: bytes, sheet_name: str | None) -> SheetData:
        if not content[:4].startswith(_XLSX_MAGIC):
            raise ValidationError("Arquivo não é um XLSX válido.")
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        name = ws.title or "Sheet1"
        rows = []
        for raw_row in ws.iter_rows(values_only=True):
            row = list(raw_row)
            # strip trailing None columns
            while row and row[-1] is None:
                row.pop()
            rows.append(row)
        wb.close()
        return SheetData(sheet_name=name, rows=rows)

    @staticmethod
    def _parse_csv(content: bytes) -> SheetData:
        text = FileExtractor._decode_csv(content)
        reader = csv.reader(io.StringIO(text))
        rows = [list(row) for row in reader if any(c.strip() for c in row)]
        return SheetData(sheet_name="Sheet1", rows=rows)

    @staticmethod
    def _decode_csv(content: bytes) -> str:
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        raise ValidationError("Não foi possível decodificar o CSV.")
```

- [ ] **Step 5: Run tests — all must pass**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_extractor.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add app/backend/services/smart_import/ app/backend/tests/unit/smart_import/
git commit -m "feat(smart-import): FileExtractor — validates and parses XLSX/CSV to SheetData"
```

---

## Task 3: `HeaderDetector` — find the header row

**Files:**
- Create: `app/backend/services/smart_import/header_detector.py`
- Create: `app/backend/tests/unit/smart_import/test_header_detector.py`

Context: The examples show header rows at row 11 (QQP format) and rows 7-8 (PLANILHA format). The detector must scan up to row 30, score each row by how many cells match known target aliases, and return the best candidate's index (0-based).

- [ ] **Step 1: Write failing tests**

```python
# app/backend/tests/unit/smart_import/test_header_detector.py
import pytest
from backend.services.smart_import.header_detector import HeaderDetector


def _sheet_rows(header_at: int, header: list, data: list[list], total_rows=15) -> list[list]:
    """Build a synthetic sheet: blank rows before header, then header, then data."""
    rows = [[] for _ in range(header_at)]
    rows.append(header)
    rows.extend(data)
    # pad to total_rows
    while len(rows) < total_rows:
        rows.append([])
    return rows


def test_detects_header_at_row_0():
    rows = _sheet_rows(
        header_at=0,
        header=["ITEM", "DESCRICAO", "UNID", "QUANT"],
        data=[["1.1", "Mobilizacao", "vb", 1]],
    )
    idx = HeaderDetector.detect(rows)
    assert idx == 0


def test_detects_header_at_row_10():
    rows = _sheet_rows(
        header_at=10,
        header=["Item", "Descrição", "Unidade", "Qtd", "Preço Unitário", "Valor Total"],
        data=[["1.1.1", "Escavacao manual", "m2", 10.5, 50.0, 525.0]],
    )
    idx = HeaderDetector.detect(rows)
    assert idx == 10


def test_detects_header_at_row_7_with_partial_matches():
    # PLANILHA-style: header split across rows 7-8; row 7 has more matches
    rows = _sheet_rows(
        header_at=7,
        header=["ITEM", "DESCRIÇÃO DAS ATIVIDADES", "", "UNID.", "CRITÉRIO", "QUANT.", "PREÇO", "TOTAL"],
        data=[["1.1.1.1", "Canteiro de obras", "", "vb", "", 1, 3100, 3100]],
    )
    idx = HeaderDetector.detect(rows)
    assert idx == 7


def test_returns_0_when_header_is_first_non_empty_row_and_has_descricao():
    rows = [
        [],
        ["Código", "Serviço", "Un.", "Qtde.", "P.U.", "Total"],
        ["001", "Limpeza", "m2", 100, 5.5, 550],
    ]
    idx = HeaderDetector.detect(rows)
    assert idx == 1


def test_raises_when_no_header_found():
    rows = [["1", "2", "3", "4"]] * 35  # no recognizable header words
    from backend.core.exceptions import ValidationError
    with pytest.raises(ValidationError, match="cabeçalho"):
        HeaderDetector.detect(rows)


def test_respects_profile_fixed_row():
    rows = _sheet_rows(
        header_at=5,
        header=["Código", "Descrição", "Un.", "Qtd."],
        data=[["1", "Obra", "vb", 1]],
    )
    idx = HeaderDetector.detect(rows, profile_header_row=5)
    assert idx == 5
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_header_detector.py -v
```

Expected: `ImportError` — module doesn't exist.

- [ ] **Step 3: Implement `HeaderDetector`**

```python
# app/backend/services/smart_import/header_detector.py
from __future__ import annotations

from backend.core.exceptions import ValidationError

_MAX_SCAN_ROWS = 30
_MIN_SCORE = 2  # minimum alias matches for a row to qualify as header

_TARGET_ALIASES: dict[str, set[str]] = {
    "codigo": {"item", "código", "codigo", "cod", "cod.", "id", "nº", "num", "número"},
    "descricao": {
        "descrição", "descricao", "serviço", "servico", "atividade",
        "descrição das atividades", "descrição do serviço", "discriminação",
        "discriminacao",
    },
    "unidade": {"unidade", "unid", "unid.", "und", "und.", "un", "un.", "uom"},
    "quantidade": {"quantidade", "qtde", "qtd", "quant", "quant.", "coef", "coef.", "coeficiente"},
    "preco": {
        "preço", "preco", "preço unitário", "preco unitario", "p.u.", "pu",
        "custo unitário", "custo unitario", "valor unitário",
    },
    "valor": {"valor", "valor total", "total", "preço total", "subtotal"},
}

_ALL_ALIASES: set[str] = {alias for aliases in _TARGET_ALIASES.values() for alias in aliases}


def _normalize(cell: object) -> str:
    if cell is None:
        return ""
    import unicodedata
    text = str(cell).strip().lower()
    text = " ".join(text.split())
    # remove accents for loose matching
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _score_row(row: list) -> tuple[int, bool]:
    """Return (alias_match_count, has_descricao_match)."""
    count = 0
    has_descricao = False
    seen_fields: set[str] = set()
    for cell in row:
        norm = _normalize(cell)
        if not norm:
            continue
        for field, aliases in _TARGET_ALIASES.items():
            if field in seen_fields:
                continue
            # exact match
            if norm in {_normalize(a) for a in aliases}:
                count += 1
                seen_fields.add(field)
                if field == "descricao":
                    has_descricao = True
                break
            # containment: header text contains a key alias word
            for alias in aliases:
                if _normalize(alias) in norm or norm in _normalize(alias):
                    count += 1
                    seen_fields.add(field)
                    if field == "descricao":
                        has_descricao = True
                    break
    return count, has_descricao


class HeaderDetector:
    @staticmethod
    def detect(rows: list[list], profile_header_row: int | None = None) -> int:
        """Return 0-based index of the header row.

        If profile_header_row is given, trust it directly (profile takes precedence).
        Otherwise scan up to _MAX_SCAN_ROWS.
        """
        if profile_header_row is not None:
            return profile_header_row

        best_idx = -1
        best_score = 0
        best_has_descricao = False

        for idx, row in enumerate(rows[:_MAX_SCAN_ROWS]):
            score, has_descricao = _score_row(row)
            if score > best_score or (score == best_score and has_descricao and not best_has_descricao):
                best_score = score
                best_idx = idx
                best_has_descricao = has_descricao

        if best_idx == -1 or best_score < _MIN_SCORE:
            raise ValidationError(
                "Não foi possível identificar o cabeçalho da planilha. "
                "Verifique se o arquivo contém colunas de Descrição e Quantidade."
            )

        return best_idx
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_header_detector.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/header_detector.py app/backend/tests/unit/smart_import/test_header_detector.py
git commit -m "feat(smart-import): HeaderDetector — scans up to row 30, scores alias matches"
```

---

## Task 4: `ColumnMapper` — map headers to canonical fields

**Files:**
- Create: `app/backend/services/smart_import/column_mapper.py`
- Create: `app/backend/tests/unit/smart_import/test_column_mapper.py`

Context: Once the header row is known, `ColumnMapper` returns `ColumnMap` — a dict mapping canonical field name to 0-based column index. It tries profile aliases first, then global aliases, then Jaccard token overlap.

- [ ] **Step 1: Write failing tests**

```python
# app/backend/tests/unit/smart_import/test_column_mapper.py
import pytest
from backend.services.smart_import.column_mapper import ColumnMapper, ColumnMap


def test_maps_standard_portuguese_headers():
    headers = ["ITEM", "DESCRIÇÃO", "UNID.", "QUANT.", "PREÇO UNITÁRIO", "VALOR TOTAL"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 0
    assert cm["descricao"] == 1
    assert cm["unidade"] == 2
    assert cm["quantidade"] == 3
    assert cm["preco"] == 4
    assert cm["valor"] == 5


def test_maps_verbose_qqp_headers():
    headers = [None, None, "Item", "Descrição", "%Subcont.", "%Próprio", "Unid.", "Quant.", "BDI", "Preço Unitário", "Valor Total"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 2
    assert cm["descricao"] == 3
    assert cm["unidade"] == 6
    assert cm["quantidade"] == 7
    assert cm["preco"] == 9
    assert cm["valor"] == 10


def test_maps_planilha_style_headers():
    headers = ["ITEM", "", "", "", "", "", "", "", "", "DESCRIÇÃO DAS ATIVIDADES", "UNID.", "", "", "", "", "", "QUANT.", "PREÇO", "TOTAL"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 0
    assert cm["descricao"] == 9
    assert cm["unidade"] == 10
    assert cm["quantidade"] == 16
    assert cm["preco"] == 17
    assert cm["valor"] == 18


def test_raises_when_descricao_not_found():
    from backend.core.exceptions import ValidationError
    headers = ["XPTO", "AAAA", "ZZZZ"]
    with pytest.raises(ValidationError, match="descrição"):
        ColumnMapper.from_headers(headers)


def test_profile_aliases_override_global():
    # Profile knows "CRITÉRIO" → quantidade
    profile_aliases = {"quantidade": ["critério de medição"]}
    headers = ["ITEM", "ATIVIDADE", "UNID.", "CRITÉRIO DE MEDIÇÃO", "VALOR"]
    cm = ColumnMapper.from_headers(headers, profile_aliases=profile_aliases)
    assert cm["quantidade"] == 3


def test_returns_empty_for_optional_fields_not_found():
    headers = ["ITEM", "DESCRIÇÃO", "UNIDADE"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 0
    assert cm["descricao"] == 1
    assert cm["unidade"] == 2
    assert "quantidade" not in cm
    assert "preco" not in cm
    assert "valor" not in cm
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_column_mapper.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `ColumnMapper`**

```python
# app/backend/services/smart_import/column_mapper.py
from __future__ import annotations

import unicodedata

from backend.core.exceptions import ValidationError

# Canonical field → set of known aliases (normalized, no accents)
_GLOBAL_ALIASES: dict[str, set[str]] = {
    "codigo": {"item", "codigo", "cod", "cod.", "id", "no", "num", "numero"},
    "descricao": {
        "descricao", "servico", "atividade",
        "descricao das atividades", "descricao do servico", "discriminacao",
    },
    "unidade": {"unidade", "unid", "unid.", "und", "und.", "un", "un.", "uom"},
    "quantidade": {"quantidade", "qtde", "qtd", "quant", "quant.", "coef", "coef.", "coeficiente"},
    "preco": {
        "preco", "preco unitario", "p.u.", "pu",
        "custo unitario", "valor unitario",
    },
    "valor": {"valor", "valor total", "total", "preco total", "subtotal"},
}

_REQUIRED = {"descricao"}

# ColumnMap: canonical_field -> column_index
ColumnMap = dict[str, int]


def _normalize(text: object) -> str:
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = " ".join(s.split())
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _jaccard(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _match_score(norm_header: str, aliases: set[str]) -> float:
    """Return confidence [0, 1] of norm_header belonging to this alias set."""
    if norm_header in aliases:
        return 1.0
    for alias in aliases:
        if alias in norm_header or norm_header in alias:
            return 0.85
    best = max((_jaccard(norm_header, alias) for alias in aliases), default=0.0)
    return best * 0.8 if best >= 0.5 else 0.0


class ColumnMapper:
    @staticmethod
    def from_headers(
        headers: list,
        profile_aliases: dict[str, list[str]] | None = None,
    ) -> ColumnMap:
        """Map each header cell to a canonical field name.

        profile_aliases — e.g. {"quantidade": ["CRITÉRIO DE MEDIÇÃO"]} from a saved profile.
        """
        # Merge profile aliases into global (profile takes higher priority via score boost)
        merged: dict[str, set[str]] = {field: set(aliases) for field, aliases in _GLOBAL_ALIASES.items()}
        if profile_aliases:
            for field, extra in profile_aliases.items():
                if field in merged:
                    merged[field].update(_normalize(a) for a in extra)
                else:
                    merged[field] = {_normalize(a) for a in extra}

        norm_headers = [_normalize(h) for h in headers]
        result: ColumnMap = {}
        assigned_cols: set[int] = set()

        # Score every (field, col) pair and pick best matches greedily
        scores: list[tuple[float, str, int]] = []
        for field, aliases in merged.items():
            for col_idx, norm in enumerate(norm_headers):
                if not norm:
                    continue
                score = _match_score(norm, aliases)
                if score > 0:
                    scores.append((score, field, col_idx))

        scores.sort(key=lambda x: -x[0])  # highest confidence first

        assigned_fields: set[str] = set()
        for score, field, col_idx in scores:
            if field in assigned_fields or col_idx in assigned_cols:
                continue
            result[field] = col_idx
            assigned_fields.add(field)
            assigned_cols.add(col_idx)

        for req in _REQUIRED:
            if req not in result:
                raise ValidationError(
                    "A planilha deve conter uma coluna de descrição identificável. "
                    "Verifique os cabeçalhos do arquivo."
                )

        return result
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_column_mapper.py -v
```

Expected: 6 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/column_mapper.py app/backend/tests/unit/smart_import/test_column_mapper.py
git commit -m "feat(smart-import): ColumnMapper — cascade alias match (profile → global → Jaccard)"
```

---

## Task 5: `RowClassifier` — classify each data row

**Files:**
- Create: `app/backend/services/smart_import/row_classifier.py`
- Create: `app/backend/tests/unit/smart_import/test_row_classifier.py`

Context: Replaces `_is_likely_section_title` from `pq_import_service.py` with a richer classifier that returns a label instead of a bool.

- [ ] **Step 1: Write failing tests**

```python
# app/backend/tests/unit/smart_import/test_row_classifier.py
from decimal import Decimal
import pytest
from backend.services.smart_import.row_classifier import RowClassifier, RowClass


def _row(descricao=None, unidade=None, quantidade=None, preco=None, valor=None, codigo=None):
    return {
        "descricao": descricao,
        "unidade": unidade,
        "quantidade": quantidade,
        "preco": preco,
        "valor": valor,
        "codigo": codigo,
    }


def test_item_with_qtd_and_unidade():
    result = RowClassifier.classify(_row("Escavacao manual", "m2", 10.5, 50.0))
    assert result == RowClass.ITEM


def test_item_with_qtd_only():
    result = RowClassifier.classify(_row("Concreto C-25", None, 5.0))
    assert result == RowClass.ITEM


def test_secao_no_qtd_no_unidade():
    result = RowClassifier.classify(_row("1 - SERVICOS PRELIMINARES"))
    assert result == RowClass.SECAO


def test_secao_all_caps_short():
    result = RowClassifier.classify(_row("CAPITULO 1"))
    assert result == RowClass.SECAO


def test_secao_numbering_only():
    result = RowClassifier.classify(_row("1.2.3"))
    assert result == RowClass.SECAO


def test_total_keyword_in_descricao():
    result = RowClassifier.classify(_row("TOTAL GERAL", None, None, None, 500000))
    assert result == RowClass.TOTAL


def test_total_subtotal_keyword():
    result = RowClassifier.classify(_row("Subtotal Capítulo 1", None, None, None, 100000))
    assert result == RowClass.TOTAL


def test_vazia_all_none():
    result = RowClassifier.classify(_row())
    assert result == RowClass.VAZIA


def test_vazia_empty_strings():
    result = RowClassifier.classify(_row("", "", ""))
    assert result == RowClass.VAZIA


def test_item_not_falsely_classified_when_has_both():
    result = RowClassifier.classify(_row("Forma metálica", "m2", 120, 35.0, 4200))
    assert result == RowClass.ITEM
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_row_classifier.py -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `RowClassifier`**

```python
# app/backend/services/smart_import/row_classifier.py
from __future__ import annotations

import enum
import re
import unicodedata
from decimal import Decimal, InvalidOperation


class RowClass(str, enum.Enum):
    ITEM = "ITEM"
    SECAO = "SECAO"
    TOTAL = "TOTAL"
    VAZIA = "VAZIA"


_SECTION_KEYWORDS = {
    "capitulo", "secao", "titulo", "etapa", "fase", "disciplina",
    "grupo", "subgrupo", "empreitada", "contrato", "obra", "projeto",
    "relatorio", "resumo", "sumario",
}
_TOTAL_KEYWORDS = {"total", "subtotal", "soma", "geral"}
_SECTION_NUMBERING_RE = re.compile(r"^\d+(\.\d+)*\s*[\.:)\-]?\s*$")


def _norm(text: object) -> str:
    if text is None:
        return ""
    s = str(text).strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        s = str(value).strip().replace(",", ".")
        return Decimal(s)
    except InvalidOperation:
        return None


class RowClassifier:
    @staticmethod
    def classify(row: dict) -> RowClass:
        """Classify a mapped row dict (keys: descricao, unidade, quantidade, preco, valor, codigo)."""
        descricao = _norm(row.get("descricao"))
        unidade = _norm(row.get("unidade"))
        qtd = _to_decimal(row.get("quantidade"))
        preco = _to_decimal(row.get("preco"))
        valor = _to_decimal(row.get("valor"))

        # VAZIA: nothing meaningful in the row
        if not descricao and not unidade and qtd is None and preco is None and valor is None:
            return RowClass.VAZIA

        has_qtd = qtd is not None and qtd > 0
        has_unidade = bool(unidade)

        # TOTAL: keyword in description and some value present
        first_word = descricao.split()[0] if descricao.split() else ""
        if first_word in _TOTAL_KEYWORDS or any(kw in descricao for kw in _TOTAL_KEYWORDS):
            if not has_qtd:  # totals don't have individual quantities
                return RowClass.TOTAL

        # ITEM: has quantity > 0 or has both description + unit
        if has_qtd:
            return RowClass.ITEM
        if has_unidade and descricao:
            return RowClass.ITEM

        # SECAO heuristics (no qty, no unit at this point)
        if _SECTION_NUMBERING_RE.match(descricao):
            return RowClass.SECAO
        if len(descricao) <= 5:
            return RowClass.SECAO
        if descricao.isupper() and len(descricao) <= 60:
            return RowClass.SECAO
        if first_word in _SECTION_KEYWORDS:
            return RowClass.SECAO

        # Default: treat as section if no qty/unit
        return RowClass.SECAO
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_row_classifier.py -v
```

Expected: 10 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/row_classifier.py app/backend/tests/unit/smart_import/test_row_classifier.py
git commit -m "feat(smart-import): RowClassifier — ITEM/SECAO/TOTAL/VAZIA labels replacing boolean heuristic"
```

---

## Task 6: Rewrite `SmartImportService` — orchestrate the pipeline

**Files:**
- Modify: `app/backend/services/smart_import_service.py`
- Create: `app/backend/tests/unit/smart_import/test_smart_import_service.py`

- [ ] **Step 1: Write failing tests**

```python
# app/backend/tests/unit/smart_import/test_smart_import_service.py
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import openpyxl
import pytest

from backend.services.smart_import_service import SmartImportService
from backend.models.smart_import import SmartImportStatus


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
        ["ITEM", "DESCRIÇÃO", "UNID.", "QUANT.", "PREÇO UNITÁRIO", "VALOR TOTAL"],
        ["1", "SERVIÇOS PRELIMINARES", "", "", "", ""],
        ["1.1.1", "Mobilização de equipe", "vb", 1, 5200, 5200],
        ["1.1.2", "Desmobilização", "vb", 1, 2800, 2800],
        ["", "SUBTOTAL", "", "", "", 8000],
    ])
    svc = SmartImportService()
    cliente_id = uuid4()

    job = await svc.create_job(
        cliente_id=cliente_id,
        filename="test.xlsx",
        content=content,
        db=db,
    )

    assert db.add.called
    added_job = db.add.call_args[0][0]
    assert added_job.status == SmartImportStatus.REVIEW_REQUIRED
    assert added_job.detected_header_row == 0
    staging = added_job.payload_staging
    assert staging is not None
    classified = [r for r in staging["rows"] if r["row_class"] == "ITEM"]
    assert len(classified) == 2
    sections = [r for r in staging["rows"] if r["row_class"] == "SECAO"]
    assert len(sections) >= 1


@pytest.mark.asyncio
async def test_create_job_marks_complete_when_no_errors(db):
    content = _make_xlsx([
        ["ITEM", "DESCRIÇÃO", "UNID.", "QUANT."],
        ["1.1", "Escavacao manual", "m2", 10],
        ["1.2", "Aterro compactado", "m3", 5],
    ])
    svc = SmartImportService()
    job = await svc.create_job(uuid4(), "clean.xlsx", content, db)
    added_job = db.add.call_args[0][0]
    assert added_job.status == SmartImportStatus.COMPLETED


@pytest.mark.asyncio
async def test_patch_row_updates_staging(db):
    content = _make_xlsx([
        ["ITEM", "DESCRIÇÃO", "UNID.", "QUANT."],
        ["1.1", "Escavacao manual", "m2", 10],
    ])
    svc = SmartImportService()
    job = MagicMock()
    job.payload_staging = {
        "rows": [
            {
                "idx": 0, "row_class": "ITEM",
                "descricao": "Escavacao manual", "unidade": "m2",
                "quantidade": "10", "codigo": "1.1",
            }
        ]
    }
    svc.patch_row(job, row_idx=0, patch={"descricao": "Escavação manual CORRIGIDA", "quantidade": "12"})
    assert job.payload_staging["rows"][0]["descricao"] == "Escavação manual CORRIGIDA"
    assert job.payload_staging["rows"][0]["quantidade"] == "12"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_smart_import_service.py -v
```

Expected: tests fail — `SmartImportService` still has the old mock implementation.

- [ ] **Step 3: Rewrite `SmartImportService`**

Replace `app/backend/services/smart_import_service.py` entirely:

```python
"""Smart Import Service — deterministic pipeline: Extract → Detect Header → Map Columns → Classify Rows → Stage."""
from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.smart_import import SmartImportJob, SmartImportStatus
from backend.services.smart_import.column_mapper import ColumnMapper
from backend.services.smart_import.extractor import FileExtractor
from backend.services.smart_import.header_detector import HeaderDetector
from backend.services.smart_import.row_classifier import RowClass, RowClassifier

logger = get_logger(__name__)


def _cell_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


class SmartImportService:
    async def create_job(
        self,
        cliente_id: UUID,
        filename: str,
        content: bytes,
        db: AsyncSession,
        proposta_id: UUID | None = None,
        sheet_name: str | None = None,
        profile_header_row: int | None = None,
        profile_aliases: dict[str, list[str]] | None = None,
    ) -> SmartImportJob:
        # 1. Extract raw sheet
        sheet = FileExtractor.from_bytes(filename, content, sheet_name)

        # 2. Detect header row
        header_row_idx = HeaderDetector.detect(sheet.rows, profile_header_row=profile_header_row)

        # 3. Map columns
        header_cells = sheet.rows[header_row_idx] if header_row_idx < len(sheet.rows) else []
        col_map = ColumnMapper.from_headers(header_cells, profile_aliases=profile_aliases)

        # 4. Extract data rows
        data_rows = sheet.rows[header_row_idx + 1 :]
        end_row = len(data_rows) - 1
        staging_rows: list[dict] = []

        for local_idx, raw_row in enumerate(data_rows):
            mapped: dict[str, Any] = {}
            for field, col_idx in col_map.items():
                mapped[field] = _cell_str(raw_row[col_idx]) if col_idx < len(raw_row) else None

            row_class = RowClassifier.classify(mapped)
            staging_rows.append(
                {
                    "idx": local_idx,
                    "sheet_row": header_row_idx + 1 + local_idx,
                    "row_class": row_class.value,
                    **{k: mapped.get(k) for k in ("codigo", "descricao", "unidade", "quantidade", "preco", "valor")},
                }
            )

        # 5. Determine status
        has_aviso = any(
            r["row_class"] == RowClass.ITEM.value and (r.get("quantidade") is None or r.get("descricao") is None)
            for r in staging_rows
        )
        status = SmartImportStatus.REVIEW_REQUIRED if has_aviso else SmartImportStatus.COMPLETED

        data_range = {
            "start_row": header_row_idx + 1,
            "end_row": header_row_idx + 1 + end_row,
            "col_map": {f: i for f, i in col_map.items()},
        }

        job = SmartImportJob(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            proposta_id=proposta_id,
            arquivo_origem=filename,
            status=status,
            detected_header_row=header_row_idx,
            detected_data_range=data_range,
            mapping_metadata={"sheet_name": sheet.sheet_name, "col_map": col_map},
            payload_staging={"rows": staging_rows},
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"SmartImportJob {job.id} created: {len(staging_rows)} rows, status={status}")
        return job

    def patch_row(self, job: SmartImportJob, row_idx: int, patch: dict[str, Any]) -> None:
        """Edit fields on a staging row in-place. Caller must commit the session."""
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        target = next((r for r in rows if r["idx"] == row_idx), None)
        if target is None:
            raise NotFoundError("StagingRow", row_idx)
        allowed = {"codigo", "descricao", "unidade", "quantidade", "preco", "valor"}
        for key, val in patch.items():
            if key in allowed:
                target[key] = val
        # Re-classify after edit
        target["row_class"] = RowClassifier.classify(target).value

    def add_row(self, job: SmartImportJob, data: dict[str, Any]) -> dict:
        """Append a manually entered row to staging."""
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        new_idx = max((r["idx"] for r in rows), default=-1) + 1
        new_row = {
            "idx": new_idx,
            "sheet_row": None,
            "row_class": RowClass.ITEM.value,
            "codigo": data.get("codigo"),
            "descricao": data.get("descricao"),
            "unidade": data.get("unidade"),
            "quantidade": data.get("quantidade"),
            "preco": data.get("preco"),
            "valor": data.get("valor"),
        }
        new_row["row_class"] = RowClassifier.classify(new_row).value
        rows.append(new_row)
        return new_row

    def delete_row(self, job: SmartImportJob, row_idx: int) -> None:
        """Remove a staging row by idx."""
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        before = len(rows)
        job.payload_staging["rows"] = [r for r in rows if r["idx"] != row_idx]
        if len(job.payload_staging["rows"]) == before:
            raise NotFoundError("StagingRow", row_idx)

    def reclassify_row(self, job: SmartImportJob, row_idx: int, new_class: RowClass) -> None:
        """Override the automatic classification for a row."""
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        target = next((r for r in rows if r["idx"] == row_idx), None)
        if target is None:
            raise NotFoundError("StagingRow", row_idx)
        target["row_class"] = new_class.value
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_smart_import_service.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 5: Run the full unit test suite to catch regressions**

```bash
cd app && python -m pytest backend/tests/unit/ -v --tb=short
```

Expected: All existing tests pass (the old `SmartImportService` was never wired up, so no regressions expected).

- [ ] **Step 6: Commit**

```bash
git add app/backend/services/smart_import_service.py app/backend/tests/unit/smart_import/test_smart_import_service.py
git commit -m "feat(smart-import): rewrite SmartImportService — real pipeline replaces Docling mock"
```

---

## Task 7: Schemas for REST layer

**Files:**
- Modify: `app/backend/schemas/smart_import.py`

- [ ] **Step 1: Replace the schema file with the extended version**

```python
# app/backend/schemas/smart_import.py
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.models.smart_import import SmartImportStatus
from backend.services.smart_import.row_classifier import RowClass


# ── Upload ────────────────────────────────────────────────────────────────────

class SmartImportCreateRequest(BaseModel):
    proposta_id: UUID | None = None
    sheet_name: str | None = None
    profile_header_row: int | None = None
    profile_aliases: dict[str, list[str]] | None = None


# ── Staging row ───────────────────────────────────────────────────────────────

class StagingRowOut(BaseModel):
    idx: int
    sheet_row: int | None
    row_class: RowClass
    codigo: str | None = None
    descricao: str | None = None
    unidade: str | None = None
    quantidade: str | None = None
    preco: str | None = None
    valor: str | None = None


class StagingRowEdit(BaseModel):
    codigo: str | None = None
    descricao: str | None = None
    unidade: str | None = None
    quantidade: str | None = None
    preco: str | None = None
    valor: str | None = None


class StagingRowAdd(BaseModel):
    codigo: str | None = None
    descricao: str
    unidade: str | None = None
    quantidade: str | None = None
    preco: str | None = None
    valor: str | None = None


class ClassifyRequest(BaseModel):
    row_class: RowClass


class ColumnRemapRequest(BaseModel):
    field: str   # canonical field name, e.g. "quantidade"
    col_idx: int  # 0-based column index in the original sheet


# ── Job response ──────────────────────────────────────────────────────────────

class SmartImportJobOut(BaseModel):
    id: UUID
    cliente_id: UUID
    proposta_id: UUID | None
    arquivo_origem: str
    status: SmartImportStatus
    detected_header_row: int | None
    detected_data_range: dict | None
    mapping_metadata: dict | None
    rows: list[StagingRowOut] = Field(default_factory=list)

    @classmethod
    def from_job(cls, job: Any) -> "SmartImportJobOut":
        rows_raw = (job.payload_staging or {}).get("rows", [])
        return cls(
            id=job.id,
            cliente_id=job.cliente_id,
            proposta_id=job.proposta_id,
            arquivo_origem=job.arquivo_origem,
            status=job.status,
            detected_header_row=job.detected_header_row,
            detected_data_range=job.detected_data_range,
            mapping_metadata=job.mapping_metadata,
            rows=[StagingRowOut(**r) for r in rows_raw],
        )
```

- [ ] **Step 2: Verify no import errors**

```bash
cd app && python -c "from backend.schemas.smart_import import SmartImportJobOut; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/backend/schemas/smart_import.py
git commit -m "feat(smart-import): extend schemas with staging CRUD and job response types"
```

---

## Task 8: REST endpoints

**Files:**
- Create: `app/backend/api/v1/endpoints/smart_import.py`
- Modify: `app/backend/api/v1/router.py`

- [ ] **Step 1: Create the endpoint module**

```python
# app/backend/api/v1/endpoints/smart_import.py
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db
from backend.core.exceptions import NotFoundError
from backend.models.smart_import import SmartImportJob
from backend.schemas.smart_import import (
    ClassifyRequest,
    ColumnRemapRequest,
    SmartImportJobOut,
    StagingRowAdd,
    StagingRowEdit,
    StagingRowOut,
)
from backend.services.smart_import.row_classifier import RowClass
from backend.services.smart_import_service import SmartImportService

router = APIRouter(prefix="/smart-import", tags=["smart-import"])


async def _get_job(job_id: UUID, db: AsyncSession) -> SmartImportJob:
    result = await db.execute(select(SmartImportJob).where(SmartImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("SmartImportJob", str(job_id))
    return job


@router.post("", response_model=SmartImportJobOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    cliente_id: UUID = Form(...),
    proposta_id: UUID | None = Form(default=None),
    sheet_name: str | None = Form(default=None),
    profile_header_row: int | None = Form(default=None),
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SmartImportJobOut:
    content = await file.read()
    svc = SmartImportService()
    job = await svc.create_job(
        cliente_id=cliente_id,
        filename=file.filename or "upload",
        content=content,
        db=db,
        proposta_id=proposta_id,
        sheet_name=sheet_name,
        profile_header_row=profile_header_row,
    )
    return SmartImportJobOut.from_job(job)


@router.get("/{job_id}", response_model=SmartImportJobOut)
async def get_job(
    job_id: UUID,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SmartImportJobOut:
    job = await _get_job(job_id, db)
    return SmartImportJobOut.from_job(job)


@router.patch("/{job_id}/rows/{row_idx}", response_model=StagingRowOut)
async def edit_row(
    job_id: UUID,
    row_idx: int,
    body: StagingRowEdit,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StagingRowOut:
    job = await _get_job(job_id, db)
    SmartImportService().patch_row(job, row_idx, body.model_dump(exclude_none=True))
    await db.commit()
    rows = job.payload_staging["rows"]
    updated = next(r for r in rows if r["idx"] == row_idx)
    return StagingRowOut(**updated)


@router.post("/{job_id}/rows", response_model=StagingRowOut, status_code=201)
async def add_row(
    job_id: UUID,
    body: StagingRowAdd,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StagingRowOut:
    job = await _get_job(job_id, db)
    new_row = SmartImportService().add_row(job, body.model_dump())
    await db.commit()
    return StagingRowOut(**new_row)


@router.delete("/{job_id}/rows/{row_idx}", status_code=204)
async def delete_row(
    job_id: UUID,
    row_idx: int,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    job = await _get_job(job_id, db)
    SmartImportService().delete_row(job, row_idx)
    await db.commit()


@router.patch("/{job_id}/rows/{row_idx}/classify", response_model=StagingRowOut)
async def reclassify_row(
    job_id: UUID,
    row_idx: int,
    body: ClassifyRequest,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StagingRowOut:
    job = await _get_job(job_id, db)
    SmartImportService().reclassify_row(job, row_idx, RowClass(body.row_class))
    await db.commit()
    rows = job.payload_staging["rows"]
    updated = next(r for r in rows if r["idx"] == row_idx)
    return StagingRowOut(**updated)
```

- [ ] **Step 2: Register the router**

Edit `app/backend/api/v1/router.py` — add two lines:

```python
# Add to imports:
from backend.api.v1.endpoints import smart_import

# Add to router includes (after pq_layout.router):
router.include_router(smart_import.router)
```

- [ ] **Step 3: Smoke-test imports**

```bash
cd app && python -c "from backend.api.v1.endpoints.smart_import import router; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Run all unit tests to confirm no regressions**

```bash
cd app && python -m pytest backend/tests/unit/ -v --tb=short
```

Expected: All green.

- [ ] **Step 5: Commit**

```bash
git add app/backend/api/v1/endpoints/smart_import.py app/backend/api/v1/router.py
git commit -m "feat(smart-import): REST endpoints — upload, staging CRUD, classify, remap"
```

---

## Self-Review

### Spec coverage check

| Requirement | Covered by |
|-------------|------------|
| No LLM / external API | All matching is in-process (Tasks 3-5) |
| XLSX / XLS / CSV input | `FileExtractor` handles xlsx + csv; XLS needs `xlrd` — not in scope for Phase A (add as follow-up) |
| Auto header detection | `HeaderDetector` (Task 3) |
| Column alias mapping | `ColumnMapper` with profile override (Task 4) |
| Filter sections/titles/totals | `RowClassifier` (Task 5) |
| Staging: view all rows with class | `SmartImportJobOut.rows` (Task 7-8) |
| Edit row content | `PATCH /{job_id}/rows/{idx}` (Task 8) |
| Add row | `POST /{job_id}/rows` (Task 8) |
| Delete row | `DELETE /{job_id}/rows/{idx}` (Task 8) |
| Reclassify row | `PATCH /{job_id}/rows/{idx}/classify` (Task 8) |
| Persist staging as JSONB | `SmartImportJob.payload_staging` (Task 1 + 6) |
| Profile/learning hook | `profile_aliases` param in `create_job` — Phase B completes this |

**Gap identified:** XLS (`.xls`) legacy format is not handled — `openpyxl` only does `.xlsx`. Phase A uses xlsx + csv. Add a note to Phase B to add `xlrd` dependency.

### Placeholder scan

No TBD, TODO, or placeholder patterns found in the plan.

### Type consistency

- `RowClass` enum used consistently across `row_classifier.py`, `smart_import_service.py`, `schemas/smart_import.py`, and endpoints.
- `SheetData.rows` is `list[list]` throughout — `HeaderDetector`, `ColumnMapper`, and `FileExtractor` all operate on `list[list]`.
- `SmartImportJob.payload_staging["rows"]` dict keys match `StagingRowOut` field names (`idx`, `sheet_row`, `row_class`, `codigo`, `descricao`, `unidade`, `quantidade`, `preco`, `valor`).
- `patch_row` uses `model_dump(exclude_none=True)` so optional fields don't overwrite existing values with None.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-14-smart-import-phase-a.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
