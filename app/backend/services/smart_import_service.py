"""Smart Import Service — deterministic pipeline: Extract -> Detect Header -> Map Columns -> Classify Rows -> Stage."""
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

        end_row = header_row_idx + len(data_rows)
        data_range = {
            "start_row": header_row_idx + 1,
            "end_row": end_row,
            "col_map": col_map,
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
