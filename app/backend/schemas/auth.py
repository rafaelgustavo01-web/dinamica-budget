from pydantic import BaseModel, EmailStr, Field, model_validator


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    username: EmailStr | None = None
    password: str

    @model_validator(mode="after")
    def normalize_login_identifier(self):
        if self.email is None and self.username is not None:
            self.email = self.username
        if self.email is None:
            raise ValueError("Informe email (ou username) para login.")
        return self


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    # P1.6: minimum 8 characters required
    password: str = Field(min_length=8, description="Senha com mínimo de 8 caracteres.")
    is_admin: bool = False


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}


class PerfilClienteResponse(BaseModel):
    cliente_id: str
    perfil: str
    cliente_nome: str = ""


class MeResponse(BaseModel):
    id: str
    nome: str
    email: str
    is_active: bool
    is_admin: bool
    perfis: list[PerfilClienteResponse]


class ProfileUpdateRequest(BaseModel):
    """Atualização parcial do perfil do próprio usuário."""
    nome: str = Field(min_length=2, max_length=200, description="Nome completo.")


class PasswordChangeRequest(BaseModel):
    """Troca de senha — exige senha atual para validação."""
    current_password: str = Field(description="Senha atual para verificação.")
    new_password: str = Field(min_length=8, description="Nova senha com mínimo de 8 caracteres.")
