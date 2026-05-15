"""Smart Import Service — deterministic pipeline: Extract -> Detect Header -> Map Columns -> Classify Rows -> Stage."""
from __future__ import annotations

import copy
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select
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
        # Auto-apply saved profile if caller did not provide explicit overrides
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

        has_warnings = any(
            r["row_class"] == RowClass.ITEM.value
            and (r.get("quantidade") is None or r.get("descricao") is None)
            for r in staging_rows
        )
        status = SmartImportStatus.REVIEW_REQUIRED

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
            mapping_metadata={
            "sheet_name": sheet.sheet_name,
            "col_map": col_map,
            "has_warnings": has_warnings,
            "warnings": ["ITEM sem quantidade ou descricao"] if has_warnings else [],
        },
            payload_staging={"rows": staging_rows},
            payload_raw=copy.deepcopy({"rows": staging_rows}),
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
        from backend.services.smart_import.number_parser import parse_decimal_br

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
            quantidade = parse_decimal_br(row.get("quantidade"))

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

        # Acquire row-level lock and re-fetch status to ensure idempotency
        result = await db.execute(
            select(SmartImportJob).where(SmartImportJob.id == job.id).with_for_update()
        )
        locked_job = result.scalar_one()
        job = locked_job
        if locked_job.status == SmartImportStatus.COMPLETED:
            logger.info(f"SmartImportJob {job.id} already committed; skipping.")
            return locked_job

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
