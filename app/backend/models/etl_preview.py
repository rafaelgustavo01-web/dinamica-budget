"""DB-backed ETL parse-token store — replaces volatile in-memory dict in EtlService."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class EtlPreview(Base):
    __tablename__ = "etl_preview"
    __table_args__ = {"schema": "operacional"}

    token: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    # Serialised _EtlParseResult — {itens: [...], relacoes: [...], avisos: [...]}
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
