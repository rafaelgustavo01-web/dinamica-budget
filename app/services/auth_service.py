import uuid
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest, PasswordChangeRequest, ProfileUpdateRequest, TokenResponse, UsuarioCreate

logger = get_logger(__name__)

ACCESS_TOKEN_EXPIRE_SECONDS = 30 * 60


class AuthService:
    def __init__(self, repo: UsuarioRepository) -> None:
        self.repo = repo

    async def login(self, credentials: LoginRequest, db: AsyncSession) -> TokenResponse:
        user = await self.repo.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise AuthenticationError("Email ou senha inválidos.")
        if not user.is_active:
            raise AuthenticationError("Usuário inativo.")

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        token_hash = sha256(refresh_token.encode()).hexdigest()

        await self.repo.update_refresh_token(user.id, token_hash)
        logger.info("user_logged_in", user_id=str(user.id), email=user.email)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        )

    async def refresh_token(self, refresh_token: str, db: AsyncSession) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise AuthenticationError("Refresh token inválido.") from exc

        if payload.get("type") != "refresh":
            raise AuthenticationError("Tipo de token inválido.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Token sem identificador.")

        user = await self.repo.get_by_id(uuid.UUID(user_id_str))
        if not user or not user.is_active:
            raise AuthenticationError("Usuário não encontrado ou inativo.")

        expected_hash = sha256(refresh_token.encode()).hexdigest()
        if user.refresh_token_hash != expected_hash:
            raise AuthenticationError("Refresh token revogado.")

        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)
        await self.repo.update_refresh_token(user.id, sha256(new_refresh.encode()).hexdigest())

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_in=ACCESS_TOKEN_EXPIRE_SECONDS,
        )

    async def logout(self, user_id: uuid.UUID) -> None:
        await self.repo.update_refresh_token(user_id, None)

    async def create_user(self, data: UsuarioCreate) -> Usuario:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictError("Usuario", "email", data.email)
        user = Usuario(
            id=uuid.uuid4(),
            nome=data.nome,
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            is_admin=data.is_admin,
        )
        return await self.repo.create(user)

    async def update_profile(self, user_id: uuid.UUID, data: ProfileUpdateRequest) -> Usuario:
        user = await self.repo.update_nome(user_id, data.nome)
        if not user:
            raise AuthenticationError("Usuário não encontrado.")
        logger.info("user_profile_updated", user_id=str(user_id))
        return user

    async def change_password(self, user_id: uuid.UUID, data: PasswordChangeRequest) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("Usuário não encontrado.")
        if not verify_password(data.current_password, user.hashed_password):
            raise AuthenticationError("Senha atual incorreta.")
        await self.repo.update_hashed_password(user_id, hash_password(data.new_password))
        # Revoke refresh tokens so user must re-login with new password
        await self.repo.update_refresh_token(user_id, None)
        logger.info("user_password_changed", user_id=str(user_id))
