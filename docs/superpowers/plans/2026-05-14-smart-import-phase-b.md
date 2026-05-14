# Smart Import Engine — Phase B (Learning Loop) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After a user reviews and commits a staging job, the system detects what was changed (column remaps, header row fixes, row reclassifications), persists those corrections, and feeds them back into a per-client import profile so future uploads for the same client auto-apply the learned settings.

**Architecture:** A new `ImportProfile` model (per client) stores learned `column_aliases` and `header_row_strategy` as JSONB. A pure `ProfileLearner` function applies correction diffs to the profile. The commit endpoint triggers the learning cycle. On upload, the service auto-loads the client's profile and applies it to `HeaderDetector` and `ColumnMapper`.

**Tech Stack:** Same as Phase A — FastAPI, SQLAlchemy async, PostgreSQL JSONB, Alembic, pytest-asyncio.

**Phase A files referenced:**
- `app/backend/models/smart_import.py` — `SmartImportJob`
- `app/backend/services/smart_import_service.py` — `SmartImportService`
- `app/backend/services/smart_import/column_mapper.py` — `ColumnMapper`
- `app/backend/services/smart_import/header_detector.py` — `HeaderDetector`
- `app/backend/api/v1/endpoints/smart_import.py` — REST router

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `app/alembic/versions/033_import_profile_tables.py` | **Create** | `import_profile` + `import_profile_correction` tables; add `profile_id` FK to `smart_import_jobs` |
| `app/backend/models/import_profile.py` | **Create** | `ImportProfile` + `ImportProfileCorrection` ORM models |
| `app/backend/repositories/import_profile_repository.py` | **Create** | get/create/update `ImportProfile` per `cliente_id` |
| `app/backend/services/smart_import/profile_learner.py` | **Create** | Pure function: takes corrections → updates profile aliases/header_row/score |
| `app/backend/services/smart_import_service.py` | **Modify** | Add `commit_job()` (correction detection + profile update) and `get_profile_for_client()` |
| `app/backend/schemas/smart_import.py` | **Modify** | Add `ImportProfileOut`, `CommitJobRequest`, `CommitJobResponse` |
| `app/backend/api/v1/endpoints/smart_import.py` | **Modify** | Add `POST /{job_id}/commit`; auto-apply profile in `upload` |
| `app/backend/tests/unit/smart_import/test_profile_learner.py` | **Create** | Unit tests for `ProfileLearner` |
| `app/backend/tests/unit/smart_import/test_commit.py` | **Create** | Integration-level unit tests for commit + learning cycle |

---

## Task B1: Migration + ORM Models

**Files:**
- Create: `app/alembic/versions/033_import_profile_tables.py`
- Create: `app/backend/models/import_profile.py`
- Modify: `app/backend/models/smart_import.py`

- [ ] **Step 1: Write the migration**

```python
# app/alembic/versions/033_import_profile_tables.py
"""Add import_profile and import_profile_correction tables."""
from typing import Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

revision: str = "033"
down_revision: Union[str, None] = "032"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

_SCHEMA = "operacional"


def upgrade() -> None:
    op.create_table(
        "import_profile",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("cliente_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("aba_pattern", sa.String(200), nullable=True),
        sa.Column("header_row_strategy", JSONB(), nullable=False,
                  server_default=sa.text('\'{"mode": "scan"}\'::jsonb')),
        sa.Column("column_aliases", JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("score_confianca", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("uso_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_aprovado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema=_SCHEMA,
    )

    correction_type_enum = sa.Enum(
        "COLUMN_REMAP", "HEADER_ROW_FIX", "ROW_RECLASSIFY", "SHEET_CHANGE",
        name="import_correction_type_enum",
    )
    correction_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "import_profile_correction",
        sa.Column("id", PGUUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.import_profile.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("job_id", PGUUID(as_uuid=True),
                  sa.ForeignKey("operacional.smart_import_jobs.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("tipo", sa.Enum("COLUMN_REMAP", "HEADER_ROW_FIX", "ROW_RECLASSIFY", "SHEET_CHANGE",
                                  name="import_correction_type_enum", create_type=False), nullable=False),
        sa.Column("detalhe", JSONB(), nullable=True),
        sa.Column("aplicada", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema=_SCHEMA,
    )

    op.add_column("smart_import_jobs",
                  sa.Column("profile_id", PGUUID(as_uuid=True), nullable=True),
                  schema=_SCHEMA)
    op.create_foreign_key(
        "fk_smart_import_jobs_profile_id",
        "smart_import_jobs", "import_profile",
        ["profile_id"], ["id"],
        source_schema=_SCHEMA, referent_schema=_SCHEMA,
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_smart_import_jobs_profile_id", "smart_import_jobs",
                       schema=_SCHEMA, type_="foreignkey")
    op.drop_column("smart_import_jobs", "profile_id", schema=_SCHEMA)
    op.drop_table("import_profile_correction", schema=_SCHEMA)
    op.drop_table("import_profile", schema=_SCHEMA)
    sa.Enum(name="import_correction_type_enum").drop(op.get_bind(), checkfirst=True)
```

