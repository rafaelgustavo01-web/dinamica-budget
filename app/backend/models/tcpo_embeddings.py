from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class TcpoEmbedding(Base):
    __tablename__ = "tcpo_embeddings"
    __table_args__ = {"schema": "referencia"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vetor: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    # 'metadata' is reserved by SQLAlchemy Declarative API — use embedding_metadata
    embedding_metadata: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, name="metadata"  # DB column keeps the name 'metadata'
    )

    base_tcpo: Mapped["BaseTcpo"] = relationship(
        back_populates="embedding", lazy="noload"
    )

