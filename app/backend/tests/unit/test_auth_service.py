import uuid
import pytest
from unittest.mock import AsyncMock

from backend.services.auth_service import AuthService
from backend.core.exceptions import AuthenticationError


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_repo):
    return AuthService(mock_repo)


@pytest.mark.asyncio
async def test_get_user_profile_success(auth_service, mock_repo):
    from backend.models.usuario import Usuario, UsuarioPerfil

    user_id = uuid.uuid4()
    cliente_id = uuid.uuid4()
    user = Usuario(
        id=user_id,
        nome="Test User",
        email="test@example.com",
        is_admin=False,
        is_active=True,
    )
    perfil = UsuarioPerfil(usuario_id=user_id, cliente_id=cliente_id, perfil="USUARIO")

    mock_repo.get_by_id.return_value = user
    mock_repo.get_perfis_with_nomes.return_value = [(perfil, "Test Cliente")]

    result = await auth_service.get_user_profile(user_id)

    assert result["nome"] == "Test User"
    assert result["email"] == "test@example.com"
    assert result["is_admin"] is False
    assert len(result["perfis"]) == 1
    assert result["perfis"][0].perfil == "USUARIO"
    assert result["perfis"][0].cliente_id == str(cliente_id)
    assert result["perfis"][0].cliente_nome == "Test Cliente"


@pytest.mark.asyncio
async def test_get_user_profile_admin_adds_wildcard(auth_service, mock_repo):
    from backend.models.usuario import Usuario

    user_id = uuid.uuid4()
    user = Usuario(
        id=user_id,
        nome="Admin User",
        email="admin@example.com",
        is_admin=True,
        is_active=True,
    )
    mock_repo.get_by_id.return_value = user
    mock_repo.get_perfis_with_nomes.return_value = []

    result = await auth_service.get_user_profile(user_id)

    assert len(result["perfis"]) == 1
    assert result["perfis"][0].cliente_id == "*"
    assert result["perfis"][0].perfil == "ADMIN"


@pytest.mark.asyncio
async def test_get_user_profile_not_found(auth_service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(AuthenticationError, match="Usuário não encontrado"):
        await auth_service.get_user_profile(uuid.uuid4())

