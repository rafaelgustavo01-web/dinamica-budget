import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.enums import CampoSistemaPQ


class PqLayoutCliente(Base, TimestampMixin):
    __tablename__ = "pq_layout_cliente"
    __table_args__ = (
        UniqueConstraint("cliente_id", name="uq_pq_layout_cliente_cliente_id"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False, default="Layout Padrao")
    aba_nome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linha_inicio: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    # F4-02 — Perfil aprovado + learning loop
    is_aprovado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aprovado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aliases_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_confianca: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    mapeamentos: Mapped[list["PqImportacaoMapeamento"]] = relationship(
        back_populates="layout",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    historico: Mapped[list["PqLayoutHistorico"]] = relationship(
        back_populates="layout",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="PqLayoutHistorico.created_at.desc()",
    )


class PqImportacaoMapeamento(Base):
    __tablename__ = "pq_importacao_mapeamento"
    __table_args__ = (
        UniqueConstraint("layout_id", "campo_sistema", name="uq_pq_mapeamento_layout_campo"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layout_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.pq_layout_cliente.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campo_sistema: Mapped[CampoSistemaPQ] = mapped_column(
        SAEnum(CampoSistemaPQ, name="campo_sistema_pq_enum", create_type=False),
        nullable=False,
    )
    coluna_planilha: Mapped[str] = mapped_column(String(100), nullable=False)

    layout: Mapped["PqLayoutCliente"] = relationship(back_populates="mapeamentos", lazy="noload")


class PqLayoutHistorico(Base):
    __tablename__ = "pq_layout_historico"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layout_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.pq_layout_cliente.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    acao: Mapped[str] = mapped_column(String(20), nullable=False)
    usuario_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    detalhe_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    layout: Mapped["PqLayoutCliente"] = relationship(back_populates="historico", lazy="noload")
