"""SQLAlchemy ORM models for per-proposal extra resources."""

import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class PropostaRecursoExtra(Base):
    __tablename__ = "proposta_recurso_extra"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_recurso: Mapped[str] = mapped_column(String(20), nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade_medida: Mapped[str | None] = mapped_column(String(30), nullable=True)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_por_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.usuarios.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    alocacoes: Mapped[list["PropostaRecursoAlocacao"]] = relationship(
        back_populates="recurso_extra", lazy="noload", cascade="all, delete-orphan"
    )


class PropostaRecursoAlocacao(Base):
    __tablename__ = "proposta_recurso_alocacao"
    __table_args__ = (
        UniqueConstraint("recurso_extra_id", "composicao_id", name="uq_recurso_alocacao"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recurso_extra_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.proposta_recurso_extra.id", ondelete="CASCADE"), nullable=False, index=True)
    composicao_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.proposta_item_composicoes.id", ondelete="CASCADE"), nullable=False, index=True)
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(15, 6), nullable=False, default=Decimal("1"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    recurso_extra: Mapped[PropostaRecursoExtra] = relationship(back_populates="alocacoes", lazy="noload")
    composicao: Mapped["PropostaItemComposicao"] = relationship(back_populates="recursos_extras", lazy="noload")
