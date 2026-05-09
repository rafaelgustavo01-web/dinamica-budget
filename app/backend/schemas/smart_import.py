from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field
from backend.models.smart_import import SmartImportStatus

class StagingRowError(BaseModel):
    loc: list[str | int]
    msg: str
    type: str

class StagingRow(BaseModel):
    linha_planilha: int
    raw_data: dict[str, Any] = Field(default_factory=dict)
    normalized_data: dict[str, Any] | None = None
    errors: list[StagingRowError] | None = None
    is_valid: bool = False

class SmartImportMetadata(BaseModel):
    mapper_version: str = "1.0"
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    column_mapping: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

class SmartImportPayload(BaseModel):
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    rows: list[StagingRow] = Field(default_factory=list)

class SmartImportJobResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    arquivo_origem: str
    status: SmartImportStatus
    mapping_metadata: SmartImportMetadata | None = None
    payload_staging: SmartImportPayload | None = None
