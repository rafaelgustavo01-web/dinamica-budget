# F4-05 Smart Import Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Smart Import so staged PQ imports are authorized, persisted, committed exactly once, and numerically correct for Brazilian spreadsheets.

**Architecture:** Keep the current pipeline, but add small guard rails at the module boundaries: endpoint authorization, immutable JSONB staging updates, a shared decimal parser, bounded extraction, and idempotent commit metadata. Avoid new database schema unless tests prove metadata is insufficient.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL JSONB, Pydantic, pytest, React/TypeScript only if status messaging needs a small compatibility fix.

---

## Files And Responsibilities

- Modify `app/backend/api/v1/endpoints/smart_import.py`: authorize job access/mutations and lock job row during commit.
- Modify `app/backend/services/smart_import_service.py`: immutable staging updates, idempotent commit guard, shared decimal parser usage, bounded staging metadata.
- Modify `app/backend/services/smart_import/extractor.py`: row/column bounds, workbook close safety, explicit sheet validation.
- Modify `app/backend/services/smart_import/header_detector.py`: validate fixed profile header row.
- Create `app/backend/services/smart_import/number_parser.py`: Brazilian decimal parser shared by classifier and commit.
- Modify `app/backend/services/smart_import/row_classifier.py`: use parser and distinguish invalid quantities from missing quantities where possible.
- Modify `app/backend/services/smart_import/profile_learner.py`: validate learned fields and header rows before persisting.
- Modify `app/backend/schemas/smart_import.py`: expose lightweight warnings/metadata if needed.
- Modify `app/frontend/src/shared/services/api/smartImportApi.ts`: include status/warnings typing if backend exposes them.
- Modify `app/frontend/src/features/smart-import/SmartImportStagingPage.tsx`: do not treat every `REVIEW_REQUIRED` status as "bad rows" if backend exposes `has_warnings`.
- Test `app/backend/tests/unit/smart_import/test_number_parser.py`.
- Test `app/backend/tests/unit/smart_import/test_row_classifier.py`.
- Test `app/backend/tests/unit/smart_import/test_smart_import_service.py`.
- Test `app/backend/tests/unit/smart_import/test_commit.py`.
- Test `app/backend/tests/unit/smart_import/test_smart_import_auth.py`.
- Test `app/backend/tests/unit/smart_import/test_extractor.py`.
- Test `app/backend/tests/unit/smart_import/test_header_detector.py`.

---

### Task 1: Add Smart Import Authorization Gates

**Files:**
- Modify: `app/backend/api/v1/endpoints/smart_import.py`
- Test: `app/backend/tests/unit/smart_import/test_smart_import_auth.py`

- [ ] **Step 1: Write failing authorization tests**

Create `app/backend/tests/unit/smart_import/test_smart_import_auth.py` with focused unit tests that patch dependencies instead of starting the full app.

```python
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.api.v1.endpoints import smart_import


def _user():
    u = MagicMock()
    u.id = uuid4()
    u.is_admin = False
    return u


def _job(proposta_id=None):
    j = MagicMock()
    j.id = uuid4()
    j.cliente_id = uuid4()
    j.proposta_id = proposta_id
    j.payload_staging = {"rows": []}
    return j


@pytest.mark.asyncio
async def test_authorize_job_with_proposta_requires_proposta_role():
    db = AsyncMock()
    user = _user()
    job = _job(proposta_id=uuid4())

    with patch.object(smart_import, "require_proposta_role", new=AsyncMock()) as require_role, \
         patch.object(smart_import, "require_cliente_access", new=AsyncMock()) as require_cliente:
        await smart_import._authorize_job(job, user, db, write=True)

    require_role.assert_awaited_once()
    require_cliente.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorize_job_without_proposta_requires_cliente_access():
    db = AsyncMock()
    user = _user()
    job = _job(proposta_id=None)

    with patch.object(smart_import, "require_proposta_role", new=AsyncMock()) as require_role, \
         patch.object(smart_import, "require_cliente_access", new=AsyncMock()) as require_cliente:
        await smart_import._authorize_job(job, user, db, write=True)

    require_cliente.assert_awaited_once_with(job.cliente_id, user, db)
    require_role.assert_not_awaited()


@pytest.mark.asyncio
async def test_upload_with_proposta_requires_editor_role():
    db = AsyncMock()
    user = _user()
    proposta_id = uuid4()
    cliente_id = uuid4()
    file = MagicMock()
    file.filename = "pq.csv"
    file.read = AsyncMock(return_value=b"codigo,descricao\n1,Servico\n")

    with patch.object(smart_import, "require_proposta_role", new=AsyncMock()) as require_role, \
         patch.object(smart_import, "require_cliente_access", new=AsyncMock()) as require_cliente, \
         patch.object(smart_import.SmartImportService, "create_job", new=AsyncMock()) as create_job:
        created = MagicMock()
        created.payload_staging = {"rows": []}
        create_job.return_value = created
        await smart_import.upload(
            file=file,
            cliente_id=cliente_id,
            proposta_id=proposta_id,
            sheet_name=None,
            profile_header_row=None,
            current_user=user,
            db=db,
        )

    require_role.assert_awaited_once()
    require_cliente.assert_not_awaited()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_smart_import_auth.py -q
```

