import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import OrigemItem, StatusHomologacao


class ServicoTcpo(Base, TimestampMixin):
    """
    Catálogo central de serviços/insumos.
    Unifica itens TCPO (origem=TCPO) e itens próprios do cliente (origem=PROPRIA).
    Itens PROPRIA exigem homologação antes de aparecerem na busca.
    """

    __tablename__ = "servico_tcpo"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Isolamento por cliente — NULL para itens TCPO globais
    cliente_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clientes.id"),
        nullable=True,
        index=True,
    )

    codigo_origem: Mapped[str] = mapped_column(nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(nullable=False)
    custo_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    categoria_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categoria_recurso.id"), nullable=True, index=True
    )

    # ── Governança ──────────────────────────────────────────────────────────
    origem: Mapped[OrigemItem] = mapped_column(
        SAEnum(OrigemItem, name="origem_item_enum", create_type=False),
        nullable=False,
        default=OrigemItem.TCPO,
    )
    status_homologacao: Mapped[StatusHomologacao] = mapped_column(
        SAEnum(StatusHomologacao, name="status_homologacao_enum", create_type=False),
        nullable=False,
        default=StatusHomologacao.PENDENTE,  # Defense-in-depth: default safe state
    )
    aprovado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuarios.id"),
        nullable=True,
    )
    data_aprovacao: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Soft delete ─────────────────────────────────────────────────────────
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # ── Relationships ────────────────────────────────────────────────────────
    categoria: Mapped["CategoriaRecurso | None"] = relationship(
        back_populates="servicos", lazy="noload"
    )
    cliente: Mapped["Cliente | None"] = relationship(
        "Cliente", foreign_keys=[cliente_id], lazy="noload"
    )
    aprovado_por: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[aprovado_por_id], back_populates="itens_aprovados", lazy="noload"
    )
    composicoes_pai: Mapped[list["ComposicaoTcpo"]] = relationship(
        back_populates="servico_pai",
        foreign_keys="ComposicaoTcpo.servico_pai_id",
        lazy="noload",
    )
    composicoes_filho: Mapped[list["ComposicaoTcpo"]] = relationship(
        back_populates="insumo_filho",
        foreign_keys="ComposicaoTcpo.insumo_filho_id",
        lazy="noload",
    )
    embedding: Mapped["TcpoEmbedding | None"] = relationship(
        back_populates="servico", lazy="noload", uselist=False
    )
    associacoes: Mapped[list["AssociacaoInteligente"]] = relationship(
        back_populates="servico_tcpo", lazy="noload"
    )
