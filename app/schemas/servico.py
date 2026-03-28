from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServicoTcpoResponse(BaseModel):
    id: UUID
    codigo_origem: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    categoria_id: int | None
    origem: str          # 'TCPO' | 'PROPRIA'
    cliente_id: UUID | None  # None for global TCPO items
    tipo_recurso: str | None = None  # 'MO' | 'INSUMO' | 'FERRAMENTA' | 'EQUIPAMENTO' | 'SERVICO'
    descricao_tokens: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ComposicaoItemResponse(BaseModel):
    id: UUID
    insumo_filho_id: UUID
    descricao_filho: str
    unidade_medida: str
    quantidade_consumo: Decimal
    custo_unitario: Decimal
    custo_total: Decimal  # quantidade_consumo * custo_unitario

    model_config = ConfigDict(from_attributes=True)


class VersaoInfo(BaseModel):
    versao_id: UUID
    numero_versao: int
    origem: str  # 'TCPO' | 'PROPRIA'
    cliente_id: UUID | None


class VersaoComposicaoResponse(BaseModel):
    id: UUID
    numero_versao: int
    origem: str
    cliente_id: UUID | None
    is_ativa: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ExplodeComposicaoResponse(BaseModel):
    servico: ServicoTcpoResponse
    itens: list[ComposicaoItemResponse]
    custo_total_composicao: Decimal
    versao_info: VersaoInfo | None = None


class ServicoListParams(BaseModel):
    q: str | None = None
    categoria_id: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ServicoCreate(BaseModel):
    codigo_origem: str
    descricao: str
    unidade_medida: str
    custo_unitario: Decimal
    categoria_id: int | None = None
