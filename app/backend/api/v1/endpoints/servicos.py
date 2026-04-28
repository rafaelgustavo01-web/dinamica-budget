from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_db,
    require_cliente_access,
)
from backend.schemas.common import PaginatedResponse
from backend.schemas.servico import (
    ComposicaoComponenteResponse,
    ExplodeComposicaoResponse,
    ServicoCreate,
    ServicoListParams,
    ServicoTcpoResponse,
)
from backend.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/servicos", tags=["servicos"])


@router.get("/", response_model=PaginatedResponse[ServicoTcpoResponse])
async def list_servicos(
    q: str | None = Query(default=None),
    categoria_id: int | None = Query(default=None),
    cliente_id: UUID | None = Query(default=None, description="Scope to client visibility"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ServicoTcpoResponse]:
    if cliente_id:
        await require_cliente_access(cliente_id, current_user, db)
    params = ServicoListParams(q=q, categoria_id=categoria_id, page=page, page_size=page_size)
    return await servico_catalog_service.list_servicos(params, db, cliente_id=cliente_id)


@router.get("/{servico_id}", response_model=ServicoTcpoResponse)
async def get_servico(
    servico_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    """
    Returns a service by ID.
    On-premise model: any authenticated user may read any service (global or PROPRIA).
    Write operations remain protected by per-client RBAC.
    """
    return await servico_catalog_service.get_servico(servico_id, db)


@router.get("/{servico_id}/composicao", response_model=ExplodeComposicaoResponse)
async def explode_composicao(
    servico_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExplodeComposicaoResponse:
    return await servico_catalog_service.explode_composicao(servico_id, db)


@router.get(
    "/{servico_id}/componentes",
    response_model=list[ComposicaoComponenteResponse],
    summary="Listar componentes diretos (nível 1) de uma composição",
)
async def listar_componentes_diretos(
    servico_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComposicaoComponenteResponse]:
    return await servico_catalog_service.listar_componentes_diretos(servico_id, db)


@router.post("/", response_model=ServicoTcpoResponse, status_code=201)
async def create_servico(
    data: ServicoCreate,
    _=Depends(get_current_admin_user),  # global TCPO creation: admin only
    db: AsyncSession = Depends(get_db),
) -> ServicoTcpoResponse:
    """
    Create a global TCPO catalog entry. Admin only.
    For client-specific items use POST /homologacao/itens-proprios.
    """
    return await servico_catalog_service.create_servico(data, db)

