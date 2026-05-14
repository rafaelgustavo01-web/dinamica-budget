from __future__ import annotations

import uuid
import enum
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class ImportCorrectionType(str, enum.Enum):
    COLUMN_REMAP = "COLUMN_REMAP"
    HEADER_ROW_FIX = "HEADER_ROW_FIX"
    ROW_RECLASSIFY = "ROW_RECLASSIFY"
    SHEET_CHANGE = "SHEET_CHANGE"


class ImportProfile(Base, TimestampMixin):
    __tablename__ = "import_profile"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aba_pattern: Mapped[str | None] = mapped_column(String(200), nullable=True)
    header_row_strategy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=lambda: {"mode": "scan"})
    column_aliases: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    score_confianca: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0"))
    uso_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_aprovado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    corrections: Mapped[list["ImportProfileCorrection"]] = relationship(
        back_populates="profile",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="ImportProfileCorrection.created_at.desc()",
    )


class ImportProfileCorrection(Base):
    __tablename__ = "import_profile_correction"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.import_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.smart_import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[ImportCorrectionType] = mapped_column(
        SAEnum(ImportCorrectionType, name="import_correction_type_enum", create_type=False),
        nullable=False,
    )
    detalhe: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    aplicada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[sa.DateTime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    profile: Mapped["ImportProfile"] = relationship(back_populates="corrections", lazy="noload")
