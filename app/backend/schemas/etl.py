"""
ETL schemas — upload, preview, execute, and status for the TCPO import pipeline.
These types are used only in the /admin/etl/* endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EtlMode(str, Enum):
    UPSERT = "upsert"   # INSERT … ON CONFLICT DO UPDATE (safe, incremental)
    REPLACE = "replace" # TRUNCATE + re-insert (full refresh)


# ── Parse preview (returned after file upload) ────────────────────────────────

class EtlItemPreview(BaseModel):
    codigo_origem: str
    descricao: str
    unidade_medida: str
    custo_base: float
    tipo_recurso: str | None = None


class EtlRelacaoPreview(BaseModel):
    pai_codigo: str
    filho_codigo: str
    quantidade_consumo: float
    unidade_medida: str


class EtlParsePreview(BaseModel):
    """Summary shown to admin before committing the ETL load."""
    total_itens: int
    total_relacoes: int
    itens_amostra: list[EtlItemPreview] = Field(default_factory=list)
    relacoes_amostra: list[EtlRelacaoPreview] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)


class EtlUploadResponse(BaseModel):
    """Returned by POST /admin/etl/upload-tcpo and /upload-converter."""
    arquivo: str
    parse_preview: EtlParsePreview
    parse_token: str  # opaque key that identifies the parsed data held in memory


# ── Execute ───────────────────────────────────────────────────────────────────

class EtlExecuteRequest(BaseModel):
    parse_token_tcpo: str | None = None
    parse_token_converter: str | None = None
    mode: EtlMode = EtlMode.UPSERT
    recomputar_embeddings: bool = True


class EtlExecuteResponse(BaseModel):
    mode: EtlMode
    itens_inseridos: int
    itens_atualizados: int
    relacoes_inseridas: int
    embeddings_computados: int
    duracao_segundos: float
    avisos: list[str] = Field(default_factory=list)


# ── Status ────────────────────────────────────────────────────────────────────

class EtlStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_itens_base_tcpo: int
    total_composicoes_base: int
    total_embeddings: int
    ultima_carga: datetime | None = None
