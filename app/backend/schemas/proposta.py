from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.models.enums import StatusMatch, StatusProposta, TipoServicoMatch


class PropostaCreate(BaseModel):
    cliente_id: UUID
    titulo: str | None = Field(default=None, max_length=255)
    descricao: str | None = None


class PropostaUpdate(BaseModel):
    titulo: str | None = Field(default=None, max_length=255)
    descricao: str | None = None


class PropostaStatusUpdate(BaseModel):
    status: StatusProposta


class PropostaResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    criado_por_id: UUID
    codigo: str
    titulo: str | None
    descricao: str | None
    status: StatusProposta
    versao_cpu: int
    pc_cabecalho_id: UUID | None
    total_direto: Decimal | None
    total_indireto: Decimal | None
    total_geral: Decimal | None
    data_finalizacao: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PqImportacaoResponse(BaseModel):
    importacao_id: UUID
    status: str
    linhas_total: int
    linhas_importadas: int
    linhas_com_erro: int


class PqMatchResponse(BaseModel):
    processados: int
    sugeridos: int
    sem_match: int


class CpuGeracaoDetalheResponse(BaseModel):
    processados: int
    erros: int


class CpuGeracaoResponse(BaseModel):
    proposta_id: str
    total_direto: float
    total_indireto: float
    total_geral: float
    detalhe: CpuGeracaoDetalheResponse


class CpuItemResponse(BaseModel):
    id: UUID
    proposta_id: UUID
    pq_item_id: UUID | None
    servico_id: UUID
    servico_tipo: TipoServicoMatch
    codigo: str
    descricao: str
    unidade_medida: str
    quantidade: Decimal
    custo_material_unitario: Decimal | None
    custo_mao_obra_unitario: Decimal | None
    custo_equipamento_unitario: Decimal | None
    custo_direto_unitario: Decimal | None
    percentual_indireto: Decimal | None
    custo_indireto_unitario: Decimal | None
    preco_unitario: Decimal | None
    preco_total: Decimal | None
    composicao_fonte: str | None
    pc_cabecalho_id: UUID | None
    ordem: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComposicaoDetalheResponse(BaseModel):
    id: UUID
    proposta_item_id: UUID
    descricao_insumo: str
    unidade_medida: str
    quantidade_consumo: Decimal
    custo_unitario_insumo: Decimal | None
    custo_total_insumo: Decimal | None
    tipo_recurso: str | None
    nivel: int
    e_composicao: bool
    fonte_custo: str | None

    model_config = ConfigDict(from_attributes=True)


class RecalcularBdiRequest(BaseModel):
    percentual_bdi: Decimal = Field(ge=0, le=100)


class RecalcularBdiResponse(BaseModel):
    proposta_id: str
    percentual_bdi: Decimal
    total_direto: Decimal
    total_indireto: Decimal
    total_geral: Decimal
    itens_recalculados: int


class PqItemResponse(BaseModel):
    id: UUID
    proposta_id: UUID
    pq_importacao_id: UUID | None
    codigo_original: str | None
    descricao_original: str
    unidade_medida_original: str | None
    quantidade_original: Decimal | None
    match_status: StatusMatch
    match_confidence: Decimal | None
    servico_match_id: UUID | None
    servico_match_tipo: TipoServicoMatch | None
    linha_planilha: int | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PqMatchConfirmarRequest(BaseModel):
    acao: Literal["confirmar", "substituir", "rejeitar"]
    servico_match_id: UUID | None = None
    servico_match_tipo: TipoServicoMatch | None = None
    quantidade: Decimal | None = None

    @model_validator(mode="after")
    def substituir_requer_servico(self) -> "PqMatchConfirmarRequest":
        if self.acao == "substituir" and self.servico_match_id is None:
            raise ValueError("servico_match_id e obrigatorio para acao=substituir")
        return self

