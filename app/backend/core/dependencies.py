from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
from backend.core.exceptions import AuthenticationError, AuthorizationError
from backend.core.security import decode_token

# tokenUrl points to the OAuth2-compatible form endpoint used by Swagger "Authorize"
# The JSON-based /auth/login stays intact for the frontend.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    from backend.repositories.usuario_repository import UsuarioRepository

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise AuthenticationError(str(exc)) from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Tipo de token inválido.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Token sem identificador de usuário.")

    repo = UsuarioRepository(db)
    user = await repo.get_by_id(UUID(user_id_str))
    if not user:
        raise AuthenticationError("Usuário não encontrado.")
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise AuthorizationError("Usuário inativo.")
    return current_user


async def get_current_admin_user(current_user=Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise AuthorizationError("Acesso restrito a administradores.")
    return current_user


async def get_current_catalog_import_user(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allows catalog import for:
      1) platform admins (is_admin=True)
      2) users that hold ADMIN perfil on at least one client
    """
    if current_user.is_admin:
        return current_user

    from backend.models.usuario import UsuarioPerfil

    result = await db.execute(
        select(UsuarioPerfil.usuario_id).where(
            UsuarioPerfil.usuario_id == current_user.id,
            UsuarioPerfil.perfil == "ADMIN",
        ).limit(1)
    )
    has_admin_profile = result.scalar_one_or_none() is not None
    if not has_admin_profile:
        raise AuthorizationError(
            "Acesso restrito: atribua perfil ADMIN em ao menos um cliente para executar carga."
        )

    return current_user


async def _get_perfis_para_cliente(
    usuario_id: UUID,
    cliente_id: UUID,
    db: AsyncSession,
) -> list[str]:
    """Return perfis the user holds for the given client."""
    from backend.models.usuario import UsuarioPerfil

    result = await db.execute(
        select(UsuarioPerfil.perfil).where(
            UsuarioPerfil.usuario_id == usuario_id,
            UsuarioPerfil.cliente_id == cliente_id,
        )
    )
    return [row[0] for row in result.fetchall()]


async def require_cliente_access(
    cliente_id: UUID,
    current_user,
    db: AsyncSession,
) -> list[str]:
    """
    Validates user has any RBAC link to the given cliente.
    is_admin bypasses. Returns list of perfis.
    Raises AuthorizationError if no access.
    """
    if current_user.is_admin:
        return ["ADMIN"]

    perfis = await _get_perfis_para_cliente(current_user.id, cliente_id, db)
    if not perfis:
        raise AuthorizationError(
            f"Usuário não possui acesso ao cliente '{cliente_id}'."
        )
    return perfis


async def require_cliente_perfil(
    cliente_id: UUID,
    perfis_permitidos: list[str],
    current_user,
    db: AsyncSession,
) -> list[str]:
    """
    Validates user has at least one of the required perfis for the given cliente.
    is_admin bypasses. Returns list of user's perfis.
    Raises AuthorizationError if insufficient access.
    """
    if current_user.is_admin:
        return ["ADMIN"]

    perfis = await _get_perfis_para_cliente(current_user.id, cliente_id, db)
    if not any(p in perfis_permitidos for p in perfis):
        raise AuthorizationError(
            f"Perfil insuficiente para esta operação no cliente '{cliente_id}'. "
            f"Requerido: {perfis_permitidos}."
        )
    return perfis


async def require_proposta_role(
    proposta_id: UUID,
    papel_minimo: PropostaPapel | None,
    current_user,
    db: AsyncSession,
) -> PropostaPapel | None:
    from backend.models.enums import PropostaPapel
    from backend.services.proposta_acl_service import PropostaAclService

    if current_user.is_admin:
        return PropostaPapel.OWNER

    svc = PropostaAclService(db)
    papel = await svc.papel_efetivo(proposta_id, current_user.id)

    if papel_minimo is None:
        return papel

    nivel_user = PropostaAclService.HIERARQUIA.get(papel, 1)
    nivel_minimo = PropostaAclService.HIERARQUIA[papel_minimo]
    if nivel_user < nivel_minimo:
        raise AuthorizationError(
            f"Papel insuficiente nesta proposta. Requerido: {papel_minimo.value}."
        )
    return papel

