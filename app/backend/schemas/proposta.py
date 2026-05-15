from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.models.enums import PropostaPapel, StatusMatch, StatusProposta, TipoServicoMatch


class PropostaCreate(BaseModel):
    cliente_id: UUID
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    titulo: str | None = Field(default=None, max_length=255)
    descricao: str | None = None


class PropostaUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
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
    bcu_cabecalho_id: UUID | None
    total_direto: Decimal | None
    total_indireto: Decimal | None
    total_geral: Decimal | None
    data_finalizacao: datetime | None
    created_at: datetime
    updated_at: datetime
    meu_papel: PropostaPapel | None = None

    # Versionamento (Optional for backwards compatibility with F2-01..F2-08 tests)
    proposta_root_id: UUID | None = None
    numero_versao: int | None = None
    versao_anterior_id: UUID | None = None
    is_versao_atual: bool | None = None
    is_fechada: bool | None = None

    # Aprovação
    requer_aprovacao: bool = False
    aprovado_por_id: UUID | None = None
    aprovado_em: datetime | None = None
    motivo_revisao: str | None = None

    # CPU
    cpu_desatualizada: bool = False

    model_config = ConfigDict(from_attributes=True)


# ── Versionamento / Aprovação Request schemas ──────────────────────────────────

class PropostaNovaVersaoRequest(BaseModel):
    motivo_revisao: str | None = None


class PropostaAprovarRequest(BaseModel):
    pass  # aprovador_id comes from current_user


class PropostaRejeitarRequest(BaseModel):
    motivo: str | None = None


class PropostaAclResponse(BaseModel):
    id: UUID
    proposta_id: UUID
    usuario_id: UUID
    usuario_nome: str
    usuario_email: str
    papel: PropostaPapel
    created_at: datetime
    created_by: UUID
    model_config = ConfigDict(from_attributes=True)


class PropostaAclCreate(BaseModel):
    usuario_id: UUID
    papel: PropostaPapel


class PqImportacaoResponse(BaseModel):
    importacao_id: UUID
    status: str
    linhas_total: int
    linhas_importadas: int
    linhas_com_erro: int
    linhas_ignoradas: int = 0


class PqMatchResponse(BaseModel):
    processados: int
    sugeridos: int
    sem_match: int


class PqMatchStatusResponse(BaseModel):
    status: str  # queued | running | completed | failed
    processados: int = 0
    sugeridos: int = 0
    sem_match: int = 0
    error: str | None = None


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
    codigo_pq: str | None = None
    descricao_pq: str | None = None
    descricao_servico: str | None = None
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
    bcu_cabecalho_id: UUID | None
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
    percentual_bdi: float
    total_direto: float
    total_indireto: float
    total_geral: float
    itens_recalculados: int


class PropostaRebuildResponse(BaseModel):
    proposta_id: str
    total_direto: float
    total_indireto: float
    total_geral: float
    bdi_percentual: float
    itens_processados: int
    cpu_desatualizada: bool


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
    servico_match_codigo: str | None = None
    servico_match_descricao: str | None = None
    servico_match_unidade: str | None = None
    linha_planilha: int | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PqItemManualCreate(BaseModel):
    codigo_original: str | None = Field(default=None, max_length=50)
    descricao_original: str = Field(min_length=1)
    unidade_medida_original: str | None = Field(default=None, max_length=20)
    quantidade_original: Decimal | None = Field(default=None, gt=0)
    servico_match_id: UUID | None = None
    servico_match_tipo: TipoServicoMatch | None = None


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


# ── Schemas de Composição e Valores ───────────────────────────────────────────


class BuscarValoresPropostaResponse(BaseModel):
    """Response para busca de valores de uma proposta."""
    proposta_id: str
    codigo: str
    status: str
    percentual_bdi: float
    totais: dict
    resumo_por_tipo: dict
    items: list[dict]

    model_config = ConfigDict(from_attributes=True)


class ValidarComposicaoResponse(BaseModel):
    """Response para validação de composição."""
    proposta_id: str
    valido: bool
    erros: list[str]
    avisos: list[str]
    items_total: int
    items_com_composicao: int
    items_vazios: int

    model_config = ConfigDict(from_attributes=True)


class RelatorioComposicaoResponse(BaseModel):
    """Response para relatório de composição."""
    proposta: dict
    items_detalhados: list[dict]
    totais_proposta: dict

    model_config = ConfigDict(from_attributes=True)

