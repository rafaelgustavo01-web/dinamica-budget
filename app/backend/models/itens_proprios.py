"""
Itens criados pelo cliente. Schema: operacional.
Passam por workflow de homologação (PENDENTE → APROVADO → REPROVADO).
Soft delete via deleted_at. Somente APROVADOS aparecem na busca (Fase 0).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.enums import StatusHomologacao, TipoRecurso


class ItemProprio(Base, TimestampMixin):
    __tablename__ = "itens_proprios"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo_origem: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tipo_recurso: Mapped[TipoRecurso | None] = mapped_column(
        SAEnum(TipoRecurso, name="tipo_recurso_enum", create_type=False),
        nullable=True,
    )
    categoria_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("referencia.categoria_recurso.id"), nullable=True, index=True
    )

    # ── Governança ──────────────────────────────────────────────────────────
    status_homologacao: Mapped[StatusHomologacao] = mapped_column(
        SAEnum(StatusHomologacao, name="status_homologacao_enum", create_type=False),
        nullable=False,
        default=StatusHomologacao.PENDENTE,
    )
    aprovado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id"),
        nullable=True,
    )
    data_aprovacao: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Busca ────────────────────────────────────────────────────────────────
    descricao_tokens: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Soft delete ─────────────────────────────────────────────────────────
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # ── Relationships ────────────────────────────────────────────────────────
    categoria: Mapped["CategoriaRecurso | None"] = relationship(
        back_populates="itens_proprios", lazy="noload"
    )
    cliente: Mapped["Cliente"] = relationship(
        "Cliente", foreign_keys=[cliente_id], lazy="noload"
    )
    aprovado_por: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[aprovado_por_id], back_populates="itens_aprovados", lazy="noload"
    )
    versoes: Mapped[list["VersaoComposicao"]] = relationship(
        back_populates="item_proprio", lazy="noload"
    )

