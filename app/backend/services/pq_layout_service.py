import uuid
from uuid import UUID

import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.pq_layout import PqImportacaoMapeamento, PqLayoutCliente
from backend.repositories.pq_layout_repository import PqLayoutRepository
from backend.schemas.pq_layout import PqLayoutCriarRequest


class PqLayoutService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = PqLayoutRepository(db)

    async def criar_ou_substituir(self, cliente_id: UUID, req: PqLayoutCriarRequest) -> PqLayoutCliente:
        await self._repo.delete_by_cliente_id(cliente_id)
        layout = PqLayoutCliente(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            nome=req.nome,
            aba_nome=req.aba_nome,
            linha_inicio=req.linha_inicio,
            mapeamentos=[],
        )
        for m in req.mapeamentos:
            layout.mapeamentos.append(
                PqImportacaoMapeamento(
                    id=uuid.uuid4(),
                    campo_sistema=m.campo_sistema,
                    coluna_planilha=m.coluna_planilha,
                )
            )
        return await self._repo.create(layout)

    async def obter_por_cliente(self, cliente_id: UUID) -> PqLayoutCliente | None:
        return await self._repo.get_by_cliente_id(cliente_id)

    def detectar_colunas_xlsx(self, filepath: str, aba_nome: str | None) -> list[str]:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb[aba_nome] if aba_nome and aba_nome in wb.sheetnames else wb.active
        primeira = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        wb.close()
        return [str(c) for c in primeira if c is not None]

    def build_coluna_map(self, layout: PqLayoutCliente) -> dict[str, str]:
        return {m.campo_sistema.value: m.coluna_planilha for m in layout.mapeamentos}
