from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.api.v1.endpoints.clientes import create_cliente, patch_cliente
from backend.schemas.cliente import ClienteCreate, ClientePatch


def test_cliente_create_accepts_pc_fields_and_normalizes_values():
    data = ClienteCreate(
        nome_fantasia="Empresa X",
        cnpj="12345678000190",
        razao_social="Empresa X Engenharia S.A.",
        endereco_uf=" sp ",
        endereco_cep="01001000",
        contato_email="propostas@empresa.test",
        contato_telefone="",
    )

    assert data.endereco_uf == "SP"
    assert data.contato_telefone is None


def test_cliente_pc_fields_validate_export_contract_values():
    with pytest.raises(ValidationError):
        ClienteCreate(nome_fantasia="Empresa X", cnpj="12345678000190", endereco_cep="01001-000")

    with pytest.raises(ValidationError):
        ClientePatch(endereco_uf="SPO")

    with pytest.raises(ValidationError):
        ClientePatch(contato_email="email-invalido")


@pytest.mark.asyncio
async def test_create_cliente_passes_pc_fields_to_repository():
    cliente_id = uuid4()

    class Repo:
        async def get_by_cnpj(self, cnpj):
            return None

        async def create_cliente(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(id=cliente_id, is_active=True, **kwargs)

    repo = Repo()
    response = await create_cliente(
        data=ClienteCreate(
            nome_fantasia="Empresa X",
            cnpj="12345678000190",
            razao_social="Empresa X Engenharia S.A.",
            endereco_municipio="Sao Paulo",
            endereco_uf="SP",
            endereco_cep="01001000",
            contato_email="propostas@empresa.test",
        ),
        repo=repo,
    )

    assert repo.kwargs["razao_social"] == "Empresa X Engenharia S.A."
    assert repo.kwargs["endereco_cep"] == "01001000"
    assert response.razao_social == "Empresa X Engenharia S.A."
    assert response.contato_email == "propostas@empresa.test"


@pytest.mark.asyncio
async def test_patch_cliente_sends_only_fields_explicitly_set():
    cliente_id = uuid4()

    class Repo:
        async def update_cliente(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(
                id=cliente_id,
                nome_fantasia="Empresa X",
                cnpj="12345678000190",
                is_active=True,
                **{k: v for k, v in kwargs.items() if k not in {"cliente_id"}},
            )

    repo = Repo()
    response = await patch_cliente(
        cliente_id=cliente_id,
        data=ClientePatch(contato_email=None, endereco_uf="rj"),
        repo=repo,
    )

    assert repo.kwargs["contato_email"] is None
    assert repo.kwargs["endereco_uf"] == "RJ"
    assert "razao_social" not in repo.kwargs
    assert response.endereco_uf == "RJ"
