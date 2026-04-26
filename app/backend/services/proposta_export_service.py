from io import BytesIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError
from backend.repositories.cliente_repository import ClienteRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_item_composicao_repository import (
    PropostaItemComposicaoRepository,
)


class PropostaExportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.cliente_repo = ClienteRepository(db)
        self.item_repo = PropostaItemRepository(db)
        self.composicao_repo = PropostaItemComposicaoRepository(db)

    async def gerar_excel(self, proposta_id: UUID) -> bytes:
        raise NotImplementedError

    async def gerar_pdf(self, proposta_id: UUID) -> bytes:
        raise NotImplementedError
