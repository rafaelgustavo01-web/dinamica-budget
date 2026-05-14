from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BcuCabecalhoOut(BaseModel):
    id: UUID
    nome_arquivo: str
    data_referencia: datetime | None
    versao_layout: str | None
    observacao: str | None
    is_ativo: bool
    criado_por_id: UUID | None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class BcuMaoObraItemOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    descricao_funcao: str
    codigo_origem: str | None
    salario: Decimal | None
    previsao_reajuste: Decimal | None
    encargos_percent: Decimal | None
    periculosidade_insalubridade: Decimal | None
    refeicao: Decimal | None
    agua_potavel: Decimal | None
    vale_alimentacao: Decimal | None
    plano_saude: Decimal | None
    ferramentas_val: Decimal | None
    seguro_vida: Decimal | None
    abono_ferias: Decimal | None
    uniforme_val: Decimal | None
    epi_val: Decimal | None
    custo_unitario_h: Decimal | None
    custo_mensal: Decimal | None
    mobilizacao: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuEquipamentoPremissaOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    horas_mes: Decimal | None
    preco_gasolina_l: Decimal | None
    preco_diesel_l: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuEquipamentoItemOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    codigo: str | None
    codigo_origem: str | None
    equipamento: str
    combustivel_utilizado: str | None
    consumo_l_h: Decimal | None
    aluguel_r_h: Decimal | None
    combustivel_r_h: Decimal | None
    mao_obra_r_h: Decimal | None
    hora_produtiva: Decimal | None
    hora_improdutiva: Decimal | None
    mes: Decimal | None
    aluguel_mensal: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuEquipamentosOut(BaseModel):
    premissa: BcuEquipamentoPremissaOut | None
    items: list[BcuEquipamentoItemOut]


class BcuEncargoItemOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    tipo_encargo: str
    grupo: str | None
    codigo_grupo: str | None
    discriminacao_encargo: str
    taxa_percent: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuEpiItemOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    codigo_origem: str | None
    epi: str
    unidade: str | None
    custo_unitario: Decimal | None
    vida_util_meses: Decimal | None
    custo_epi_mes: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuFerramentaItemOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    codigo_origem: str | None
    item: str | None
    descricao: str
    unidade: str | None
    preco: Decimal | None
    preco_total: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuMobilizacaoQuantidadeFuncaoOut(BaseModel):
    coluna_funcao: str
    quantidade: Decimal | None

    model_config = ConfigDict(from_attributes=True)


class BcuMobilizacaoItemOut(BaseModel):
    id: UUID
    cabecalho_id: UUID
    descricao: str
    funcao: str | None
    tipo_mao_obra: str | None
    quantidades_funcao: list[BcuMobilizacaoQuantidadeFuncaoOut]

    model_config = ConfigDict(from_attributes=True)


# ── CRUD schemas ───────────────────────────────────────────────────────

class BcuMaoObraItemCreate(BaseModel):
    descricao_funcao: str = Field(..., min_length=1, max_length=255)
    codigo_origem: str | None = Field(None, max_length=40)
    salario: Decimal | None = None
    previsao_reajuste: Decimal | None = None
    encargos_percent: Decimal | None = None
    periculosidade_insalubridade: Decimal | None = None
    refeicao: Decimal | None = None
    agua_potavel: Decimal | None = None
    vale_alimentacao: Decimal | None = None
    plano_saude: Decimal | None = None
    ferramentas_val: Decimal | None = None
    seguro_vida: Decimal | None = None
    abono_ferias: Decimal | None = None
    uniforme_val: Decimal | None = None
    epi_val: Decimal | None = None
    custo_unitario_h: Decimal | None = None
    custo_mensal: Decimal | None = None
    mobilizacao: Decimal | None = None


class BcuMaoObraItemUpdate(BaseModel):
    descricao_funcao: str | None = Field(None, min_length=1, max_length=255)
    codigo_origem: str | None = Field(None, max_length=40)
    salario: Decimal | None = None
    previsao_reajuste: Decimal | None = None
    encargos_percent: Decimal | None = None
    periculosidade_insalubridade: Decimal | None = None
    refeicao: Decimal | None = None
    agua_potavel: Decimal | None = None
    vale_alimentacao: Decimal | None = None
    plano_saude: Decimal | None = None
    ferramentas_val: Decimal | None = None
    seguro_vida: Decimal | None = None
    abono_ferias: Decimal | None = None
    uniforme_val: Decimal | None = None
    epi_val: Decimal | None = None
    custo_unitario_h: Decimal | None = None
    custo_mensal: Decimal | None = None
    mobilizacao: Decimal | None = None


