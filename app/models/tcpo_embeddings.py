from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class TcpoEmbedding(Base):
    __tablename__ = "tcpo_embeddings"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vetor: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    # 'metadata' is reserved by SQLAlchemy Declarative API — use embedding_metadata
    embedding_metadata: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, name="metadata"  # DB column keeps the name 'metadata'
    )

    servico: Mapped["ServicoTcpo"] = relationship(
        back_populates="embedding", lazy="noload"
    )
