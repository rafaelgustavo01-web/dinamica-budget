from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServicoTcpoResponse(BaseModel):
    id: UUID
    codigo_origem: str
    descricao: str
    unidade_medida: str
    # custo_base comes from BaseTcpo; custo_unitario from ItemProprio
    custo_base: Decimal | None = None
    custo_unitario: Decimal | None = None
    categoria_id: int | None = None
    # origem only present on ItemProprio; None for BaseTcpo items
    origem: str | None = None
    cliente_id: UUID | None = None
    tipo_recurso: str | None = None
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


class ComposicaoComponenteResponse(BaseModel):
    """Direct children of a composition (level 1 only), with tipo_recurso for tree expansion."""

    id: UUID
    insumo_filho_id: UUID
    descricao_filho: str
    unidade_medida: str
    quantidade_consumo: Decimal
    custo_unitario: Decimal
    custo_total: Decimal
    tipo_recurso: str | None = None
    # Frozen contract (F2-DT-A/B): always present, None when child has no origin code
    codigo_origem: str | None = None

    model_config = ConfigDict(from_attributes=True)


class VersaoInfo(BaseModel):
    versao_id: UUID
    numero_versao: int
    # origem and cliente_id removed from VersaoComposicao in dual-schema model
    origem: str | None = None
    cliente_id: UUID | None = None


class VersaoComposicaoResponse(BaseModel):
    id: UUID
    numero_versao: int
    # origem and cliente_id removed from VersaoComposicao in dual-schema model
    origem: str | None = None
    cliente_id: UUID | None = None
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
