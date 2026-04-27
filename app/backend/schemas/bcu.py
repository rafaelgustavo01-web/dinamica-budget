from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    quantidade: Decimal | None
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
    quantidade: Decimal | None
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
    quantidade: Decimal | None
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