- [ ] **Step 2: Create ORM models**

```python
# app/backend/models/import_profile.py
from __future__ import annotations

import uuid
import enum
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class ImportCorrectionType(str, enum.Enum):
    COLUMN_REMAP = "COLUMN_REMAP"
    HEADER_ROW_FIX = "HEADER_ROW_FIX"
    ROW_RECLASSIFY = "ROW_RECLASSIFY"
    SHEET_CHANGE = "SHEET_CHANGE"


class ImportProfile(Base, TimestampMixin):
    __tablename__ = "import_profile"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aba_pattern: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # {"mode": "scan"} or {"mode": "fixed", "row": 11}
    header_row_strategy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: {"mode": "scan"})
    # {"descricao": ["DESCRIÇÃO DAS ATIVIDADES"], "quantidade": ["QUANT."]}
    column_aliases: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    score_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
    uso_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_aprovado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    corrections: Mapped[list["ImportProfileCorrection"]] = relationship(
        back_populates="profile",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="ImportProfileCorrection.created_at.desc()",
    )


class ImportProfileCorrection(Base):
    __tablename__ = "import_profile_correction"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.import_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.smart_import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[ImportCorrectionType] = mapped_column(
        SAEnum(ImportCorrectionType, name="import_correction_type_enum", create_type=False),
        nullable=False,
    )
    detalhe: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    aplicada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[sa.DateTime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    profile: Mapped["ImportProfile"] = relationship(back_populates="corrections", lazy="noload")
```

- [ ] **Step 3: Add `profile_id` to `SmartImportJob` ORM**

In `app/backend/models/smart_import.py`, add after the `proposta_id` column:

```python
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.import_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
```

- [ ] **Step 4: Commit**

```bash
git add app/alembic/versions/033_import_profile_tables.py app/backend/models/import_profile.py app/backend/models/smart_import.py
git commit -m "feat(smart-import/phase-b): ImportProfile + ImportProfileCorrection models and migration"
```

---

## Task B2: `ImportProfileRepository`

**Files:**
- Create: `app/backend/repositories/import_profile_repository.py`

- [ ] **Step 1: Implement**

```python
# app/backend/repositories/import_profile_repository.py
from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.import_profile import ImportProfile, ImportProfileCorrection


class ImportProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_cliente_id(self, cliente_id: UUID) -> ImportProfile | None:
        result = await self._db.execute(
            select(ImportProfile).where(ImportProfile.cliente_id == cliente_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: UUID) -> ImportProfile | None:
        result = await self._db.execute(
            select(ImportProfile).where(ImportProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def create(self, cliente_id: UUID) -> ImportProfile:
        profile = ImportProfile(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
        )
        self._db.add(profile)
        await self._db.flush()
        return profile

    async def save_corrections(
        self,
        profile_id: UUID,
        job_id: UUID,
        corrections: list[dict],
    ) -> list[ImportProfileCorrection]:
        from backend.models.import_profile import ImportCorrectionType
        saved = []
        for c in corrections:
            corr = ImportProfileCorrection(
                id=uuid.uuid4(),
                profile_id=profile_id,
                job_id=job_id,
                tipo=ImportCorrectionType(c["tipo"]),
                detalhe=c.get("detalhe"),
                aplicada=False,
            )
            self._db.add(corr)
            saved.append(corr)
        await self._db.flush()
        return saved

    async def flush(self) -> None:
        await self._db.flush()
```

- [ ] **Step 2: Smoke-test import**

```bash
cd app && python -c "from backend.repositories.import_profile_repository import ImportProfileRepository; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/backend/repositories/import_profile_repository.py
git commit -m "feat(smart-import/phase-b): ImportProfileRepository — get/create/save corrections"
```

---

## Task B3: `ProfileLearner` — pure correction applier

**Files:**
- Create: `app/backend/services/smart_import/profile_learner.py`
- Create: `app/backend/tests/unit/smart_import/test_profile_learner.py`

