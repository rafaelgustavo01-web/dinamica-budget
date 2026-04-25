"""
Catálogo TCPO completo — dados de referência carregados do Excel.
Schema: referencia (OLAP/Lookup, sem vínculo com cliente).

Sem homologação, sem soft delete, sem cliente_id.
Toda carga nova entra e está disponível imediatamente.
"""

import uuid
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.enums import TipoRecurso


class BaseTcpo(Base, TimestampMixin):
    __tablename__ = "base_tcpo"
    __table_args__ = {"schema": "referencia"}

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    codigo_origem: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    custo_base: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    tipo_recurso: Mapped[TipoRecurso | None] = mapped_column(
        SAEnum(TipoRecurso, name="tipo_recurso_enum", create_type=False),
        nullable=True,
    )
    categoria_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("referencia.categoria_recurso.id"), nullable=True, index=True
    )
    descricao_tokens: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_tecnico: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    categoria: Mapped["CategoriaRecurso | None"] = relationship(
        back_populates="itens_base", lazy="noload"
    )
    composicoes_pai: Mapped[list["ComposicaoBase"]] = relationship(
        back_populates="servico_pai",
        foreign_keys="ComposicaoBase.servico_pai_id",
        lazy="noload",
    )
    composicoes_filho: Mapped[list["ComposicaoBase"]] = relationship(
        back_populates="insumo_filho",
        foreign_keys="ComposicaoBase.insumo_filho_id",
        lazy="noload",
    )
    embedding: Mapped["TcpoEmbedding | None"] = relationship(
        back_populates="base_tcpo", lazy="noload", uselist=False
    )
    associacoes: Mapped[list["AssociacaoInteligente"]] = relationship(
        back_populates="item_referencia", lazy="noload"
    )