Expected: FAIL because `_authorize_job` does not exist and `upload` still uses `_current_user`.

- [ ] **Step 3: Implement endpoint authorization**

Update `app/backend/api/v1/endpoints/smart_import.py` imports and helpers:

```python
from backend.core.dependencies import (
    get_current_active_user,
    get_db,
    require_cliente_access,
    require_proposta_role,
)
from backend.models.enums import PropostaPapel
```

Replace `_get_job` with lock-aware loading and add `_authorize_job`:

```python
async def _get_job(
    job_id: UUID,
    db: AsyncSession,
    *,
    for_update: bool = False,
) -> SmartImportJob:
    stmt = select(SmartImportJob).where(SmartImportJob.id == job_id)
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("SmartImportJob", str(job_id))
    return job


async def _authorize_job(
    job: SmartImportJob,
    current_user,
    db: AsyncSession,
    *,
    write: bool,
) -> None:
    if job.proposta_id:
        required = PropostaPapel.EDITOR if write else None
        await require_proposta_role(job.proposta_id, required, current_user, db)
        return
    await require_cliente_access(job.cliente_id, current_user, db)
```

Update endpoint signatures from `_current_user=Depends(...)` to `current_user=Depends(...)`. Before creating a job:

```python
if proposta_id:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
else:
    await require_cliente_access(cliente_id, current_user, db)
```

After loading jobs:

```python
job = await _get_job(job_id, db)
await _authorize_job(job, current_user, db, write=False)
```

For row mutation and commit endpoints use `write=True`. In `commit_job`, load with lock:

```python
job = await _get_job(job_id, db, for_update=True)
await _authorize_job(job, current_user, db, write=True)
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_smart_import_auth.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/api/v1/endpoints/smart_import.py app/backend/tests/unit/smart_import/test_smart_import_auth.py
git commit -m "fix(smart-import): enforce job authorization"
```

---

### Task 2: Add Shared Brazilian Decimal Parser

**Files:**
- Create: `app/backend/services/smart_import/number_parser.py`
- Modify: `app/backend/services/smart_import/row_classifier.py`
- Modify: `app/backend/services/smart_import_service.py`
- Test: `app/backend/tests/unit/smart_import/test_number_parser.py`
- Test: `app/backend/tests/unit/smart_import/test_row_classifier.py`
- Test: `app/backend/tests/unit/smart_import/test_commit.py`

- [ ] **Step 1: Write failing parser tests**

Create `app/backend/tests/unit/smart_import/test_number_parser.py`:

```python
from decimal import Decimal

import pytest

from backend.services.smart_import.number_parser import parse_br_decimal


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10", Decimal("10")),
        ("1,5", Decimal("1.5")),
        ("1.234,56", Decimal("1234.56")),
        ("1234.56", Decimal("1234.56")),
        ("1.234", Decimal("1234")),
        (1234.56, Decimal("1234.56")),
    ],
)
def test_parse_br_decimal_supported_formats(raw, expected):
    assert parse_br_decimal(raw) == expected


@pytest.mark.parametrize("raw", [None, "", " ", "abc", "1.234.56"])
def test_parse_br_decimal_invalid_or_empty_returns_none(raw):
    assert parse_br_decimal(raw) is None
```

