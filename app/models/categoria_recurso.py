from sqlalchemy import Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TipoCusto


class CategoriaRecurso(Base):
    __tablename__ = "categoria_recurso"
    __table_args__ = {"schema": "referencia"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_custo: Mapped[TipoCusto] = mapped_column(
        SAEnum(TipoCusto, name="tipo_custo_enum", create_type=False), nullable=False
    )

    itens_base: Mapped[list["BaseTcpo"]] = relationship(
        back_populates="categoria", lazy="noload"
    )
    itens_proprios: Mapped[list["ItemProprio"]] = relationship(
        back_populates="categoria", lazy="noload"
    )
