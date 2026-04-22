"""Pydantic schemas for PC Tabelas (Planilha de Custos)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PcCabecalhoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome_arquivo: str
    data_referencia: date | None
    versao_layout: str | None
    observacao: str | None
    criado_em: datetime


class PcMaoObraItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    descricao_funcao: str
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


class PcEquipamentoPremissaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    horas_mes: Decimal | None
    preco_gasolina_l: Decimal | None
    preco_diesel_l: Decimal | None


class PcEquipamentoItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    codigo: str | None
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


class PcEncargoItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo_encargo: str
    grupo: str | None
    codigo_grupo: str | None
    discriminacao_encargo: str
    taxa_percent: Decimal | None


class PcEpiItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    epi: str
    unidade: str | None
    custo_unitario: Decimal | None
    quantidade: Decimal | None
    vida_util_meses: Decimal | None
    custo_epi_mes: Decimal | None


class PcFerramentaItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item: str | None
    descricao: str
    unidade: str | None
    quantidade: Decimal | None
    preco: Decimal | None
    preco_total: Decimal | None


class PcMobilizacaoQuantidadeFuncaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coluna_funcao: str
    quantidade: Decimal | None


class PcMobilizacaoItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    descricao: str
    funcao: str | None
    tipo_mao_obra: str | None
    quantidades_funcao: list[PcMobilizacaoQuantidadeFuncaoOut] = []


class PcEquipamentosOut(BaseModel):
    premissa: PcEquipamentoPremissaOut | None
    items: list[PcEquipamentoItemOut]
