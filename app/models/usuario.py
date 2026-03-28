import uuid
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class UsuarioPerfil(Base):
    """Associative table: Usuario ↔ PerfilUsuario (RBAC).
    Table renamed to permissao_operacional in Migration 010.
    """

    __tablename__ = "permissao_operacional"

    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"), primary_key=True
    )
    perfil: Mapped[str] = mapped_column(String(50), primary_key=True)  # PerfilUsuario enum value


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # AD/LDAP integration: stores the objectGUID or sAMAccountName from Active Directory
    external_id_ad: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # is_admin kept for superuser override; fine-grained access via usuario_perfil
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    historicos: Mapped[list["HistoricoBuscaCliente"]] = relationship(
        back_populates="usuario", lazy="noload"
    )
    perfis: Mapped[list["UsuarioPerfil"]] = relationship(
        "UsuarioPerfil",
        foreign_keys="UsuarioPerfil.usuario_id",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    itens_aprovados: Mapped[list["ServicoTcpo"]] = relationship(
        "ServicoTcpo",
        foreign_keys="ServicoTcpo.aprovado_por_id",
        back_populates="aprovado_por",
        lazy="noload",
    )
