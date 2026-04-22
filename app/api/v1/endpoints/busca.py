import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_perfil
from app.core.exceptions import NotFoundError
from app.repositories.associacao_repository import AssociacaoRepository
from app.schemas.associacao import AssociacaoListItem
from app.schemas.busca import (
    AssociacaoResponse,
    BuscaServicoRequest,
    BuscaServicoResponse,
    CriarAssociacaoRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.busca_service import busca_service

router = APIRouter(prefix="/busca", tags=["busca"])


@router.post("/servicos", response_model=BuscaServicoResponse)
async def buscar_servicos(
    request: BuscaServicoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BuscaServicoResponse:
    return await busca_service.buscar(
        request=request,
        usuario_id=current_user.id,
        db=db,
    )


@router.post("/associar", response_model=AssociacaoResponse, status_code=201)
async def criar_associacao(
    request: CriarAssociacaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AssociacaoResponse:
    await require_cliente_access(request.cliente_id, current_user, db)
    return await busca_service.criar_associacao(
        request=request,
        usuario_id=current_user.id,
        db=db,
    )


@router.get(
    "/associacoes",
    response_model=PaginatedResponse[AssociacaoListItem],
    summary="Listar associações inteligentes do cliente",
)
async def list_associacoes(
    cliente_id: UUID = Query(..., description="ID do cliente"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AssociacaoListItem]:
    """
    Returns paginated list of intelligent associations for a client.
    On-premise model: any authenticated user may read associations.
    """
    repo = AssociacaoRepository(db)
    offset = (page - 1) * page_size
    items, total = await repo.list_by_cliente(cliente_id=cliente_id, offset=offset, limit=page_size)
    pages = math.ceil(total / page_size) if total else 0
    return PaginatedResponse(
        items=[AssociacaoListItem.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.delete(
    "/associacoes/{associacao_id}",
    status_code=204,
    summary="Excluir associação inteligente (APROVADOR+)",
)
async def delete_associacao(
    associacao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete an intelligent association.
    Requires APROVADOR or ADMIN on the association's client (or global is_admin).
    """
    repo = AssociacaoRepository(db)
    assoc = await repo.get_by_id(associacao_id)
    if not assoc:
        raise NotFoundError("AssociacaoInteligente", str(associacao_id))

    # Validate perfil on the association's client
    await require_cliente_perfil(
        cliente_id=assoc.cliente_id,
        perfis_permitidos=["APROVADOR", "ADMIN"],
        current_user=current_user,
        db=db,
    )

    await repo.delete(assoc)
