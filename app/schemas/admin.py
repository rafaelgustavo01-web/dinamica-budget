from enum import Enum

from pydantic import BaseModel, Field


class ImportSourceType(str, Enum):
    TCPO = "TCPO"
    PC = "PC"


class FieldMappingPreview(BaseModel):
    source_header: str
    target_field: str
    confidence: float = Field(ge=0, le=1)


class SheetPreview(BaseModel):
    sheet_name: str
    total_rows: int
    header_row: int
    estimated_records: int
    mapped_fields: list[FieldMappingPreview]
    sample_rows: list[list[str]]


class ImportPreviewResponse(BaseModel):
    source_type: ImportSourceType
    file_name: str
    total_rows: int
    estimated_records: int
    warnings: list[str]
    sheets: list[SheetPreview]


class ImportExecuteResponse(BaseModel):
    status: str
    source_type: ImportSourceType
    file_name: str
    message: str
    log_excerpt: str | None = None


class ComputeEmbeddingsResponse(BaseModel):
    status: str
    embeddings_computados: int