class BcuEquipamentoItemCreate(BaseModel):
    codigo: str | None = Field(None, max_length=80)
    codigo_origem: str | None = Field(None, max_length=40)
    equipamento: str = Field(..., min_length=1, max_length=255)
    combustivel_utilizado: str | None = Field(None, max_length=60)
    consumo_l_h: Decimal | None = None
    aluguel_r_h: Decimal | None = None
    combustivel_r_h: Decimal | None = None
    mao_obra_r_h: Decimal | None = None
    hora_produtiva: Decimal | None = None
    hora_improdutiva: Decimal | None = None
    mes: Decimal | None = None
    aluguel_mensal: Decimal | None = None


class BcuEquipamentoItemUpdate(BaseModel):
    codigo: str | None = Field(None, max_length=80)
    codigo_origem: str | None = Field(None, max_length=40)
    equipamento: str | None = Field(None, min_length=1, max_length=255)
    combustivel_utilizado: str | None = Field(None, max_length=60)
    consumo_l_h: Decimal | None = None
    aluguel_r_h: Decimal | None = None
    combustivel_r_h: Decimal | None = None
    mao_obra_r_h: Decimal | None = None
    hora_produtiva: Decimal | None = None
    hora_improdutiva: Decimal | None = None
    mes: Decimal | None = None
    aluguel_mensal: Decimal | None = None


class BcuEncargoItemCreate(BaseModel):
    tipo_encargo: str = Field(..., min_length=1, max_length=20)
    grupo: str | None = Field(None, max_length=80)
    codigo_grupo: str | None = Field(None, max_length=255)
    discriminacao_encargo: str = Field(..., min_length=1, max_length=255)
    taxa_percent: Decimal | None = None


class BcuEncargoItemUpdate(BaseModel):
    tipo_encargo: str | None = Field(None, min_length=1, max_length=20)
    grupo: str | None = Field(None, max_length=80)
    codigo_grupo: str | None = Field(None, max_length=255)
    discriminacao_encargo: str | None = Field(None, min_length=1, max_length=255)
    taxa_percent: Decimal | None = None


class BcuEpiItemCreate(BaseModel):
    codigo_origem: str | None = Field(None, max_length=40)
    epi: str = Field(..., min_length=1, max_length=255)
    unidade: str | None = Field(None, max_length=30)
    custo_unitario: Decimal | None = None
    vida_util_meses: Decimal | None = None
    custo_epi_mes: Decimal | None = None


class BcuEpiItemUpdate(BaseModel):
    codigo_origem: str | None = Field(None, max_length=40)
    epi: str | None = Field(None, min_length=1, max_length=255)
    unidade: str | None = Field(None, max_length=30)
    custo_unitario: Decimal | None = None
    vida_util_meses: Decimal | None = None
    custo_epi_mes: Decimal | None = None


class BcuFerramentaItemCreate(BaseModel):
    codigo_origem: str | None = Field(None, max_length=40)
    item: str | None = Field(None, max_length=40)
    descricao: str = Field(..., min_length=1, max_length=255)
    unidade: str | None = Field(None, max_length=30)
    preco: Decimal | None = None
    preco_total: Decimal | None = None


class BcuFerramentaItemUpdate(BaseModel):
    codigo_origem: str | None = Field(None, max_length=40)
    item: str | None = Field(None, max_length=40)
    descricao: str | None = Field(None, min_length=1, max_length=255)
    unidade: str | None = Field(None, max_length=30)
    preco: Decimal | None = None
    preco_total: Decimal | None = None


class BcuMobilizacaoItemCreate(BaseModel):
    descricao: str = Field(..., min_length=1, max_length=255)
    funcao: str | None = Field(None, max_length=120)
    tipo_mao_obra: str | None = Field(None, max_length=20)


class BcuMobilizacaoItemUpdate(BaseModel):
    descricao: str | None = Field(None, min_length=1, max_length=255)
    funcao: str | None = Field(None, max_length=120)
    tipo_mao_obra: str | None = Field(None, max_length=20)


# ── Upload individual schemas ──────────────────────────────────────────

class BcuUploadPreviewRow(BaseModel):
    row_number: int
    data: dict
    errors: list[str] | None = None


class BcuUploadPreviewOut(BaseModel):
    tipo: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[BcuUploadPreviewRow]


class BcuUploadConfirmOut(BaseModel):
    tipo: str
    cabecalho_id: UUID
    imported_rows: int
    warnings: list[str] | None = None


# ── De/Para schemas ────────────────────────────────────────────────────

class DeParaCreate(BaseModel):
    base_tcpo_id: UUID
    bcu_table_type: str
    bcu_item_id: UUID


class DeParaOut(BaseModel):
    id: UUID
    base_tcpo_id: UUID
    bcu_table_type: str
    bcu_item_id: UUID
    criado_por_id: UUID | None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class DeParaListItemOut(BaseModel):
    id: UUID | None
    base_tcpo_id: UUID
    base_tcpo_codigo: str
    base_tcpo_descricao: str
    base_tcpo_tipo_recurso: str
    bcu_table_type: str | None
    bcu_item_id: UUID | None
    bcu_item_descricao: str | None

    model_config = ConfigDict(from_attributes=True)
