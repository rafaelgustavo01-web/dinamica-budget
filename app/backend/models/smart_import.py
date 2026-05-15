import uuid
import enum
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class SmartImportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSANDO"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SmartImportJob(Base, TimestampMixin):
    __tablename__ = "smart_import_jobs"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proposta_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.import_profile.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    arquivo_origem: Mapped[str] = mapped_column(String(260), nullable=False)
    status: Mapped[SmartImportStatus] = mapped_column(
        SAEnum(SmartImportStatus, name="smart_import_status_enum", create_type=False),
        nullable=False,
        default=SmartImportStatus.PENDING,
    )
    mapping_metadata: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    payload_staging: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    payload_raw: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    detected_header_row: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detected_data_range: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    row_classifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
