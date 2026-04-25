"""
Versão de composição de um ItemProprio (operacional).

Cada item próprio pode ter múltiplas versões de composição.
Apenas itens do cliente são versionados — base TCPO é imutável (composicao_base).
O cliente_id é derivado do item_proprio.cliente_id (sem redundância).
"""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


class VersaoComposicao(Base):
    __tablename__ = "versao_composicao"
    __table_args__ = (
        UniqueConstraint("item_proprio_id", "numero_versao", name="uq_versao_composicao_item_numero"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_proprio_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.itens_proprios.id"),
        nullable=False,
        index=True,
    )
    numero_versao: Mapped[int] = mapped_column(Integer, nullable=False)
    is_ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id"),
        nullable=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    item_proprio: Mapped["ItemProprio"] = relationship(
        "ItemProprio", foreign_keys=[item_proprio_id], back_populates="versoes", lazy="noload"
    )
    criado_por: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[criado_por_id], lazy="noload"
    )
    itens: Mapped[list["ComposicaoCliente"]] = relationship(
        back_populates="versao",
        foreign_keys="ComposicaoCliente.versao_id",
        lazy="noload",
    )

