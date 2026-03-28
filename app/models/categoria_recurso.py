from sqlalchemy import Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import TipoCusto


class CategoriaRecurso(Base):
    __tablename__ = "categoria_recurso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    descricao: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_custo: Mapped[TipoCusto] = mapped_column(
        SAEnum(TipoCusto, name="tipo_custo_enum", create_type=False), nullable=False
    )

    servicos: Mapped[list["ServicoTcpo"]] = relationship(
        back_populates="categoria", lazy="noload"
    )
