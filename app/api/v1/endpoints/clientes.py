"""
Client management endpoints.

Routes:
  GET   /clientes       — admin: list all clients
  POST  /clientes       — admin: create a new client
"""

import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user, get_db
from app.core.exceptions import ConflictError
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente import ClienteCreate, ClienteResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/clientes", tags=["clientes"])


def _get_repo(db: AsyncSession = Depends(get_db)) -> ClienteRepository:
    return ClienteRepository(db)


@router.get(
    "/",
    response_model=PaginatedResponse[ClienteResponse],
    summary="Listar clientes (admin)",
    dependencies=[Depends(get_current_admin_user)],
)
async def list_clientes(
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repo: ClienteRepository = Depends(_get_repo),
) -> PaginatedResponse[ClienteResponse]:
    """Admin-only: paginated list of all clients."""
    offset = (page - 1) * page_size
    items, total = await repo.list_paginated(offset=offset, limit=page_size, is_active=is_active)
    pages = math.ceil(total / page_size) if total else 0
    return PaginatedResponse(
        items=[ClienteResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=201,
    summary="Criar cliente (admin)",
    dependencies=[Depends(get_current_admin_user)],
)
async def create_cliente(
    data: ClienteCreate,
    repo: ClienteRepository = Depends(_get_repo),
) -> ClienteResponse:
    """Admin-only: create a new client. CNPJ must be unique."""
    existing = await repo.get_by_cnpj(data.cnpj)
    if existing:
        raise ConflictError("Cliente", "cnpj", data.cnpj)

    cliente = await repo.create_cliente(
        nome_fantasia=data.nome_fantasia,
        cnpj=data.cnpj,
    )
    return ClienteResponse.model_validate(cliente)
