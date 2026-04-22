"""
BOM (Bill of Materials) TCPO — hierarquia pai→filho do Excel.
Schema: referencia. Imutável. Sem versionamento.
"""

import uuid
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ComposicaoBase(Base):
    __tablename__ = "composicao_base"
    __table_args__ = {"schema": "referencia"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    servico_pai_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id"),
        nullable=False,
        index=True,
    )
    insumo_filho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id"),
        nullable=False,
        index=True,
    )
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Relationships ────────────────────────────────────────────────────────
    servico_pai: Mapped["BaseTcpo"] = relationship(
        back_populates="composicoes_pai",
        foreign_keys=[servico_pai_id],
        lazy="noload",
    )
    insumo_filho: Mapped["BaseTcpo"] = relationship(
        back_populates="composicoes_filho",
        foreign_keys=[insumo_filho_id],
        lazy="noload",
    )
