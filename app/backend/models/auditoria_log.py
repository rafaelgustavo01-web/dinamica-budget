"""
Audit log table — records all write operations on sensitive fields.
Populated explicitly in services (not via SQLAlchemy hooks).

Captures:
  - Price changes on itens_proprios.custo_unitario
  - Status changes on itens_proprios.status_homologacao (approval/rejection)
  - Soft deletes on itens_proprios
  - Creation of item próprio
  - Creation/strengthening of associacao_inteligente
"""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base
from backend.models.enums import TipoOperacaoAuditoria


class AuditoriaLog(Base):
    __tablename__ = "auditoria_log"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tabela: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    registro_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True  # UUID as string for flexibility
    )
    operacao: Mapped[TipoOperacaoAuditoria] = mapped_column(
        SAEnum(TipoOperacaoAuditoria, name="tipo_operacao_auditoria_enum", create_type=False),
        nullable=False,
    )
    campo_alterado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dados_anteriores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dados_novos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    usuario_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operacional.usuarios.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    cliente_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("operacional.clientes.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

