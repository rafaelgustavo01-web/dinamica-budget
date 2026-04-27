"""SQLAlchemy ORM models for per-proposal cost snapshot (Histograma)."""

import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class PropostaPcMaoObra(Base):
    __tablename__ = "proposta_pc_mao_obra"
    __table_args__ = (
        UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_mao_obra"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    descricao_funcao: Mapped[str] = mapped_column(String(255), nullable=False)
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True)
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
    valor_bcu_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PropostaPcEquipamentoPremissa(Base):
    __tablename__ = "proposta_pc_equipamento_premissa"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    horas_mes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    preco_gasolina_l: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    preco_diesel_l: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PropostaPcEquipamento(Base):
    __tablename__ = "proposta_pc_equipamento"
    __table_args__ = (
        UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_equipamento"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    codigo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True)
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
    valor_bcu_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PropostaPcEncargo(Base):
    __tablename__ = "proposta_pc_encargo"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    tipo_encargo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    grupo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    codigo_grupo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discriminacao_encargo: Mapped[str] = mapped_column(String(255), nullable=False)
    taxa_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    valor_bcu_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PropostaPcEpi(Base):
    __tablename__ = "proposta_pc_epi"
    __table_args__ = (
        UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_epi"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True)
    epi: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    custo_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    vida_util_meses: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    custo_epi_mes: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    valor_bcu_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PropostaPcFerramenta(Base):
    __tablename__ = "proposta_pc_ferramenta"
    __table_args__ = (
        UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_ferramenta"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    codigo_origem: Mapped[str | None] = mapped_column(String(40), nullable=True)
    item: Mapped[str | None] = mapped_column(String(40), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    valor_bcu_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PropostaPcMobilizacao(Base):
    __tablename__ = "proposta_pc_mobilizacao"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    bcu_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    funcao: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tipo_mao_obra: Mapped[str | None] = mapped_column(String(20), nullable=True)
    editado_manualmente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    quantidades_funcao: Mapped[list["PropostaPcMobilizacaoQuantidade"]] = relationship(
        back_populates="mobilizacao", lazy="noload", cascade="all, delete-orphan"
    )


class PropostaPcMobilizacaoQuantidade(Base):
    __tablename__ = "proposta_pc_mobilizacao_quantidade"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mobilizacao_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.proposta_pc_mobilizacao.id", ondelete="CASCADE"), nullable=False, index=True)
    coluna_funcao: Mapped[str] = mapped_column(String(50), nullable=False)
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    mobilizacao: Mapped[PropostaPcMobilizacao] = relationship(back_populates="quantidades_funcao", lazy="noload")
