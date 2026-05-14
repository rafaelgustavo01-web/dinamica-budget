# Code Review Request — Smart Import Engine (Phases A–D)

You are reviewing a production FastAPI + React feature for a Brazilian construction budget SaaS.
The feature imports PQ spreadsheets (Planilha de Quantitativos — lists of services and quantities),
stages them for user review, learns column/header patterns per client, and commits approved rows
as PqItem records for downstream price matching.

Provide a thorough code review with severity-classified findings.

---

## Project Stack

- Backend: FastAPI + SQLAlchemy async + PostgreSQL (operacional schema)
- Frontend: React 19 + TypeScript + MUI 7 + TanStack Query 5 + React Router 7
- Domain: Civil construction budgeting. PQ = spreadsheet of services. BCU = base price tables. Match = linking PQ items to catalog for budget calculation.

---

## File 1 — extractor.py

```python
from __future__ import annotations

import csv
import io
from dataclasses import dataclass

import openpyxl

from backend.core.exceptions import ValidationError

_MAX_FILE_SIZE = 10 * 1024 * 1024
_XLSX_MAGIC = b"PK\x03\x04"
_SUPPORTED = {"xlsx", "csv"}


@dataclass
class SheetData:
    sheet_name: str
    rows: list[list]


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

---

## File 2 — header_detector.py

```python
from __future__ import annotations

import unicodedata

from backend.core.exceptions import ValidationError

_MAX_SCAN_ROWS = 30
_MIN_SCORE = 2

_TARGET_ALIASES: dict[str, set[str]] = {
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


def _normalize(cell: object) -> str:
    if cell is None:
        return ""
    text = str(cell).strip().lower()
    text = " ".join(text.split())
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _score_row(row: list) -> tuple[int, bool]:
    count = 0
    has_descricao = False
    seen_fields: set[str] = set()
    norm_aliases = {field: {_normalize(a) for a in aliases} for field, aliases in _TARGET_ALIASES.items()}
    for cell in row:
        norm = _normalize(cell)
        if not norm:
            continue
        for field, aliases in norm_aliases.items():
            if field in seen_fields:
                continue
            matched = False
            if norm in aliases:
                matched = True
            else:
                for alias in aliases:
                    if alias in norm or norm in alias:
                        matched = True
                        break
            if matched:
                count += 1
                seen_fields.add(field)
                if field == "descricao":
                    has_descricao = True
                break
    return count, has_descricao


class HeaderDetector:
    @staticmethod
    def detect(rows: list[list], profile_header_row: int | None = None) -> int:
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
                "Nao foi possivel identificar o cabecalho da planilha. "
                "Verifique se o arquivo contem colunas de Descricao e Quantidade."
            )

        return best_idx
```

---

## File 3 — column_mapper.py

```python
from __future__ import annotations

import unicodedata

from backend.core.exceptions import ValidationError

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
        merged: dict[str, set[str]] = {field: set(aliases) for field, aliases in _GLOBAL_ALIASES.items()}
        if profile_aliases:
            for field, extra in profile_aliases.items():
                if field in merged:
                    merged[field].update(_normalize(a) for a in extra)
                else:
                    merged[field] = {_normalize(a) for a in extra}

        norm_headers = [_normalize(h) for h in headers]
        scores: list[tuple[float, str, int]] = []
        for field, aliases in merged.items():
            norm_aliases = {_normalize(a) for a in aliases}
            for col_idx, norm in enumerate(norm_headers):
                if not norm:
                    continue
                score = _match_score(norm, norm_aliases)
                if score > 0:
                    scores.append((score, field, col_idx))

        scores.sort(key=lambda x: -x[0])

        result: ColumnMap = {}
        assigned_cols: set[int] = set()
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
                    "A planilha deve conter uma coluna de descricao identificavel. "
                    "Verifique os cabecalhos do arquivo."
                )

        return result