Add to `app/backend/tests/unit/smart_import/test_row_classifier.py`:

```python
def test_item_with_brazilian_decimal_thousands():
    result = RowClassifier.classify(_row("Concreto usinado", "m3", "1.234,56"))
    assert result == RowClass.ITEM
```

Add to `app/backend/tests/unit/smart_import/test_commit.py` inside `test_commit_job_with_proposta_id_creates_pq_items`, change the quantity to `"1.234,56"` and assert:

```python
assert pq_items[0].quantidade_original == Decimal("1234.56")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_number_parser.py app/backend/tests/unit/smart_import/test_row_classifier.py app/backend/tests/unit/smart_import/test_commit.py -q
```

Expected: FAIL because parser module does not exist and current parsing treats `"1.234,56"` as invalid.

- [ ] **Step 3: Implement parser**

Create `app/backend/services/smart_import/number_parser.py`:

```python
from __future__ import annotations

from decimal import Decimal, InvalidOperation


def parse_br_decimal(value: object) -> Decimal | None:
    if value is None:
        return None

    raw = str(value).strip().replace(" ", "")
    if not raw:
        return None

    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(".") == 1:
        left, right = raw.split(".", 1)
        if len(right) == 3 and left.isdigit() and right.isdigit():
            raw = left + right

    try:
        return Decimal(raw)
    except InvalidOperation:
        return None
```

Update `row_classifier.py`:

```python
from backend.services.smart_import.number_parser import parse_br_decimal
```

Replace `_to_decimal` body with:

```python
def _to_decimal(value: object) -> Decimal | None:
    return parse_br_decimal(value)
```

Update `_write_pq_items` in `smart_import_service.py`:

```python
from backend.services.smart_import.number_parser import parse_br_decimal
```

Replace the local Decimal parsing block with:

```python
quantidade = parse_br_decimal(row.get("quantidade"))
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_number_parser.py app/backend/tests/unit/smart_import/test_row_classifier.py app/backend/tests/unit/smart_import/test_commit.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/number_parser.py app/backend/services/smart_import/row_classifier.py app/backend/services/smart_import_service.py app/backend/tests/unit/smart_import/test_number_parser.py app/backend/tests/unit/smart_import/test_row_classifier.py app/backend/tests/unit/smart_import/test_commit.py
git commit -m "fix(smart-import): parse brazilian decimal values"
```

---

### Task 3: Make JSONB Staging Mutations Trackable

**Files:**
- Modify: `app/backend/services/smart_import_service.py`
- Test: `app/backend/tests/unit/smart_import/test_smart_import_service.py`

- [ ] **Step 1: Write failing immutable mutation tests**

Add tests to `app/backend/tests/unit/smart_import/test_smart_import_service.py`:

```python
def test_patch_row_reassigns_payload_staging():
    svc = SmartImportService()
    job = MagicMock()
    original_payload = {
        "rows": [
            {
                "idx": 0,
                "row_class": "ITEM",
                "descricao": "Escavacao",
                "unidade": "m2",
                "quantidade": "10",
                "codigo": "1",
                "preco": None,
                "valor": None,
            }
        ]
    }
    job.payload_staging = original_payload

    svc.patch_row(job, 0, {"quantidade": "12"})

    assert job.payload_staging is not original_payload
    assert job.payload_staging["rows"][0]["quantidade"] == "12"


def test_add_row_reassigns_payload_staging():
    svc = SmartImportService()
    job = MagicMock()
    original_payload = {"rows": []}
    job.payload_staging = original_payload

    new_row = svc.add_row(job, {"descricao": "Servico", "quantidade": "1"})

    assert job.payload_staging is not original_payload
    assert job.payload_staging["rows"] == [new_row]


def test_reclassify_row_reassigns_payload_staging():
    svc = SmartImportService()
    job = MagicMock()
    original_payload = {
        "rows": [
            {
                "idx": 0,
                "row_class": "ITEM",
                "descricao": "Subtotal",
                "unidade": None,
                "quantidade": None,
                "codigo": None,
                "preco": None,
                "valor": "100",
            }
        ]
    }
    job.payload_staging = original_payload

    svc.reclassify_row(job, 0, RowClass.TOTAL)

    assert job.payload_staging is not original_payload
    assert job.payload_staging["rows"][0]["row_class"] == "TOTAL"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_smart_import_service.py -q
```

