"""Request schemas for composition-by-copy endpoints."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ClonarComposicaoRequest(BaseModel):
    servico_origem_id: UUID
    cliente_id: UUID
    codigo_clone: str
    descricao: str | None = None  # if None, inherits from original


class AdicionarComponenteRequest(BaseModel):
    insumo_filho_id: UUID
    quantidade_consumo: Decimal = Field(gt=0)
    unidade_medida: str = Field(max_length=20)  # unidade do insumo_filho na composição
