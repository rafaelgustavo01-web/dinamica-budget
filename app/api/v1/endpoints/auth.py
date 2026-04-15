from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from app.core.rate_limit import limiter
from app.models.usuario import UsuarioPerfil
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    PasswordChangeRequest,
    PerfilClienteResponse,
    ProfileUpdateRequest,
    RefreshRequest,
    TokenResponse,
    UsuarioCreate,
    UsuarioResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UsuarioRepository(db))


@router.post("/login", response_model=TokenResponse, summary="Login JSON (frontend)")
@limiter.limit("10/minute")
async def login(
    request: Request,  # required by slowapi for rate limiting
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """
    Login via JSON body — used by the frontend application.
    Returns access_token + refresh_token.
    """
    return await svc.login(credentials, db)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login OAuth2 (Swagger Authorize)",
    include_in_schema=True,
)
@limiter.limit("10/minute")
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """
    OAuth2 Password Flow — accepts application/x-www-form-urlencoded.
    Used by Swagger UI 'Authorize' button (username = email).
    Does NOT replace /auth/login — both coexist.
    """
    credentials = LoginRequest(email=form_data.username, password=form_data.password)
    return await svc.login(credentials, db)


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token")
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,  # required by slowapi for rate limiting
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    return await svc.refresh_token(body.refresh_token, db)


@router.post("/logout", status_code=204, summary="Revogar token")
async def logout(
    current_user=Depends(get_current_active_user),
    svc: AuthService = Depends(_get_auth_service),
) -> None:
    await svc.logout(current_user.id)


@router.get("/me", response_model=MeResponse, summary="Usuário atual + perfis")
async def me(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    """Returns current user with all client/perfil bindings."""
    result = await db.execute(
        select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == current_user.id)
    )
    perfis_db = result.scalars().all()
    perfis = [
        PerfilClienteResponse(cliente_id=str(p.cliente_id), perfil=p.perfil)
        for p in perfis_db
    ]
    if current_user.is_admin:
        perfis.append(PerfilClienteResponse(cliente_id="*", perfil="ADMIN"))
    return MeResponse(
        id=str(current_user.id),
        nome=current_user.nome,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        perfis=perfis,
    )


@router.patch("/me", response_model=MeResponse, summary="Atualizar perfil próprio")
async def update_profile(
    data: ProfileUpdateRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(_get_auth_service),
) -> MeResponse:
    """Atualiza nome do próprio usuário autenticado."""
    await svc.update_profile(current_user.id, data)
    # Rebuild MeResponse with updated data
    result = await db.execute(
        select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == current_user.id)
    )
    perfis_db = result.scalars().all()
    perfis = [
        PerfilClienteResponse(cliente_id=str(p.cliente_id), perfil=p.perfil)
        for p in perfis_db
    ]
    if current_user.is_admin:
        perfis.append(PerfilClienteResponse(cliente_id="*", perfil="ADMIN"))
    updated_user = await svc.repo.get_by_id(current_user.id)
    return MeResponse(
        id=str(updated_user.id),
        nome=updated_user.nome,
        email=updated_user.email,
        is_active=updated_user.is_active,
        is_admin=updated_user.is_admin,
        perfis=perfis,
    )


@router.post("/trocar-senha", status_code=204, summary="Trocar senha")
async def change_password(
    data: PasswordChangeRequest,
    current_user=Depends(get_current_active_user),
    svc: AuthService = Depends(_get_auth_service),
) -> None:
    """
    Troca a senha do usuário autenticado.
    Exige senha atual para validação. Revoga refresh tokens após troca.
    """
    await svc.change_password(current_user.id, data)


@router.post(
    "/usuarios",
    response_model=UsuarioResponse,
    status_code=201,
    summary="Criar usuário (admin)",
    dependencies=[Depends(get_current_admin_user)],  # visible in OpenAPI as secured
)
async def create_usuario(
    data: UsuarioCreate,
    svc: AuthService = Depends(_get_auth_service),
) -> UsuarioResponse:
    """
    Create a new user. Requires an authenticated admin (is_admin=True).
    Unauthenticated or non-admin requests receive 401/403.
    """
    user = await svc.create_user(data)
    return UsuarioResponse.model_validate(user)
