"""
User management endpoints — admin operations and RBAC profile management.

Routes:
  GET    /usuarios                        — admin: list all users (paginated)
  PATCH  /usuarios/{id}                   — admin: partial update
  GET    /usuarios/{id}/perfis-cliente    — admin or self: list RBAC bindings
  PUT    /usuarios/{id}/perfis-cliente    — admin: replace perfis on a client
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_db,
)
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import UsuarioResponse
from app.schemas.common import PaginatedResponse
from app.schemas.usuario import (
    PerfilClienteItem,
    SetPerfisClienteRequest,
    UsuarioAdminResponse,
    UsuarioPatch,
    UsuarioPerfisResponse,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _get_repo(db: AsyncSession = Depends(get_db)) -> UsuarioRepository:
    return UsuarioRepository(db)


@router.get(
    "/",
    response_model=PaginatedResponse[UsuarioAdminResponse],
    summary="Listar usuários (admin)",
    dependencies=[Depends(get_current_admin_user)],
)
async def list_usuarios(
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repo: UsuarioRepository = Depends(_get_repo),
) -> PaginatedResponse[UsuarioAdminResponse]:
    """Admin-only: paginated list of all users."""
    import math

    offset = (page - 1) * page_size
    items, total = await repo.list_paginated(offset=offset, limit=page_size, is_active=is_active)
    pages = math.ceil(total / page_size) if total else 0
    return PaginatedResponse(
        items=[UsuarioAdminResponse.model_validate(u) for u in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioAdminResponse,
    summary="Atualizar usuário (admin)",
    dependencies=[Depends(get_current_admin_user)],
)
async def patch_usuario(
    usuario_id: UUID,
    data: UsuarioPatch,
    repo: UsuarioRepository = Depends(_get_repo),
) -> UsuarioAdminResponse:
    """Admin-only: partial update of a user (nome, email, is_active, is_admin)."""
    user = await repo.get_by_id(usuario_id)
    if not user:
        raise NotFoundError("Usuario", str(usuario_id))

    if data.nome is not None:
        user.nome = data.nome
    if data.email is not None:
        existing = await repo.get_by_email(str(data.email))
        if existing and existing.id != usuario_id:
            raise ConflictError("Usuario", "email", str(data.email))
        user.email = str(data.email).lower()
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_admin is not None:
        user.is_admin = data.is_admin

    user = await repo.update(user)
    return UsuarioAdminResponse.model_validate(user)


@router.get(
    "/{usuario_id}/perfis-cliente",
    response_model=UsuarioPerfisResponse,
    summary="Listar perfis do usuário por cliente",
)
async def get_perfis_cliente(
    usuario_id: UUID,
    current_user=Depends(get_current_active_user),
    repo: UsuarioRepository = Depends(_get_repo),
) -> UsuarioPerfisResponse:
    """
    Returns all RBAC bindings (client + perfil) for a user.
    Admin can query any user. A regular user can only query themselves.
    """
    if not current_user.is_admin and current_user.id != usuario_id:
        raise AuthorizationError("Acesso negado: só é possível consultar os próprios perfis.")

    user = await repo.get_by_id(usuario_id)
    if not user:
        raise NotFoundError("Usuario", str(usuario_id))

    perfis = await repo.get_perfis(usuario_id)
    return UsuarioPerfisResponse(
        usuario_id=usuario_id,
        perfis=[
            PerfilClienteItem(cliente_id=p.cliente_id, perfil=p.perfil)
            for p in perfis
        ],
    )


@router.put(
    "/{usuario_id}/perfis-cliente",
    response_model=UsuarioPerfisResponse,
    summary="Definir perfis do usuário em um cliente (admin)",
    dependencies=[Depends(get_current_admin_user)],
)
async def set_perfis_cliente(
    usuario_id: UUID,
    data: SetPerfisClienteRequest,
    repo: UsuarioRepository = Depends(_get_repo),
) -> UsuarioPerfisResponse:
    """
    Admin-only: replace all perfis for a user on a specific client.
    Send perfis=[] to revoke all access for that client.
    Valid perfis: USUARIO, APROVADOR, ADMIN.
    """
    user = await repo.get_by_id(usuario_id)
    if not user:
        raise NotFoundError("Usuario", str(usuario_id))

    _VALID_PERFIS = {"USUARIO", "APROVADOR", "ADMIN"}
    invalid = [p for p in data.perfis if p.upper() not in _VALID_PERFIS]
    if invalid:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"Perfis inválidos: {invalid}. Válidos: {sorted(_VALID_PERFIS)}")

    await repo.set_perfis_cliente(
        usuario_id=usuario_id,
        cliente_id=data.cliente_id,
        perfis=data.perfis,
    )

    # Return updated full perfis list
    all_perfis = await repo.get_perfis(usuario_id)
    return UsuarioPerfisResponse(
        usuario_id=usuario_id,
        perfis=[
            PerfilClienteItem(cliente_id=p.cliente_id, perfil=p.perfil)
            for p in all_perfis
        ],
    )
