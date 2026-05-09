import uuid
import enum
from sqlalchemy import String, Enum as SAEnum, ForeignKey
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
    """
    Staging table for the Smart Import Architecture.
    Separates the flexible extraction phase from the rigid transactional phase.
    """
    __tablename__ = "smart_import_jobs"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    arquivo_origem: Mapped[str] = mapped_column(String(260), nullable=False)
    status: Mapped[SmartImportStatus] = mapped_column(
        SAEnum(SmartImportStatus, name="smart_import_status_enum", create_type=False),
        nullable=False,
        default=SmartImportStatus.PENDING
    )
    
    # Stores confidence scores and column mappings determined by the AI/Heuristic mapper
    mapping_metadata: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    
    # Stores the raw/normalized data, including validation errors for human review
    payload_staging: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