The profile dict shape:
```python
{
  "header_row_strategy": {"mode": "scan"},  # or {"mode": "fixed", "row": 11}
  "column_aliases": {"quantidade": ["QUANT.", "CRITÉRIO DE MEDIÇÃO"], "descricao": [...]},
  "aba_pattern": None,
  "uso_count": 3,
  "score_confianca": 0.75,
}
```

- [ ] **Step 1: Write failing tests**

```python
# app/backend/tests/unit/smart_import/test_profile_learner.py
import pytest
from backend.services.smart_import.profile_learner import ProfileLearner, _compute_score


def _base_profile():
    return {
        "header_row_strategy": {"mode": "scan"},
        "column_aliases": {},
        "aba_pattern": None,
        "uso_count": 0,
        "score_confianca": 0.0,
    }


def test_column_remap_adds_alias():
    profile = _base_profile()
    corrections = [
        {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QUANT."}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert "QUANT." in result["column_aliases"].get("quantidade", [])


def test_column_remap_does_not_duplicate_alias():
    profile = _base_profile()
    profile["column_aliases"] = {"quantidade": ["QUANT."]}
    corrections = [
        {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QUANT."}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result["column_aliases"]["quantidade"].count("QUANT.") == 1


def test_header_row_fix_updates_strategy_to_fixed():
    profile = _base_profile()
    corrections = [
        {"tipo": "HEADER_ROW_FIX", "detalhe": {"detected": 0, "corrected": 10}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result["header_row_strategy"]["mode"] == "fixed"
    assert result["header_row_strategy"]["row"] == 10


def test_sheet_change_updates_aba_pattern():
    profile = _base_profile()
    corrections = [
        {"tipo": "SHEET_CHANGE", "detalhe": {"sheet_name": "QQP"}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result["aba_pattern"] == "QQP"


def test_uso_count_increments_on_apply():
    profile = _base_profile()
    profile["uso_count"] = 2
    result = ProfileLearner.apply(profile, [])
    assert result["uso_count"] == 3


def test_score_increases_with_clean_import():
    score_0 = _compute_score(uso_count=1, correction_count=0)
    score_1 = _compute_score(uso_count=3, correction_count=0)
    assert score_1 > score_0


def test_score_penalized_by_corrections():
    clean = _compute_score(uso_count=5, correction_count=0)
    corrected = _compute_score(uso_count=5, correction_count=3)
    assert corrected < clean


def test_score_capped_at_one():
    score = _compute_score(uso_count=1000, correction_count=0)
    assert score <= 1.0


def test_row_reclassify_does_not_crash():
    profile = _base_profile()
    corrections = [
        {"tipo": "ROW_RECLASSIFY", "detalhe": {"descricao": "Limpeza de terreno", "de": "SECAO", "para": "ITEM"}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result is not None
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_profile_learner.py -v 2>&1 | head -20
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `ProfileLearner`**

```python
# app/backend/services/smart_import/profile_learner.py
from __future__ import annotations

from decimal import Decimal


def _compute_score(uso_count: int, correction_count: int) -> float:
    """Score rises with uso_count, penalized 2x per correction."""
    if uso_count == 0:
        return 0.0
    raw = uso_count / (uso_count + correction_count * 2)
    return min(round(raw, 4), 1.0)


class ProfileLearner:
    @staticmethod
    def apply(profile: dict, corrections: list[dict]) -> dict:
        """Return an updated copy of the profile dict after applying corrections.

        profile keys: header_row_strategy, column_aliases, aba_pattern, uso_count, score_confianca
        correction keys: tipo (str), detalhe (dict)
        """
        import copy
        p = copy.deepcopy(profile)
        aliases: dict[str, list[str]] = p.setdefault("column_aliases", {})

        for c in corrections:
            tipo = c.get("tipo", "")
            detail = c.get("detalhe") or {}

            if tipo == "COLUMN_REMAP":
                campo = detail.get("campo")
                header_text = detail.get("header_text")
                if campo and header_text:
                    field_aliases = aliases.setdefault(campo, [])
                    if header_text not in field_aliases:
                        field_aliases.append(header_text)

            elif tipo == "HEADER_ROW_FIX":
                corrected_row = detail.get("corrected")
                if corrected_row is not None:
                    p["header_row_strategy"] = {"mode": "fixed", "row": int(corrected_row)}

            elif tipo == "SHEET_CHANGE":
                sheet_name = detail.get("sheet_name")
                if sheet_name:
                    p["aba_pattern"] = sheet_name

            # ROW_RECLASSIFY — tracked for audit, no structural profile change

        uso_count = p.get("uso_count", 0) + 1
        p["uso_count"] = uso_count
        p["score_confianca"] = _compute_score(uso_count, len(corrections))
        return p
