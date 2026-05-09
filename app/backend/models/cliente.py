import uuid
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Cliente(Base, TimestampMixin):
    __tablename__ = "clientes"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome_fantasia: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    razao_social: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inscricao_estadual: Mapped[str | None] = mapped_column(String(30), nullable=True)
    inscricao_municipal: Mapped[str | None] = mapped_column(String(30), nullable=True)
    endereco_logradouro: Mapped[str | None] = mapped_column(String(255), nullable=True)
    endereco_numero: Mapped[str | None] = mapped_column(String(30), nullable=True)
    endereco_complemento: Mapped[str | None] = mapped_column(String(120), nullable=True)
    endereco_bairro: Mapped[str | None] = mapped_column(String(120), nullable=True)
    endereco_municipio: Mapped[str | None] = mapped_column(String(120), nullable=True)
    endereco_uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    endereco_cep: Mapped[str | None] = mapped_column(String(8), nullable=True)
    contato_nome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contato_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contato_telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    associacoes: Mapped[list["AssociacaoInteligente"]] = relationship(
        "AssociacaoInteligente", foreign_keys="AssociacaoInteligente.cliente_id",
        lazy="noload", overlaps="cliente"
    )
    historicos: Mapped[list["HistoricoBuscaCliente"]] = relationship(
        back_populates="cliente", lazy="noload"
    )
    itens_proprios: Mapped[list["ItemProprio"]] = relationship(
        "ItemProprio", foreign_keys="ItemProprio.cliente_id",
        lazy="noload", overlaps="cliente"
    )

