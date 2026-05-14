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
    field: str
    col_idx: int


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
