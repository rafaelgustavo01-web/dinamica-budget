from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_access
from app.repositories.proposta_repository import PropostaRepository
from app.schemas.common import PaginatedResponse
from app.schemas.proposta import PropostaCreate, PropostaResponse, PropostaUpdate
from app.services.proposta_service import PropostaService

router = APIRouter(prefix="/propostas", tags=["propostas"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PropostaService:
    return PropostaService(PropostaRepository(db))


@router.post("/", response_model=PropostaResponse, status_code=status.HTTP_201_CREATED)
async def criar_proposta(
    data: PropostaCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PropostaResponse:
    await require_cliente_access(data.cliente_id, current_user, db)
    proposta = await svc.criar_proposta(data.cliente_id, current_user.id, data)
    return PropostaResponse.model_validate(proposta)


@router.get("/", response_model=PaginatedResponse[PropostaResponse])
async def listar_propostas(
    cliente_id: UUID = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PaginatedResponse[PropostaResponse]:
    await require_cliente_access(cliente_id, current_user, db)
    items, total = await svc.listar_propostas(cliente_id, page=page, page_size=page_size)
    pages = ceil(total / page_size) if total else 0
    return PaginatedResponse[PropostaResponse](
        items=[PropostaResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{proposta_id}", response_model=PropostaResponse)
async def obter_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PropostaResponse:
    proposta = await svc.obter_por_id(proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)
    return PropostaResponse.model_validate(proposta)


@router.patch("/{proposta_id}", response_model=PropostaResponse)
async def atualizar_proposta(
    proposta_id: UUID,
    data: PropostaUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PropostaResponse:
    proposta = await svc.obter_por_id(proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)
    proposta = await svc.atualizar_metadados(proposta_id, proposta.cliente_id, data)
    return PropostaResponse.model_validate(proposta)


@router.delete("/{proposta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> None:
    proposta = await svc.obter_por_id(proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)
    await svc.soft_delete(proposta_id, proposta.cliente_id)
