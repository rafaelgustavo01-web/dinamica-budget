from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_proposta_role
from backend.core.exceptions import NotFoundError
from backend.repositories.proposta_repository import PropostaRepository
from backend.services.proposta_export_service import PropostaExportService

router = APIRouter(prefix="/propostas/{proposta_id}/export", tags=["proposta-export"])


async def _get_proposta_or_404(db, proposta_id: UUID):
    proposta = await PropostaRepository(db).get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    return proposta


@router.get("/excel")
async def export_excel(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    from io import BytesIO

    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, None, current_user, db)

    raw = await PropostaExportService(db).gerar_excel(proposta_id)
    filename = f"proposta-{proposta.codigo}.xlsx"
    return StreamingResponse(
        BytesIO(raw),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf")
async def export_pdf(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    from io import BytesIO

    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, None, current_user, db)

    raw = await PropostaExportService(db).gerar_pdf(proposta_id)
    filename = f"proposta-{proposta.codigo}.pdf"
    return StreamingResponse(
        BytesIO(raw),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
