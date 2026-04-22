"""Schemas for association management endpoints."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssociacaoListItem(BaseModel):
    id: UUID
    cliente_id: UUID
    texto_busca_normalizado: str
    item_referencia_id: UUID
    origem_associacao: str
    frequencia_uso: int
    status_validacao: str
    confiabilidade_score: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)
