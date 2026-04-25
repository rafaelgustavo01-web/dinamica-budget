"""
BOM customizado do cliente. Schema: operacional.
Cada componente pode ser da base TCPO OU item próprio (XOR via CHECK).
"""

import uuid
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class ComposicaoCliente(Base):
    __tablename__ = "composicao_cliente"
    __table_args__ = (
        CheckConstraint(
            "(insumo_base_id IS NOT NULL AND insumo_proprio_id IS NULL) OR "
            "(insumo_base_id IS NULL AND insumo_proprio_id IS NOT NULL)",
            name="ck_composicao_cliente_exclusivo",
        ),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    versao_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.versao_composicao.id"),
        nullable=False,
        index=True,
    )
    insumo_base_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id"),
        nullable=True,
        index=True,
    )
    insumo_proprio_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.itens_proprios.id"),
        nullable=True,
        index=True,
    )
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Relationships ────────────────────────────────────────────────────────
    versao: Mapped["VersaoComposicao"] = relationship(
        back_populates="itens", foreign_keys=[versao_id], lazy="noload"
    )
    insumo_base: Mapped["BaseTcpo | None"] = relationship(
        foreign_keys=[insumo_base_id], lazy="noload"
    )
    insumo_proprio: Mapped["ItemProprio | None"] = relationship(
        foreign_keys=[insumo_proprio_id], lazy="noload"
    )

