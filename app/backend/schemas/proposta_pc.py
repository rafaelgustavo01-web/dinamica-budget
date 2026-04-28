from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PropostaPcMaoObraOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
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
    valor_bcu_snapshot: Decimal | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class PropostaPcEquipamentoPremissaOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
    horas_mes: Decimal | None
    preco_gasolina_l: Decimal | None
    preco_diesel_l: Decimal | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class PropostaPcEquipamentoOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
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
    valor_bcu_snapshot: Decimal | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class PropostaPcEncargoOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
    tipo_encargo: str
    grupo: str | None
    codigo_grupo: str | None
    discriminacao_encargo: str
    taxa_percent: Decimal | None
    valor_bcu_snapshot: Decimal | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class PropostaPcEpiOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
    codigo_origem: str | None
    epi: str
    unidade: str | None
    custo_unitario: Decimal | None
    quantidade: Decimal | None
    vida_util_meses: Decimal | None
    custo_epi_mes: Decimal | None
    valor_bcu_snapshot: Decimal | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class PropostaPcFerramentaOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
    codigo_origem: str | None
    item: str | None
    descricao: str
    unidade: str | None
    quantidade: Decimal | None
    preco: Decimal | None
    preco_total: Decimal | None
    valor_bcu_snapshot: Decimal | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class PropostaPcMobilizacaoOut(BaseModel):
    id: UUID
    proposta_id: UUID
    bcu_item_id: UUID | None
    descricao: str
    funcao: str | None
    tipo_mao_obra: str | None
    editado_manualmente: bool
    model_config = ConfigDict(from_attributes=True)


class DivergenciaOut(BaseModel):
    tabela: Literal["mao-obra", "equipamento", "epi", "ferramenta", "encargo"]
    item_id: UUID
    campo: str
    valor_snapshot: Decimal | None
    valor_atual_bcu: Decimal | None
    valor_proposta: Decimal | None


class RecursoExtraOut(BaseModel):
    id: UUID
    proposta_id: UUID
    tipo_recurso: str
    descricao: str
    unidade_medida: str | None
    custo_unitario: Decimal
    observacao: str | None
    alocacoes_count: int


class HistogramaCompletoResponse(BaseModel):
    proposta_id: UUID
    bcu_cabecalho_id: UUID | str | None
    mao_obra: list[PropostaPcMaoObraOut]
    equipamento_premissa: PropostaPcEquipamentoPremissaOut | None
    equipamentos: list[PropostaPcEquipamentoOut]
    encargos_horista: list[PropostaPcEncargoOut]
    encargos_mensalista: list[PropostaPcEncargoOut]
    epis: list[PropostaPcEpiOut]
    ferramentas: list[PropostaPcFerramentaOut]
    mobilizacao: list[PropostaPcMobilizacaoOut]
    recursos_extras: list[RecursoExtraOut]
    divergencias: list[DivergenciaOut]
    cpu_desatualizada: bool


class MontarHistogramaResponse(BaseModel):
    mao_obra: int
    equipamento_premissa: int
    equipamentos: int
    encargos: int
    epis: int
    ferramentas: int
    mobilizacao: int


class RecursoExtraCreate(BaseModel):
    tipo_recurso: str
    descricao: str
    unidade_medida: str | None = None
    custo_unitario: Decimal
    observacao: str | None = None


class RecursoExtraUpdate(BaseModel):
    descricao: str | None = None
    unidade_medida: str | None = None
    custo_unitario: Decimal | None = None
    observacao: str | None = None


class AlocarRecursoRequest(BaseModel):
    recurso_extra_id: UUID
    quantidade_consumo: Decimal = Decimal("1")


class AlocacaoOut(BaseModel):
    id: UUID
    recurso_extra_id: UUID
    composicao_id: UUID
    quantidade_consumo: Decimal
    model_config = ConfigDict(from_attributes=True)