```

---

## File 4 — row_classifier.py

```python
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
        descricao = _norm(row.get("descricao"))
        unidade = _norm(row.get("unidade"))
        qtd = _to_decimal(row.get("quantidade"))
        preco = _to_decimal(row.get("preco"))
        valor = _to_decimal(row.get("valor"))

        if not descricao and not unidade and qtd is None and preco is None and valor is None:
            return RowClass.VAZIA

        has_qtd = qtd is not None and qtd > 0
        has_unidade = bool(unidade)

        first_word = descricao.split()[0] if descricao.split() else ""
        if first_word in _TOTAL_KEYWORDS or any(kw in descricao for kw in _TOTAL_KEYWORDS):
            if not has_qtd:
                return RowClass.TOTAL

        if has_qtd:
            return RowClass.ITEM
        if has_unidade and descricao:
            return RowClass.ITEM

        if _SECTION_NUMBERING_RE.match(descricao):
            return RowClass.SECAO
        if len(descricao) <= 5:
            return RowClass.SECAO
        if descricao.isupper() and len(descricao) <= 60:
            return RowClass.SECAO
        if first_word in _SECTION_KEYWORDS:
            return RowClass.SECAO

        return RowClass.SECAO
```

---

## File 5 — profile_learner.py

```python
from __future__ import annotations

import copy


def _compute_score(uso_count: int, correction_count: int) -> float:
    if uso_count == 0:
        return 0.0
    raw = uso_count / (uso_count + correction_count * 2)
    return min(round(raw, 4), 1.0)


class ProfileLearner:
    @staticmethod
    def apply(profile: dict, corrections: list[dict]) -> dict:
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

        uso_count = p.get("uso_count", 0) + 1
        p["uso_count"] = uso_count
        p["score_confianca"] = _compute_score(uso_count, len(corrections))
        return p