Expected: FAIL because current methods mutate nested dict/list in place.

- [ ] **Step 3: Implement immutable staging helpers**

In `app/backend/services/smart_import_service.py`, add helpers near `_cell_str`:

```python
def _staging_rows(job: SmartImportJob) -> list[dict]:
    return list((job.payload_staging or {}).get("rows", []))


def _replace_staging_rows(job: SmartImportJob, rows: list[dict]) -> None:
    payload = dict(job.payload_staging or {})
    payload["rows"] = rows
    job.payload_staging = payload
```

Update mutation methods so every changed row is copied and final rows are re-assigned:

```python
rows = _staging_rows(job)
new_rows = []
found = False
for row in rows:
    if row["idx"] != row_idx:
        new_rows.append(row)
        continue
    found = True
    target = dict(row)
    for key, val in patch.items():
        if key in allowed:
            target[key] = val
    target["row_class"] = RowClassifier.classify(target).value
    new_rows.append(target)
if not found:
    raise NotFoundError("StagingRow", row_idx)
_replace_staging_rows(job, new_rows)
```

Apply the same pattern to `add_row`, `delete_row`, and `reclassify_row`.

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_smart_import_service.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import_service.py app/backend/tests/unit/smart_import/test_smart_import_service.py
git commit -m "fix(smart-import): persist staging json updates"
```

---

### Task 4: Make Commit Idempotent And Race-Safe

**Files:**
- Modify: `app/backend/api/v1/endpoints/smart_import.py`
- Modify: `app/backend/services/smart_import_service.py`
- Test: `app/backend/tests/unit/smart_import/test_commit.py`

- [ ] **Step 1: Write failing idempotency tests**

Add to `app/backend/tests/unit/smart_import/test_commit.py`:

```python
@pytest.mark.asyncio
async def test_commit_job_rejects_already_committed_job(db):
    from backend.core.exceptions import ValidationError

    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile

    job = _job_without_proposta()
    job.mapping_metadata = {"committed_at": "2026-05-15T00:00:00Z"}

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        with pytest.raises(ValidationError, match="ja foi commitada"):
            await SmartImportService().commit_job(job, db, corrections=[])

    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_commit_job_marks_metadata_committed(db):
    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = _job_without_proposta()
    job.mapping_metadata = {}

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        result = await SmartImportService().commit_job(job, db, corrections=[])

    assert result.mapping_metadata["committed_at"]
    assert result.status == SmartImportStatus.COMPLETED
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_commit.py -q
```

Expected: FAIL because commit currently accepts already completed/committed jobs.

- [ ] **Step 3: Implement commit guard and metadata**

In `smart_import_service.py`, import timezone:

```python
from datetime import UTC, datetime
```

At the start of `commit_job`, before profile changes:

```python
metadata = dict(job.mapping_metadata or {})
if metadata.get("committed_at"):
    raise ValidationError("Importacao ja foi commitada.")
```

After `_write_pq_items` and before `db.commit()`:

```python
metadata["committed_at"] = datetime.now(UTC).isoformat()
metadata["corrections_count"] = len(all_corrections)
job.mapping_metadata = metadata
job.status = SmartImportStatus.COMPLETED
```

If `_write_pq_items` creates a `PqImportacao`, return it or its id:

```python
async def _write_pq_items(self, job: SmartImportJob, db: AsyncSession) -> PqImportacao:
    ...
    return importacao
```

Then in `commit_job`:

```python
if job.proposta_id:
    importacao = await self._write_pq_items(job, db)
    metadata["pq_importacao_id"] = str(importacao.id)
