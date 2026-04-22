"""
Renamed from associacao_tcpo → associacao_inteligente (V2).

Key changes from V1:
  - frequencia_uso: INT tracks how many times this association was confirmed
  - status_validacao: ENUM controls auto-return threshold in Phase 1
  - Strengthening rule: after CONSOLIDACAO_THRESHOLD confirmations, status → CONSOLIDADA
    which triggers immediate circuit-break in busca_service

V3 (dual-schema): FK agora aponta para referencia.base_tcpo (item_referencia_id).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OrigemAssociacao, StatusValidacaoAssociacao

# After this many confirmations, association becomes CONSOLIDADA (auto-return)
CONSOLIDACAO_THRESHOLD = 3


class AssociacaoInteligente(Base):
    __tablename__ = "associacao_inteligente"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id"),
        nullable=False,
        index=True,
    )
    texto_busca_normalizado: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    item_referencia_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id"),
        nullable=False,
        index=True,
    )
    origem_associacao: Mapped[OrigemAssociacao] = mapped_column(
        SAEnum(OrigemAssociacao, name="origem_associacao_enum", create_type=False),
        nullable=False,
    )
    confiabilidade_score: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )

    # ── Fortalecimento ───────────────────────────────────────────────────────
    frequencia_uso: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    status_validacao: Mapped[StatusValidacaoAssociacao] = mapped_column(
        SAEnum(StatusValidacaoAssociacao, name="status_validacao_associacao_enum", create_type=False),
        nullable=False,
        default=StatusValidacaoAssociacao.SUGERIDA,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    cliente: Mapped["Cliente"] = relationship(lazy="noload")
    item_referencia: Mapped["BaseTcpo"] = relationship(
        back_populates="associacoes", lazy="noload"
    )

    def fortalecer(self) -> None:
        """Increment usage and elevate status based on threshold."""
        self.frequencia_uso += 1
        if self.frequencia_uso >= CONSOLIDACAO_THRESHOLD:
            self.status_validacao = StatusValidacaoAssociacao.CONSOLIDADA
        elif self.frequencia_uso >= 1 and self.status_validacao == StatusValidacaoAssociacao.SUGERIDA:
            self.status_validacao = StatusValidacaoAssociacao.VALIDADA
