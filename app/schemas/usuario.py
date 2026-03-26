"""
Schemas for user management and RBAC endpoints.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioAdminResponse(BaseModel):
    """Full user representation for admin listing."""
    id: UUID
    nome: str
    email: str
    is_active: bool
    is_admin: bool
    external_id_ad: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioPatch(BaseModel):
    """Partial update for a user — admin only. All fields optional."""
    nome: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    is_active: bool | None = None
    is_admin: bool | None = None


class PerfilClienteItem(BaseModel):
    """Single perfil entry for a user on a specific client."""
    cliente_id: UUID
    perfil: str  # USUARIO | APROVADOR | ADMIN

    model_config = ConfigDict(from_attributes=True)


class UsuarioPerfisResponse(BaseModel):
    """All RBAC perfis for one user."""
    usuario_id: UUID
    perfis: list[PerfilClienteItem]


class SetPerfisClienteRequest(BaseModel):
    """
    Replaces all perfis for a user on a specific client.
    Send an empty list to remove all access for that client.
    """
    cliente_id: UUID
    perfis: list[str] = Field(
        description="Perfis to assign: USUARIO, APROVADOR, ADMIN. Empty = remove all."
    )
