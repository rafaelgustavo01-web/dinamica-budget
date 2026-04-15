import uuid
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Cliente(Base, TimestampMixin):
    __tablename__ = "clientes"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome_fantasia: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    associacoes: Mapped[list["AssociacaoInteligente"]] = relationship(
        "AssociacaoInteligente", foreign_keys="AssociacaoInteligente.cliente_id",
        lazy="noload"
    )
    historicos: Mapped[list["HistoricoBuscaCliente"]] = relationship(
        back_populates="cliente", lazy="noload"
    )