```

Confirm `app/backend/api/v1/endpoints/smart_import.py` uses `_get_job(..., for_update=True)` in commit from Task 1.

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_commit.py app/backend/tests/unit/smart_import/test_smart_import_auth.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import_service.py app/backend/api/v1/endpoints/smart_import.py app/backend/tests/unit/smart_import/test_commit.py
git commit -m "fix(smart-import): make commit idempotent"
```

---

### Task 5: Normalize Staging Status And Warnings

**Files:**
- Modify: `app/backend/services/smart_import_service.py`
- Modify: `app/backend/schemas/smart_import.py`
- Modify: `app/frontend/src/shared/services/api/smartImportApi.ts`
- Modify: `app/frontend/src/features/smart-import/SmartImportStagingPage.tsx`
- Test: `app/backend/tests/unit/smart_import/test_smart_import_service.py`

- [ ] **Step 1: Write failing backend status test**

Add to `app/backend/tests/unit/smart_import/test_smart_import_service.py`:

```python
@pytest.mark.asyncio
async def test_create_job_staged_clean_is_review_required_until_commit(db):
    content = _make_xlsx([
        ["ITEM", "DESCRICAO", "UNID.", "QUANT."],
        ["1.1", "Escavacao manual", "m2", 10],
    ])
    svc = SmartImportService()
    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value.get_by_cliente_id = AsyncMock(return_value=None)
        await svc.create_job(uuid4(), "clean.xlsx", content, db)

    added_job = db.add.call_args[0][0]
    assert added_job.status == SmartImportStatus.REVIEW_REQUIRED
    assert added_job.mapping_metadata["has_warnings"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_smart_import_service.py::test_create_job_staged_clean_is_review_required_until_commit -q
```

Expected: FAIL because clean staging is currently marked `COMPLETED`.

- [ ] **Step 3: Implement staged metadata**

In `create_job`, keep warning calculation but set status to awaiting review/commit:

```python
has_warnings = any(
    r["row_class"] == RowClass.ITEM.value
    and (r.get("quantidade") is None or r.get("descricao") is None)
    for r in staging_rows
)
status = SmartImportStatus.REVIEW_REQUIRED
```

Update metadata:

```python
mapping_metadata={
    "sheet_name": sheet.sheet_name,
    "col_map": col_map,
    "has_warnings": has_warnings,
    "warnings": ["ITEM sem quantidade ou descricao"] if has_warnings else [],
},
```

In `SmartImportJobOut`, add:

```python
has_warnings: bool = False
warnings: list[str] = Field(default_factory=list)
```

In `from_job`:

```python
metadata = job.mapping_metadata or {}
...
has_warnings=bool(metadata.get("has_warnings", False)),
warnings=list(metadata.get("warnings", [])),
```

Frontend type:

```ts
has_warnings: boolean;
warnings: string[];
```

Frontend alert condition:

```tsx
{job.status === 'REVIEW_REQUIRED' && job.has_warnings && !commitMutation.isSuccess && (
  <Alert severity="warning">
    Algumas linhas precisam de revisão. Verifique itens sem quantidade ou descrição.
  </Alert>
)}
```

- [ ] **Step 4: Run tests/build**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_smart_import_service.py -q
cd app/frontend; npm run build
```

Expected: pytest PASS and frontend build PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import_service.py app/backend/schemas/smart_import.py app/backend/tests/unit/smart_import/test_smart_import_service.py app/frontend/src/shared/services/api/smartImportApi.ts app/frontend/src/features/smart-import/SmartImportStagingPage.tsx
git commit -m "fix(smart-import): separate staging warnings from commit status"
```

---

### Task 6: Bound Extraction And Validate Profile Header Rows

**Files:**
- Modify: `app/backend/services/smart_import/extractor.py`
- Modify: `app/backend/services/smart_import/header_detector.py`
- Test: `app/backend/tests/unit/smart_import/test_extractor.py`
- Test: `app/backend/tests/unit/smart_import/test_header_detector.py`

- [ ] **Step 1: Write failing bounds tests**

Add to `test_header_detector.py`:

