"""
Unit tests for governance routes and schema fixes (items 1–6).

Tests covered:
  1. /auth/login still accepts JSON body
  2. /auth/token route exists and accepts form data (OAuth2)
  3. Swagger tokenUrl points to /auth/token
  4. BuscaServicoResponse uses BuscaMetadados (not dict)
  5. BuscaMetadados is a typed Pydantic model
  6. GET /usuarios has admin dependency
  7. PATCH /usuarios/{id} has admin dependency
  8. GET /usuarios/{id}/perfis-cliente exists
  9. PUT /usuarios/{id}/perfis-cliente has admin dependency
  10. GET /busca/associacoes exists with client scoping
  11. DELETE /busca/associacoes/{id} exists
  12. GET /clientes has admin dependency
  13. POST /clientes has admin dependency
  14. ClienteCreate validates CNPJ format (14 digits)
  15. SetPerfisClienteRequest validates structure
"""

import inspect
import pytest
from pydantic import ValidationError


# ─── 1 & 2: Auth endpoint contracts ──────────────────────────────────────────

def test_login_endpoint_accepts_json_body():
    """POST /auth/login uses LoginRequest (JSON) — frontend contract intact."""
    from app.schemas.auth import LoginRequest
    from app.api.v1.endpoints.auth import login

    sig = inspect.signature(login)
    # 'credentials' parameter should be of type LoginRequest
    assert "credentials" in sig.parameters
    assert sig.parameters["credentials"].annotation is LoginRequest


def test_token_endpoint_exists():
    """POST /auth/token must exist for OAuth2 Swagger 'Authorize' button."""
    from app.api.v1.endpoints.auth import login_form
    assert callable(login_form)
    assert inspect.iscoroutinefunction(login_form)


def test_token_endpoint_uses_oauth2_form():
    """POST /auth/token must accept OAuth2PasswordRequestForm."""
    from fastapi.security import OAuth2PasswordRequestForm
    from app.api.v1.endpoints.auth import login_form

    sig = inspect.signature(login_form)
    form_param = sig.parameters.get("form_data")
    assert form_param is not None, "login_form must have a form_data parameter"


def test_oauth2_scheme_tokenurl_points_to_token():
    """OAuth2PasswordBearer tokenUrl must point to /auth/token for Swagger."""
    from app.core.dependencies import oauth2_scheme
    assert "/auth/token" in oauth2_scheme.model.flows.password.tokenUrl


# ─── 3 & 4: BuscaMetadados typed schema ─────────────────────────────────────

def test_busca_metadados_is_typed_model():
    """BuscaMetadados must be a Pydantic BaseModel, not dict."""
    from pydantic import BaseModel
    from app.schemas.busca import BuscaMetadados
    assert issubclass(BuscaMetadados, BaseModel)


def test_busca_metadados_fields():
    """BuscaMetadados must have tempo_processamento_ms (int) and id_historico_busca (UUID)."""
    import uuid
    from app.schemas.busca import BuscaMetadados

    m = BuscaMetadados(tempo_processamento_ms=42, id_historico_busca=uuid.uuid4())
    assert m.tempo_processamento_ms == 42
    assert isinstance(m.id_historico_busca, uuid.UUID)


def test_busca_servico_response_uses_metadados_model():
    """BuscaServicoResponse.metadados must be BuscaMetadados, not dict."""
    import typing
    from app.schemas.busca import BuscaServicoResponse, BuscaMetadados

    field = BuscaServicoResponse.model_fields["metadados"]
    # The annotation should be BuscaMetadados
    assert field.annotation is BuscaMetadados, (
        f"metadados field must be BuscaMetadados, got {field.annotation}"
    )


# ─── 5–8: Governance route protection ────────────────────────────────────────

def _route_has_admin_dep(router, endpoint_func) -> bool:
    """Check if a route has get_current_admin_user in its dependencies."""
    from app.core.dependencies import get_current_admin_user

    for route in router.routes:
        if not hasattr(route, "endpoint"):
            continue
        if route.endpoint is not endpoint_func:
            continue
        for dep in getattr(route, "dependencies", []):
            if hasattr(dep, "dependency") and dep.dependency is get_current_admin_user:
                return True
        # also check function signature
        sig = inspect.signature(endpoint_func)
        for param in sig.parameters.values():
            if hasattr(param.default, "dependency") and param.default.dependency is get_current_admin_user:
                return True
    return False