```

- [ ] **Step 4: Run tests — all must pass**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_profile_learner.py -v 2>&1 | tail -20
```

Expected: 9 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/backend/services/smart_import/profile_learner.py app/backend/tests/unit/smart_import/test_profile_learner.py
git commit -m "feat(smart-import/phase-b): ProfileLearner — apply corrections to profile dict"
```

---

## Task B4: Commit endpoint + auto-apply profile on upload

**Files:**
- Modify: `app/backend/services/smart_import_service.py`
- Modify: `app/backend/schemas/smart_import.py`
- Modify: `app/backend/api/v1/endpoints/smart_import.py`
- Create: `app/backend/tests/unit/smart_import/test_commit.py`

### 4a — Extend `SmartImportService` with `commit_job`

Add to the end of `SmartImportService` in `smart_import_service.py`:

```python
    async def get_or_create_profile(
        self,
        cliente_id: UUID,
        db: AsyncSession,
    ) -> "ImportProfile":
        from backend.repositories.import_profile_repository import ImportProfileRepository
        repo = ImportProfileRepository(db)
        profile = await repo.get_by_cliente_id(cliente_id)
        if profile is None:
            profile = await repo.create(cliente_id)
        return profile

    async def commit_job(
        self,
        job: "SmartImportJob",
        db: AsyncSession,
        corrections: list[dict] | None = None,
    ) -> "SmartImportJob":
        from decimal import Decimal
        from backend.models.smart_import import SmartImportStatus
        from backend.repositories.import_profile_repository import ImportProfileRepository
        from backend.services.smart_import.profile_learner import ProfileLearner

        repo = ImportProfileRepository(db)

        # Get or create profile for this client
        profile = await repo.get_by_cliente_id(job.cliente_id)
        if profile is None:
            profile = await repo.create(job.cliente_id)

        # Build correction list — provided explicitly or detected from reclassified rows
        all_corrections = list(corrections or [])

        # Save corrections
        if all_corrections:
            await repo.save_corrections(profile.id, job.id, all_corrections)

        # Apply corrections to profile
        profile_dict = {
            "header_row_strategy": profile.header_row_strategy,
            "column_aliases": profile.column_aliases,
            "aba_pattern": profile.aba_pattern,
            "uso_count": profile.uso_count,
            "score_confianca": float(profile.score_confianca),
        }
        updated = ProfileLearner.apply(profile_dict, all_corrections)

        profile.header_row_strategy = updated["header_row_strategy"]
        profile.column_aliases = updated["column_aliases"]
        profile.aba_pattern = updated.get("aba_pattern")
        profile.uso_count = updated["uso_count"]
        profile.score_confianca = Decimal(str(updated["score_confianca"]))

        # Link job → profile and mark completed
        job.profile_id = profile.id
        job.status = SmartImportStatus.COMPLETED

        await db.commit()
        logger.info(f"SmartImportJob {job.id} committed. Profile {profile.id} score={profile.score_confianca}")
        return job
```

Also add a helper to `create_job` that auto-loads the profile. Replace the beginning of `create_job` to accept and apply `profile` data:

At the top of `create_job`, after extracting the sheet, add:

```python
        # Auto-apply profile settings if not explicitly overridden
        if profile_header_row is None and profile_aliases is None:
            from backend.repositories.import_profile_repository import ImportProfileRepository
            repo = ImportProfileRepository(db)
            saved_profile = await repo.get_by_cliente_id(cliente_id)
            if saved_profile:
                strategy = saved_profile.header_row_strategy or {}
                if strategy.get("mode") == "fixed":
                    profile_header_row = strategy.get("row")
                if saved_profile.column_aliases:
                    profile_aliases = {
                        k: v for k, v in saved_profile.column_aliases.items() if v
                    }
                if sheet_name is None and saved_profile.aba_pattern:
                    sheet_name = saved_profile.aba_pattern
```

### 4b — Add schemas

Add to `app/backend/schemas/smart_import.py`:

```python
class ImportProfileOut(BaseModel):
    id: UUID
    cliente_id: UUID
    aba_pattern: str | None
    header_row_strategy: dict
    column_aliases: dict
    score_confianca: float
    uso_count: int
    is_aprovado: bool


class CommitJobRequest(BaseModel):
    corrections: list[dict] = Field(default_factory=list)


class CommitJobResponse(BaseModel):
    job_id: UUID
    status: SmartImportStatus
    profile_id: UUID
    score_confianca: float
    uso_count: int
    corrections_applied: int
