from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.servico import ServicoTcpoResponse


class ItemPendenteResponse(BaseModel):
    """A service item awaiting homologation approval."""

    id: UUID
    codigo_origem: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    cliente_id: UUID
    status_homologacao: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AprovarHomologacaoRequest(BaseModel):
    servico_id: UUID
    cliente_id: UUID  # used to validate ownership before approval
    aprovado: bool = True
    motivo_reprovacao: str | None = Field(default=None, max_length=500)


class AprovarHomologacaoResponse(BaseModel):
    servico_id: UUID
    status_homologacao: str
    aprovado_por: str  # email do aprovador
    data_aprovacao: datetime
    mensagem: str


class CriarItemProprioRequest(BaseModel):
    """Create a PROPRIA item for a specific client (starts as PENDENTE)."""

    cliente_id: UUID
    codigo_origem: str
    descricao: str = Field(..., min_length=3, max_length=2000)
    unidade_medida: str
    custo_unitario: Decimal = Field(..., gt=0)
    categoria_id: int | None = None
