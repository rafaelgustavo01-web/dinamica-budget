"""SQLAlchemy ORM models for BCU (Base de Custos Unitarios) schema."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class BcuTableType(str, enum.Enum):
    MO = "MO"
    EQP = "EQP"
    EPI = "EPI"
    FER = "FER"
    MOB = "MOB"


class BcuCabecalho(Base):
    __tablename__ = "cabecalho"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    data_referencia: Mapped[date | None] = mapped_column(Date(), nullable=True)
    versao_layout: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_ativo: Mapped[bool] = mapped_column(nullable=False, server_default="FALSE")
    criado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operacional.usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    mao_obra_items: Mapped[list["BcuMaoObraItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    equipamento_premissas: Mapped[list["BcuEquipamentoPremissa"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    equipamento_items: Mapped[list["BcuEquipamentoItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    encargo_items: Mapped[list["BcuEncargoItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    epi_items: Mapped[list["BcuEpiItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    ferramenta_items: Mapped[list["BcuFerramentaItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")
    mobilizacao_items: Mapped[list["BcuMobilizacaoItem"]] = relationship(back_populates="cabecalho", lazy="noload", cascade="all, delete-orphan")


class BcuMaoObraItem(Base):
    __tablename__ = "mao_obra_item"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao_funcao: Mapped[str] = mapped_column(String(255), nullable=False)
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    previsao_reajuste: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    encargos_percent: Mapped[Decimal | None] = mapped_column(Numeric(15, 6), nullable=True)
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
    custo_unitario_h: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_mensal: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    mobilizacao: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="mao_obra_items", lazy="noload")


class BcuEquipamentoPremissa(Base):
    __tablename__ = "equipamento_premissa"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    horas_mes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    preco_gasolina_l: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    preco_diesel_l: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="equipamento_premissas", lazy="noload")


class BcuEquipamentoItem(Base):
    __tablename__ = "equipamento_item"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
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

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="equipamento_items", lazy="noload")


class BcuEncargoItem(Base):
    __tablename__ = "encargo_item"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo_encargo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    grupo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    codigo_grupo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discriminacao_encargo: Mapped[str] = mapped_column(String(255), nullable=False)
    taxa_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="encargo_items", lazy="noload")


class BcuEpiItem(Base):
    __tablename__ = "epi_item"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    epi: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    custo_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    vida_util_meses: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    custo_epi_mes: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="epi_items", lazy="noload")
    distribuicoes: Mapped[list["BcuEpiDistribuicaoFuncao"]] = relationship(back_populates="epi_item", lazy="noload", cascade="all, delete-orphan")


class BcuEpiDistribuicaoFuncao(Base):
    __tablename__ = "epi_distribuicao_funcao"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    epi_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.epi_item.id", ondelete="CASCADE"), nullable=False, index=True
    )
    funcao: Mapped[str] = mapped_column(String(80), nullable=False)
    aplica_flag: Mapped[str | None] = mapped_column(String(20), nullable=True)

    epi_item: Mapped[BcuEpiItem] = relationship(back_populates="distribuicoes", lazy="noload")


class BcuFerramentaItem(Base):
    __tablename__ = "ferramenta_item"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    item: Mapped[str | None] = mapped_column(String(40), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="ferramenta_items", lazy="noload")


class BcuMobilizacaoItem(Base):
    __tablename__ = "mobilizacao_item"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cabecalho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.cabecalho.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    funcao: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tipo_mao_obra: Mapped[str | None] = mapped_column(String(20), nullable=True)

    cabecalho: Mapped[BcuCabecalho] = relationship(back_populates="mobilizacao_items", lazy="noload")
    quantidades_funcao: Mapped[list["BcuMobilizacaoQuantidadeFuncao"]] = relationship(back_populates="mobilizacao_item", lazy="noload", cascade="all, delete-orphan")


class BcuMobilizacaoQuantidadeFuncao(Base):
    __tablename__ = "mobilizacao_quantidade_funcao"
    __table_args__ = {"schema": "bcu"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mobilizacao_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("bcu.mobilizacao_item.id", ondelete="CASCADE"), nullable=False, index=True
    )
    coluna_funcao: Mapped[str] = mapped_column(String(50), nullable=False)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    mobilizacao_item: Mapped[BcuMobilizacaoItem] = relationship(back_populates="quantidades_funcao", lazy="noload")


class DeParaTcpoBcu(Base):
    __tablename__ = "de_para"
    __table_args__ = (
        UniqueConstraint("base_tcpo_id", name="uq_de_para_base_tcpo"),
        {"schema": "bcu"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    base_tcpo_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id", ondelete="CASCADE"),
        nullable=False,
    )
    bcu_table_type: Mapped[BcuTableType] = mapped_column(
        PGEnum(BcuTableType, name="bcu_table_type_enum", create_type=False),
        nullable=False,
    )
    bcu_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    criado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operacional.usuarios.id"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