```

### 4c — Add `POST /{job_id}/commit` endpoint

Add to `app/backend/api/v1/endpoints/smart_import.py`:

```python
from backend.schemas.smart_import import CommitJobRequest, CommitJobResponse

@router.post("/{job_id}/commit", response_model=CommitJobResponse)
async def commit_job(
    job_id: UUID,
    body: CommitJobRequest,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommitJobResponse:
    job = await _get_job(job_id, db)
    svc = SmartImportService()
    job = await svc.commit_job(job, db, corrections=body.corrections)
    return CommitJobResponse(
        job_id=job.id,
        status=job.status,
        profile_id=job.profile_id,
        score_confianca=float(
            (await db.get(__import__("backend.models.import_profile", fromlist=["ImportProfile"])
                          .ImportProfile, job.profile_id)).score_confianca
        ),
        uso_count=(await db.get(__import__("backend.models.import_profile", fromlist=["ImportProfile"])
                                .ImportProfile, job.profile_id)).uso_count,
        corrections_applied=len(body.corrections),
    )
```

### 4d — Tests

```python
# app/backend/tests/unit/smart_import/test_commit.py
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from decimal import Decimal

import openpyxl
import pytest

from backend.models.smart_import import SmartImportStatus
from backend.services.smart_import_service import SmartImportService


def _make_xlsx(rows):
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
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_commit_job_marks_completed_and_learns(db):
    from backend.models.import_profile import ImportProfile
    from decimal import Decimal

    mock_profile = MagicMock(spec=ImportProfile)
    mock_profile.id = uuid4()
    mock_profile.header_row_strategy = {"mode": "scan"}
    mock_profile.column_aliases = {}
    mock_profile.aba_pattern = None
    mock_profile.uso_count = 0
    mock_profile.score_confianca = Decimal("0")

    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None

    with patch("backend.services.smart_import_service.ImportProfileRepository", return_value=mock_repo):
        svc = SmartImportService()
        result = await svc.commit_job(job, db, corrections=[
            {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QUANT."}}
        ])

    assert result.status == SmartImportStatus.COMPLETED
    assert result.profile_id == mock_profile.id
    assert "QUANT." in mock_profile.column_aliases.get("quantidade", [])


@pytest.mark.asyncio
async def test_commit_job_creates_profile_if_none_exists(db):
    from backend.models.import_profile import ImportProfile
    from decimal import Decimal

    new_profile = MagicMock(spec=ImportProfile)
    new_profile.id = uuid4()
    new_profile.header_row_strategy = {"mode": "scan"}
    new_profile.column_aliases = {}
    new_profile.aba_pattern = None
    new_profile.uso_count = 0
    new_profile.score_confianca = Decimal("0")

    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = None
    mock_repo.create.return_value = new_profile
    mock_repo.save_corrections.return_value = []

    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None

    with patch("backend.services.smart_import_service.ImportProfileRepository", return_value=mock_repo):
        svc = SmartImportService()
        result = await svc.commit_job(job, db, corrections=[])

    mock_repo.create.assert_called_once_with(job.cliente_id)
    assert result.status == SmartImportStatus.COMPLETED
```

- [ ] **Step 5: Run all Phase B tests**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/ -v --tb=short 2>&1 | tail -20
```

Expected: 40+ PASSED, 0 failed.

- [ ] **Step 6: Smoke-test router imports**

```bash
cd app && python -c "from backend.api.v1.endpoints.smart_import import router; print('OK')"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add app/backend/services/smart_import_service.py app/backend/schemas/smart_import.py app/backend/api/v1/endpoints/smart_import.py app/backend/tests/unit/smart_import/test_commit.py
git commit -m "feat(smart-import/phase-b): commit endpoint + auto-apply profile on upload"
```

---

## Self-Review

| Requirement | Covered |
|-------------|---------|
| Track column remaps | `COLUMN_REMAP` correction + `ProfileLearner.apply` |
| Track header row fixes | `HEADER_ROW_FIX` correction |
| Track sheet changes | `SHEET_CHANGE` correction |
| Persist corrections | `import_profile_correction` table + `save_corrections` |
| Update profile on commit | `commit_job` → `ProfileLearner.apply` → profile update |
| Auto-apply on next upload | `create_job` reads saved profile at upload time |
| Score confidence | `_compute_score(uso_count, correction_count)` |
| Create profile if missing | `get_or_create_profile` in `commit_job` |
| Profile per client | `cliente_id` FK, `get_by_cliente_id` |
