import uuid
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ComposicaoTcpo(Base):
    __tablename__ = "composicao_tcpo"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Legacy FK — será removido na Migration 012 após validação da 009
    servico_pai_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id"),
        nullable=False,
        index=True,
    )
    insumo_filho_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("servico_tcpo.id"),
        nullable=False,
        index=True,
    )
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # FK para a versão de composição (criado na Migration 009)
    versao_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("versao_composicao.id"),
        nullable=False,
        index=True,
    )
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)

    servico_pai: Mapped["ServicoTcpo"] = relationship(
        back_populates="composicoes_pai",
        foreign_keys=[servico_pai_id],
        lazy="noload",
    )
    insumo_filho: Mapped["ServicoTcpo"] = relationship(
        back_populates="composicoes_filho",
        foreign_keys=[insumo_filho_id],
        lazy="noload",
    )
    versao: Mapped["VersaoComposicao"] = relationship(
        back_populates="itens",
        foreign_keys=[versao_id],
        lazy="noload",
    )