```python
def test_rejects_negative_profile_fixed_row():
    from backend.core.exceptions import ValidationError
    with pytest.raises(ValidationError, match="linha"):
        HeaderDetector.detect([["Codigo", "Descricao"]], profile_header_row=-1)


def test_rejects_out_of_range_profile_fixed_row():
    from backend.core.exceptions import ValidationError
    with pytest.raises(ValidationError, match="linha"):
        HeaderDetector.detect([["Codigo", "Descricao"]], profile_header_row=5)
```

Add to `test_extractor.py`:

```python
def test_extract_rejects_missing_sheet_name():
    content = _make_xlsx([["ITEM", "DESCRICAO"]])
    with pytest.raises(ValidationError, match="Aba"):
        FileExtractor.from_bytes("test.xlsx", content, sheet_name="NaoExiste")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_extractor.py app/backend/tests/unit/smart_import/test_header_detector.py -q
```

Expected: FAIL for fixed-row validation and missing sheet behavior.

- [ ] **Step 3: Implement bounds**

In `extractor.py`, define:

```python
_MAX_ROWS = 5000
_MAX_COLUMNS = 80
```

Wrap workbook load/close safely:

```python
wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
try:
    if sheet_name and sheet_name not in wb.sheetnames:
        raise ValidationError(f"Aba '{sheet_name}' nao encontrada no XLSX.")
    ws = wb[sheet_name] if sheet_name else wb.active
    ...
finally:
    wb.close()
```

Inside row loop:

```python
for row_number, raw_row in enumerate(ws.iter_rows(values_only=True), start=1):
    if row_number > _MAX_ROWS:
        raise ValidationError(f"Planilha excede o limite de {_MAX_ROWS} linhas.")
    row = list(raw_row)
    if len(row) > _MAX_COLUMNS:
        raise ValidationError(f"Planilha excede o limite de {_MAX_COLUMNS} colunas.")
```

In CSV parsing, use the same row/column limits.

In `header_detector.py`:

```python
if profile_header_row is not None:
    if profile_header_row < 0 or profile_header_row >= len(rows):
        raise ValidationError("Linha de cabecalho configurada esta fora do intervalo da planilha.")
    return profile_header_row
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_extractor.py app/backend/tests/unit/smart_import/test_header_detector.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/extractor.py app/backend/services/smart_import/header_detector.py app/backend/tests/unit/smart_import/test_extractor.py app/backend/tests/unit/smart_import/test_header_detector.py
git commit -m "fix(smart-import): bound spreadsheet extraction"
```

---

### Task 7: Harden Profile Learning Inputs

**Files:**
- Modify: `app/backend/services/smart_import/profile_learner.py`
- Test: `app/backend/tests/unit/smart_import/test_profile_learner.py`

- [ ] **Step 1: Write failing profile learner tests**

Add to `app/backend/tests/unit/smart_import/test_profile_learner.py`:

```python
import pytest

from backend.services.smart_import.profile_learner import ProfileLearner


def _profile():
    return {
        "header_row_strategy": {"mode": "scan"},
        "column_aliases": {},
        "aba_pattern": None,
        "uso_count": 0,
        "score_confianca": 0,
    }


def test_ignores_unknown_column_remap_field():
    result = ProfileLearner.apply(_profile(), [
        {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "danger", "header_text": "DROP"}}
    ])
    assert "danger" not in result["column_aliases"]


def test_rejects_negative_header_row_fix():
    with pytest.raises(ValueError, match="header"):
        ProfileLearner.apply(_profile(), [
            {"tipo": "HEADER_ROW_FIX", "detalhe": {"corrected": -1}}
        ])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_profile_learner.py -q
```

Expected: FAIL because unknown fields are currently accepted and negative rows are stored.

- [ ] **Step 3: Implement validation**

In `profile_learner.py`, add:

```python
_ALLOWED_FIELDS = {"codigo", "descricao", "unidade", "quantidade", "preco", "valor"}
_MAX_HEADER_ROW = 200
```

For `COLUMN_REMAP`:

```python
if campo not in _ALLOWED_FIELDS:
    continue
```

For `HEADER_ROW_FIX`:

