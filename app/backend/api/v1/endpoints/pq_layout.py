from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from backend.core.exceptions import NotFoundError
from backend.schemas.pq_layout import (
    PqLayoutAprovarRequest,
    PqLayoutCriarRequest,
    PqLayoutHistoricoResponse,
    PqLayoutResponse,
)
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


@router.post("/aprovar", response_model=PqLayoutResponse)
async def aprovar_layout(
    cliente_id: UUID,
    body: PqLayoutAprovarRequest,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PqLayoutResponse:
    svc = PqLayoutService(db)
    layout = await svc.obter_por_cliente(cliente_id)
    if layout is None:
        raise NotFoundError("PqLayoutCliente", f"cliente={cliente_id}")
    layout = await svc.aprovar(layout.id, current_user.id)
    return PqLayoutResponse.model_validate(layout)


@router.post("/sugerir", response_model=list[dict])
async def sugerir_mapeamento(
    cliente_id: UUID,
    arquivo: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    svc = PqLayoutService(db)
    from io import BytesIO
    import openpyxl

    contents = await arquivo.read()
    if arquivo.filename and arquivo.filename.lower().endswith(".xlsx"):
        wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
        ws = wb.active
        primeira = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [str(c) for c in primeira if c is not None]
        wb.close()
    else:
        import csv, io as bio
        text = contents.decode("utf-8-sig")
        reader = csv.reader(bio.StringIO(text))
        rows = list(reader)
        headers = [str(c) for c in rows[0]] if rows else []

    return svc.sugerir_mapeamento(headers)


@router.get("/historico", response_model=list[PqLayoutHistoricoResponse])
async def listar_historico(
    cliente_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PqLayoutHistoricoResponse]:
    svc = PqLayoutService(db)
    layout = await svc.obter_por_cliente(cliente_id)
    if layout is None:
        return []
    historico = await svc.listar_historico(layout.id)
    return [PqLayoutHistoricoResponse.model_validate(h) for h in historico]
