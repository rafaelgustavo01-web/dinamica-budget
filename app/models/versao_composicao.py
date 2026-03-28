import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OrigemItem


class VersaoComposicao(Base):
    """
    Versão de composição de um ServicoTcpo.

    Cada ServicoTcpo do tipo SERVICO pode ter múltiplas versões de composição:
      - Versão 1 (origem=TCPO, cliente_id=None): composição padrão do catálogo
      - Versão N (origem=PROPRIA, cliente_id=<uuid>): composição customizada do cliente

    Para explosão de custo, usa-se a versão PROPRIA ativa do cliente se existir,
    caso contrário a versão TCPO ativa global.
    """

    __tablename__ = "versao_composicao"
    __table_args__ = (
        UniqueConstraint("servico_id", "numero_versao", name="uq_versao_composicao_servico_numero"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    servico_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id"),
        nullable=False,
        index=True,
    )
    numero_versao: Mapped[int] = mapped_column(Integer, nullable=False)
    origem: Mapped[OrigemItem] = mapped_column(
        SAEnum(OrigemItem, name="origem_item_enum", create_type=False),
        nullable=False,
    )
    # NULL → versão global TCPO; preenchido → versão própria do cliente
    cliente_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clientes.id"),
        nullable=True,
        index=True,
    )
    is_ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ── Relationships ────────────────────────────────────────────────────────
    servico: Mapped["ServicoTcpo"] = relationship(
        "ServicoTcpo", foreign_keys=[servico_id], lazy="noload"
    )
    cliente: Mapped["Cliente | None"] = relationship(
        "Cliente", foreign_keys=[cliente_id], lazy="noload"
    )
    criado_por: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[criado_por_id], lazy="noload"
    )
    itens: Mapped[list["ComposicaoTcpo"]] = relationship(
        back_populates="versao",
        foreign_keys="ComposicaoTcpo.versao_id",
        lazy="noload",
    )
