from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_active_user,
    get_db,
    require_cliente_access,
    require_cliente_perfil,
)
from app.schemas.common import PaginatedResponse
from app.schemas.homologacao import (
    AprovarHomologacaoRequest,
    AprovarHomologacaoResponse,
    CriarItemProprioRequest,
    ItemPendenteResponse,
)
from app.schemas.servico import ServicoTcpoResponse
from app.services.homologacao_service import homologacao_service

router = APIRouter(prefix="/homologacao", tags=["homologacao"])

_PERFIS_APROVADORES = ["APROVADOR", "ADMIN"]


@router.get("/pendentes", response_model=PaginatedResponse[ItemPendenteResponse])
async def listar_pendentes(
    cliente_id: UUID = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ItemPendenteResponse]:
    await require_cliente_perfil(cliente_id, _PERFIS_APROVADORES, current_user, db)
    return await homologacao_service.listar_pendentes(
        cliente_id=cliente_id,
        page=page,
        page_size=page_size,
        db=db,
    )


@router.post("/aprovar", response_model=AprovarHomologacaoResponse)
async def aprovar_item(
    request: AprovarHomologacaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AprovarHomologacaoResponse:
    # Validate the item's client before approving — service will also check
    await require_cliente_perfil(request.cliente_id, _PERFIS_APROVADORES, current_user, db)
    return await homologacao_service.aprovar(
        request=request,
        aprovador_id=current_user.id,
        aprovador_email=current_user.email,
        db=db,
    )


@router.post("/itens-proprios", response_model=ServicoTcpoResponse, status_code=201)
async def criar_item_proprio(
    request: CriarItemProprioRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    await require_cliente_access(request.cliente_id, current_user, db)
    servico = await homologacao_service.criar_item_proprio(
        request=request,
        criado_por_id=current_user.id,
        db=db,
    )
    return ServicoTcpoResponse.model_validate(servico)
