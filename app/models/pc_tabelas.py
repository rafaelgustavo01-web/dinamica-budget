"""SQLAlchemy ORM models for PC Tabelas (Planilha de Custos) data."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EtlCarga(Base):
    __tablename__ = "etl_carga"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fonte_arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    tipo_fonte: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="EM_PROCESSAMENTO")
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    linhas_lidas: Mapped[int] = mapped_column(nullable=False, server_default="0")
    linhas_carregadas: Mapped[int] = mapped_column(nullable=False, server_default="0")
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)

    cabecalhos: Mapped[list["PcCabecalho"]] = relationship(back_populates="etl_carga", lazy="noload")


class PcCabecalho(Base):
    __tablename__ = "pc_cabecalho"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    etl_carga_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("etl_carga.id", ondelete="SET NULL"), nullable=True
    )
    nome_arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    data_referencia: Mapped[date | None] = mapped_column(Date(), nullable=True)
    versao_layout: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    etl_carga: Mapped[EtlCarga | None] = relationship(back_populates="cabecalhos", lazy="noload")
    mao_obra_items: Mapped[list["PcMaoObraItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    equipamento_premissas: Mapped[list["PcEquipamentoPremissa"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    equipamento_items: Mapped[list["PcEquipamentoItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    encargo_items: Mapped[list["PcEncargoItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    epi_items: Mapped[list["PcEpiItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    ferramenta_items: Mapped[list["PcFerramentaItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    mobilizacao_items: Mapped[list["PcMobilizacaoItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")


class PcMaoObraItem(Base):
    __tablename__ = "pc_mao_obra_item"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao_funcao: Mapped[str] = mapped_column(String(255), nullable=False)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    previsao_reajuste: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    encargos_percent: Mapped[Decimal | None] = mapped_column(Numeric(15, 6), nullable=True)
    # Benefícios individuais
    periculosidade_insalubridade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    refeicao: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    agua_potavel: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    vale_alimentacao: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    plano_saude: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    ferramentas_val: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    seguro_vida: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    abono_ferias: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    uniforme_val: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    epi_val: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    # Resultados calculados
    custo_unitario_h: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_mensal: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    mobilizacao: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="mao_obra_items", lazy="noload")


class PcEquipamentoPremissa(Base):
    __tablename__ = "pc_equipamento_premissa"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    horas_mes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    preco_gasolina_l: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    preco_diesel_l: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="equipamento_premissas", lazy="noload")


class PcEquipamentoItem(Base):
    __tablename__ = "pc_equipamento_item"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    equipamento: Mapped[str] = mapped_column(String(255), nullable=False)
    combustivel_utilizado: Mapped[str | None] = mapped_column(String(60), nullable=True)
    consumo_l_h: Mapped[Decimal | None] = mapped_column(Numeric(15, 6), nullable=True)
    aluguel_r_h: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    combustivel_r_h: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    mao_obra_r_h: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    hora_produtiva: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    hora_improdutiva: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    mes: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    aluguel_mensal: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="equipamento_items", lazy="noload")


class PcEncargoItem(Base):
    __tablename__ = "pc_encargo_item"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo_encargo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # HORISTA | MENSALISTA
    grupo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    codigo_grupo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discriminacao_encargo: Mapped[str] = mapped_column(String(255), nullable=False)
    taxa_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="encargo_items", lazy="noload")


class PcEpiItem(Base):
    __tablename__ = "pc_epi_item"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    epi: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    custo_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    vida_util_meses: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    custo_epi_mes: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="epi_items", lazy="noload")
    distribuicoes: Mapped[list["PcEpiDistribuicaoFuncao"]] = relationship(back_populates="epi_item", lazy="noload", cascade="all, delete-orphan")


class PcEpiDistribuicaoFuncao(Base):
    __tablename__ = "pc_epi_distribuicao_funcao"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_epi_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_epi_item.id", ondelete="CASCADE"), nullable=False, index=True
    )
    funcao: Mapped[str] = mapped_column(String(80), nullable=False)
    aplica_flag: Mapped[str | None] = mapped_column(String(20), nullable=True)

    epi_item: Mapped[PcEpiItem] = relationship(back_populates="distribuicoes", lazy="noload")


class PcFerramentaItem(Base):
    __tablename__ = "pc_ferramenta_item"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item: Mapped[str | None] = mapped_column(String(40), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="ferramenta_items", lazy="noload")


class PcMobilizacaoItem(Base):
    __tablename__ = "pc_mobilizacao_item"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    funcao: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tipo_mao_obra: Mapped[str | None] = mapped_column(String(20), nullable=True)

    cabecalho: Mapped[PcCabecalho] = relationship(back_populates="mobilizacao_items", lazy="noload")
    quantidades_funcao: Mapped[list["PcMobilizacaoQuantidadeFuncao"]] = relationship(back_populates="mobilizacao_item", lazy="noload", cascade="all, delete-orphan")


class PcMobilizacaoQuantidadeFuncao(Base):
    __tablename__ = "pc_mobilizacao_quantidade_funcao"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pc_mobilizacao_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("pc_mobilizacao_item.id", ondelete="CASCADE"), nullable=False, index=True
    )
    coluna_funcao: Mapped[str] = mapped_column(String(50), nullable=False)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    mobilizacao_item: Mapped[PcMobilizacaoItem] = relationship(back_populates="quantidades_funcao", lazy="noload")