```python
row = int(corrected_row)
if row < 0 or row > _MAX_HEADER_ROW:
    raise ValueError("header row fora do intervalo permitido")
p["header_row_strategy"] = {"mode": "fixed", "row": row}
```

For aliases, store normalized text by stripping whitespace but preserve original accents only if the mapper can normalize later:

```python
header_text = str(header_text).strip()
if header_text and header_text not in field_aliases:
    field_aliases.append(header_text)
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest app/backend/tests/unit/smart_import/test_profile_learner.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/profile_learner.py app/backend/tests/unit/smart_import/test_profile_learner.py
git commit -m "fix(smart-import): validate learned profile corrections"
```

---

### Task 8: Regression Gate And Sprint Evidence

**Files:**
- Create: `docs/sprints/F4-05/technical-review/technical-review-2026-05-15-f4-05.md`
- Create: `docs/sprints/F4-05/walkthrough/done/walkthrough-F4-05.md`
- Modify: `docs/shared/governance/BACKLOG.md`

- [ ] **Step 1: Run focused backend tests**

Run:

```powershell
pytest app/backend/tests/unit/smart_import -q
```

Expected: all Smart Import unit tests PASS.

- [ ] **Step 2: Run import-adjacent security tests**

Run:

```powershell
pytest app/backend/tests/unit/test_security_p0.py app/backend/tests/unit/test_security_s04.py app/backend/tests/unit/test_proposta_acl_dependency.py -q
```

Expected: PASS or documented environment-only blocker.

- [ ] **Step 3: Run frontend build only if frontend files changed**

Run:

```powershell
cd app/frontend
npm run build
```

Expected: PASS.

- [ ] **Step 4: Write technical review**

Create `docs/sprints/F4-05/technical-review/technical-review-2026-05-15-f4-05.md`:

```markdown
# Technical Review — F4-05 Smart Import Hardening

## Scope
- Smart Import authorization
- JSONB staging persistence
- Idempotent commit
- Brazilian decimal parsing
- Extraction bounds
- Profile learner validation

## Findings Addressed
- P0 authorization gap closed
- P0 duplicate commit risk closed
- P0 decimal parsing corrected
- P1 JSONB nested mutation risk closed
- P1 spreadsheet bounds added

## Gates
- `pytest app/backend/tests/unit/smart_import -q`: [result]
- Security regression: [result]
- Frontend build: [result or N/A]

## Residual Risk
- [state any environment blocker or deferred non-critical issue]
```

- [ ] **Step 5: Write walkthrough**

Create `docs/sprints/F4-05/walkthrough/done/walkthrough-F4-05.md`:

```markdown
# Walkthrough — F4-05 Smart Import Hardening

## Changed
- [files changed]

## Why
- [risks closed]

## Checked
- [commands and outcomes]

## Risk
- [remaining risk]

## QA Handoff
- Ready for QA review if focused tests pass.
```

- [ ] **Step 6: Update backlog status**

After implementation and evidence, update `F4-05` in `docs/shared/governance/BACKLOG.md` to `TESTED`. Do not mark `DONE`; QA owns that transition.

- [ ] **Step 7: Commit evidence**

```bash
git add docs/sprints/F4-05/technical-review/technical-review-2026-05-15-f4-05.md docs/sprints/F4-05/walkthrough/done/walkthrough-F4-05.md docs/shared/governance/BACKLOG.md
git commit -m "docs(f4-05): add smart import hardening evidence"
```

---

## Self-Review Checklist

- Spec coverage: covers authorization, JSONB persistence, idempotency, race lock, decimal parsing, file safety, learning loop, and test gaps.
- Placeholder scan: no task uses placeholder-marker language.
- Type consistency: `SmartImportStatus`, `PropostaPapel`, `payload_staging`, `mapping_metadata`, `RowClass`, and test paths match current repo names.
- Scope control: no Docling, no large refactor, no migration by default.

## Execution Handoff

Plan complete and saved to `docs/sprints/F4-05/plans/2026-05-15-f4-05-smart-import-hardening.md`.

Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh worker per task, review between tasks, fast iteration.
2. Inline Execution - execute tasks in one session using executing-plans, batch execution with checkpoints.