def test_list_usuarios_requires_admin():
    from app.api.v1.endpoints.usuarios import router, list_usuarios
    assert _route_has_admin_dep(router, list_usuarios)


def test_patch_usuario_requires_admin():
    from app.api.v1.endpoints.usuarios import router, patch_usuario
    assert _route_has_admin_dep(router, patch_usuario)


def test_set_perfis_cliente_requires_admin():
    from app.api.v1.endpoints.usuarios import router, set_perfis_cliente
    assert _route_has_admin_dep(router, set_perfis_cliente)


def test_get_perfis_cliente_exists_and_is_async():
    from app.api.v1.endpoints.usuarios import get_perfis_cliente
    assert inspect.iscoroutinefunction(get_perfis_cliente)


def test_list_clientes_requires_admin():
    from app.api.v1.endpoints.clientes import router, list_clientes
    assert _route_has_admin_dep(router, list_clientes)


def test_create_cliente_requires_admin():
    from app.api.v1.endpoints.clientes import router, create_cliente
    assert _route_has_admin_dep(router, create_cliente)


def test_patch_cliente_requires_admin():
    from app.api.v1.endpoints.clientes import router, patch_cliente
    assert _route_has_admin_dep(router, patch_cliente)


# ─── 9: Associations governance ──────────────────────────────────────────────

def test_list_associacoes_endpoint_exists():
    from app.api.v1.endpoints.busca import list_associacoes
    assert inspect.iscoroutinefunction(list_associacoes)


def test_delete_associacao_endpoint_exists():
    from app.api.v1.endpoints.busca import delete_associacao
    assert inspect.iscoroutinefunction(delete_associacao)


# ─── 10: Schema validation ───────────────────────────────────────────────────

def test_cliente_create_rejects_invalid_cnpj():
    """ClienteCreate must reject CNPJs shorter or longer than 14 numeric digits."""
    from app.schemas.cliente import ClienteCreate

    with pytest.raises(ValidationError):
        ClienteCreate(nome_fantasia="Empresa X", cnpj="123")  # too short

    with pytest.raises(ValidationError):
        ClienteCreate(nome_fantasia="Empresa X", cnpj="12.345.678/0001-90")  # has mask

    with pytest.raises(ValidationError):
        ClienteCreate(nome_fantasia="Empresa X", cnpj="1234567890123456")  # too long


def test_cliente_create_accepts_valid_cnpj():
    from app.schemas.cliente import ClienteCreate

    c = ClienteCreate(nome_fantasia="Empresa X", cnpj="12345678000190")
    assert c.cnpj == "12345678000190"
    assert len(c.cnpj) == 14


def test_set_perfis_cliente_request_structure():
    """SetPerfisClienteRequest must accept a list of perfis for a cliente_id."""
    import uuid
    from app.schemas.usuario import SetPerfisClienteRequest

    req = SetPerfisClienteRequest(
        cliente_id=uuid.uuid4(),
        perfis=["USUARIO", "APROVADOR"],
    )
    assert len(req.perfis) == 2


def test_set_perfis_cliente_request_allows_empty():
    """Empty perfis list is valid (revoke all access for client)."""
    import uuid
    from app.schemas.usuario import SetPerfisClienteRequest

    req = SetPerfisClienteRequest(cliente_id=uuid.uuid4(), perfis=[])
    assert req.perfis == []


# ─── 16: status_homologacao defaults to PENDENTE ─────────────────────────────

def test_servico_tcpo_model_defaults_to_pendente():
    """ServicoTcpo ORM default must be PENDENTE (defense-in-depth)."""
    from app.models.servico_tcpo import ServicoTcpo
    from app.models.enums import StatusHomologacao

    field = ServicoTcpo.__table__.columns["status_homologacao"]
    # Check the ORM-level default (Column.default.arg)
    assert field.default.arg == StatusHomologacao.PENDENTE
