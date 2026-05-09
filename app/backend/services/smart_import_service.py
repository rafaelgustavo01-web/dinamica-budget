"""
Spike: Smart Import Service
This module demonstrates the new pipeline architecture:
Extractor (Docling concept) -> Normalizer -> Staging -> Validation -> Transactional Commit.
It operates completely isolated from existing `pq_import_service.py`.
"""

import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.logging import get_logger
from backend.models.smart_import import SmartImportJob, SmartImportStatus
from backend.schemas.smart_import import (
    SmartImportPayload,
    SmartImportMetadata,
    StagingRow,
    StagingRowError,
)

logger = get_logger(__name__)

class SmartImportService:
    def __init__(self):
        # We will mock the extraction part for this spike. 
        # In the future, docling or pandas logic goes here.
        pass

    async def _extract_with_docling_mock(self, contents: bytes, filename: str) -> list[dict[str, Any]]:
        """
        Mock for flexible extraction. It would handle PDFs/XLSXs ignoring messy headers.
        """
        # Returns raw dicts as if they were extracted from an unstructured table
        return [
            {"Cód.": "001", "Desc.": "Servico A", "Und": "m2", "Preço": "10.5", "row_num": 10},
            {"Cód.": "002", "Desc": "Servico B", "Und": "un", "Preço": "XXX", "row_num": 11}, # Error simulation
        ]

    def _normalize_and_validate(self, raw_rows: list[dict[str, Any]]) -> tuple[SmartImportPayload, SmartImportMetadata]:
        """
        Mock for Semantic Mapper and Pydantic Strict Validator.
        """
        metadata = SmartImportMetadata(
            mapper_version="docling-mock-v1",
            confidence_scores={"codigo": 0.95, "descricao": 0.80, "unidade": 0.99, "quantidade": 0.90},
            column_mapping={"Cód.": "codigo", "Desc.": "descricao", "Desc": "descricao", "Und": "unidade", "Preço": "quantidade"}
        )

        payload = SmartImportPayload(total_rows=len(raw_rows))
        
        for raw in raw_rows:
            staging_row = StagingRow(
                linha_planilha=raw.get("row_num", 0),
                raw_data=raw,
            )
            
            # Simple dummy validation logic
            try:
                # Normalization
                price = float(str(raw.get("Preço", "0")).replace(",", "."))
                staging_row.normalized_data = {
                    "codigo": raw.get("Cód."),
                    "descricao": raw.get("Desc.") or raw.get("Desc"),
                    "unidade": raw.get("Und"),
                    "quantidade": price
                }
                staging_row.is_valid = True
                payload.valid_rows += 1
            except ValueError:
                staging_row.is_valid = False
                staging_row.errors = [StagingRowError(loc=["quantidade"], msg="Valor numérico inválido", type="type_error.float")]
                payload.invalid_rows += 1
            
            payload.rows.append(staging_row)

        return payload, metadata

    async def create_import_job(self, cliente_id: uuid.UUID, filename: str, contents: bytes, db: AsyncSession) -> SmartImportJob:
        """
        Phase 1 to 4: Ingestion -> Normalization -> Validation -> Staging Write
        """
        logger.info(f"Starting Smart Import for {filename}")
        
        # 1. Flexible Extraction
        raw_rows = await self._extract_with_docling_mock(contents, filename)
        
        # 2 & 3. Semantic Normalization & Rigid Validation
        payload, metadata = self._normalize_and_validate(raw_rows)
        
        # 4. Staging
        status = SmartImportStatus.REVIEW_REQUIRED if payload.invalid_rows > 0 else SmartImportStatus.COMPLETED
        
        job = SmartImportJob(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            arquivo_origem=filename,
            status=status,
            mapping_metadata=metadata.model_dump(),
            payload_staging=payload.model_dump()
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        logger.info(f"Smart Import Job {job.id} staged with status {job.status}")
        return job

    async def confirm_and_commit_import(self, job_id: uuid.UUID, db: AsyncSession) -> bool:
        """
        Phase 5 & 6: Human Confirmation -> Transactional Commit to Final Tables
        """
        result = await db.execute(select(SmartImportJob).where(SmartImportJob.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError("Job not found")
        
        if job.status == SmartImportStatus.PROCESSING:
            raise ValueError("Job is currently processing")
            
        payload = SmartImportPayload.model_validate(job.payload_staging)
        
        if payload.invalid_rows > 0:
            raise ValueError("Cannot commit job with invalid rows. Fix them in staging first.")
            
        # 6. Efetivação Transacional
        # Transaction is implicitly handled by the session wrapper in production code.
        try:
            # Here we would map `payload.rows` -> `PqItem` or other final models and `db.add_all()`
            # For the spike, we just simulate success.
            job.status = SmartImportStatus.COMPLETED
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to commit import job {job_id}: {str(e)}")
            job.status = SmartImportStatus.FAILED
            await db.commit()
            raise

smart_import_service = SmartImportService()