```

---

## File 6 — smart_import_service.py

```python
from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.enums import StatusImportacao, StatusMatch
from backend.models.proposta import PqImportacao, PqItem
from backend.models.smart_import import SmartImportJob, SmartImportStatus
from backend.repositories.associacao_repository import normalize_text
from backend.repositories.import_profile_repository import ImportProfileRepository
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
        if profile_header_row is None and profile_aliases is None:
            saved = await ImportProfileRepository(db).get_by_cliente_id(cliente_id)
            if saved:
                strategy = saved.header_row_strategy or {}
                if strategy.get("mode") == "fixed":
                    profile_header_row = strategy.get("row")
                if saved.column_aliases:
                    profile_aliases = {k: v for k, v in saved.column_aliases.items() if v}
                if sheet_name is None and saved.aba_pattern:
                    sheet_name = saved.aba_pattern

        sheet = FileExtractor.from_bytes(filename, content, sheet_name)
        header_row_idx = HeaderDetector.detect(sheet.rows, profile_header_row=profile_header_row)
        header_cells = sheet.rows[header_row_idx] if header_row_idx < len(sheet.rows) else []
        col_map = ColumnMapper.from_headers(header_cells, profile_aliases=profile_aliases)

        data_rows = sheet.rows[header_row_idx + 1:]
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

        has_aviso = any(
            r["row_class"] == RowClass.ITEM.value
            and (r.get("quantidade") is None or r.get("descricao") is None)
            for r in staging_rows
        )
        status = SmartImportStatus.REVIEW_REQUIRED if has_aviso else SmartImportStatus.COMPLETED

        job = SmartImportJob(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            proposta_id=proposta_id,
            arquivo_origem=filename,
            status=status,
            detected_header_row=header_row_idx,
            detected_data_range={"start_row": header_row_idx + 1, "end_row": header_row_idx + len(data_rows), "col_map": col_map},
            mapping_metadata={"sheet_name": sheet.sheet_name, "col_map": col_map},
            payload_staging={"rows": staging_rows},
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"SmartImportJob {job.id} created: {len(staging_rows)} rows, status={status}")
        return job

    def patch_row(self, job: SmartImportJob, row_idx: int, patch: dict[str, Any]) -> None:
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        target = next((r for r in rows if r["idx"] == row_idx), None)
        if target is None:
            raise NotFoundError("StagingRow", row_idx)
        allowed = {"codigo", "descricao", "unidade", "quantidade", "preco", "valor"}
        for key, val in patch.items():
            if key in allowed:
                target[key] = val
        target["row_class"] = RowClassifier.classify(target).value

    def add_row(self, job: SmartImportJob, data: dict[str, Any]) -> dict:
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
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        before = len(rows)
        job.payload_staging["rows"] = [r for r in rows if r["idx"] != row_idx]
        if len(job.payload_staging["rows"]) == before:
            raise NotFoundError("StagingRow", row_idx)

    def reclassify_row(self, job: SmartImportJob, row_idx: int, new_class: RowClass) -> None:
        rows: list[dict] = (job.payload_staging or {}).get("rows", [])
        target = next((r for r in rows if r["idx"] == row_idx), None)
        if target is None:
            raise NotFoundError("StagingRow", row_idx)
        target["row_class"] = new_class.value

    async def _write_pq_items(self, job: SmartImportJob, db: AsyncSession) -> None:
        from decimal import Decimal, InvalidOperation

        rows = (job.payload_staging or {}).get("rows", [])
        item_rows = [r for r in rows if r.get("row_class") == "ITEM" and r.get("descricao")]
        non_item_count = len(rows) - len(item_rows)
        ext = job.arquivo_origem.rsplit(".", 1)[-1].lower() if "." in job.arquivo_origem else "xlsx"

        importacao = PqImportacao(
            proposta_id=job.proposta_id,
            nome_arquivo=job.arquivo_origem,
            formato=ext,
            linhas_total=len(rows),
            linhas_importadas=len(item_rows),
            linhas_com_erro=0,
            linhas_ignoradas=non_item_count,
            status=StatusImportacao.CONCLUIDO,
        )
        db.add(importacao)
        await db.flush()

        for row in item_rows:
            descricao = str(row["descricao"]).strip()
            qtd_raw = row.get("quantidade")
            try:
                quantidade = Decimal(str(qtd_raw).strip().replace(",", ".")) if qtd_raw else None
            except InvalidOperation:
                quantidade = None

            db.add(PqItem(
                proposta_id=job.proposta_id,
                pq_importacao_id=importacao.id,
                codigo_original=row.get("codigo"),
                descricao_original=descricao,
                unidade_medida_original=row.get("unidade"),
                quantidade_original=quantidade,
                descricao_tokens=normalize_text(descricao),
                match_status=StatusMatch.PENDENTE,
                linha_planilha=row.get("sheet_row"),
            ))

    async def commit_job(
        self,
        job: SmartImportJob,
        db: AsyncSession,
        corrections: list[dict] | None = None,
    ) -> SmartImportJob:
        from decimal import Decimal
        from backend.services.smart_import.profile_learner import ProfileLearner

        repo = ImportProfileRepository(db)
        profile = await repo.get_by_cliente_id(job.cliente_id)
        if profile is None:
            profile = await repo.create(job.cliente_id)

        all_corrections = list(corrections or [])

        if all_corrections:
            await repo.save_corrections(profile.id, job.id, all_corrections)

        profile_dict = {
            "header_row_strategy": profile.header_row_strategy or {"mode": "scan"},
            "column_aliases": profile.column_aliases or {},
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

        job.profile_id = profile.id
        job.status = SmartImportStatus.COMPLETED

        if job.proposta_id:
            await self._write_pq_items(job, db)

        await db.commit()
        logger.info(f"SmartImportJob {job.id} committed. Profile {profile.id} score={profile.score_confianca}")
        return job
```

---

## File 7 — api/v1/endpoints/smart_import.py

```python
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db
from backend.core.exceptions import NotFoundError
from backend.models.smart_import import SmartImportJob
from backend.repositories.import_profile_repository import ImportProfileRepository
from backend.schemas.smart_import import (
    ClassifyRequest, CommitJobRequest, CommitJobResponse,
    SmartImportJobOut, StagingRowAdd, StagingRowEdit, StagingRowOut,
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
    updated = next(r for r in job.payload_staging["rows"] if r["idx"] == row_idx)
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
    updated = next(r for r in job.payload_staging["rows"] if r["idx"] == row_idx)
    return StagingRowOut(**updated)


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
    profile = await ImportProfileRepository(db).get_by_id(job.profile_id)
    return CommitJobResponse(
        job_id=job.id,
        status=job.status,
        profile_id=job.profile_id,
        score_confianca=float(profile.score_confianca) if profile else 0.0,
        uso_count=profile.uso_count if profile else 0,
        corrections_applied=len(body.corrections),
    )
```

---

## File 8 — models/smart_import.py (schema reference)

```python
class SmartImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSANDO"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SmartImportJob(Base, TimestampMixin):
    __tablename__ = "smart_import_jobs"
    __table_args__ = {"schema": "operacional"}

    id: UUID (pk)
    cliente_id: UUID (FK clientes, NOT NULL, indexed)
    proposta_id: UUID | None (FK propostas, nullable, indexed)
    profile_id: UUID | None (FK import_profile, nullable)
    arquivo_origem: str (max 260)
    status: SmartImportStatus
    mapping_metadata: JSONB | None
    payload_staging: JSONB | None   # {"rows": [...staging rows...]}
    detected_header_row: int | None
    detected_data_range: JSONB | None
```

---

## File 9 — PqImportacao + PqItem schemas (destination tables)

```python
class PqImportacao(Base, TimestampMixin):
    proposta_id: UUID (NOT NULL)
    nome_arquivo: str (max 260)
    formato: str (max 10)
    linhas_total: int
    linhas_importadas: int
    linhas_com_erro: int
    linhas_ignoradas: int
    status: StatusImportacao   # CONCLUIDO | PROCESSANDO | COM_ERROS

class PqItem(Base, TimestampMixin):
    proposta_id: UUID (NOT NULL)
    pq_importacao_id: UUID | None
    codigo_original: str | None
    descricao_original: str (NOT NULL)
    unidade_medida_original: str | None
    quantidade_original: Decimal | None
    descricao_tokens: str | None    # normalize_text(descricao) — FTS
    match_status: StatusMatch       # always PENDENTE on creation
    linha_planilha: int | None
```

---

## Business Context

1. `payload_staging["rows"]` stores quantidade as **string** (e.g. `"10"`, `"1.234,56"`, `"1,5"`). Brazilian locale uses comma as decimal separator and dot as thousand separator.
2. Only rows where `row_class == "ITEM"` and `descricao` is non-empty become `PqItem` records.
3. `normalize_text()` is a synchronous FTS tokenizer that lowercases, strips accents, removes stopwords.
4. The endpoint layer calls `get_current_active_user` but does NOT verify `current_user.cliente_id == job.cliente_id` anywhere.
5. `create_job()` calls `await db.commit()` — the service owns the transaction.
6. Each row-mutation endpoint (edit/add/delete/reclassify) independently calls `await db.commit()`.
7. `commit_job()` calls `await db.commit()` a third time — three separate transaction boundaries.

---

## Review Instructions

Analyze all files above and provide:

1. **Summary** — One-paragraph overall assessment
2. **Strengths** — What is well-designed (bullet points)
3. **Concerns** — Issues, gaps, risks (bullet points with severity: HIGH / MEDIUM / LOW)
4. **Suggestions** — Concrete fixes with code examples
5. **Test Coverage Gaps** — Which scenarios are unverified
6. **Risk Assessment** — Overall level (LOW / MEDIUM / HIGH) with justification

Focus areas:
- Correctness: RowClassifier edge cases, decimal parsing for Brazilian locale, ITEM vs SECAO misclassification
- Security: authorization gaps, file upload safety, JSONB mutation safety
- Transactional integrity: commit ownership, idempotency of commit_job, race conditions
- Performance: blocking I/O in async context, JSONB payload size
- Learning loop quality: score formula reliability, correction accumulation
- Test gaps across the pure pipeline modules

Output in markdown format.
