from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from backend.schemas.pq_layout import PqLayoutCriarRequest, PqLayoutResponse
from backend.services.pq_layout_service import PqLayoutService

router = APIRouter(prefix="/clientes/{cliente_id}/pq-layout", tags=["pq-layout"])


@router.put("", response_model=PqLayoutResponse)
async def criar_ou_substituir_layout(
    cliente_id: UUID,
    body: PqLayoutCriarRequest,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PqLayoutResponse:
    svc = PqLayoutService(db)
    layout = await svc.criar_ou_substituir(cliente_id, body)
    await db.commit()
    await db.refresh(layout)
    return PqLayoutResponse.model_validate(layout)


@router.get("", response_model=PqLayoutResponse | None)
async def obter_layout(
    cliente_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqLayoutResponse | None:
    layout = await PqLayoutService(db).obter_por_cliente(cliente_id)
    if layout is None:
        return None
    return PqLayoutResponse.model_validate(layout)
