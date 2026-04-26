import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.enums import CampoSistemaPQ
from backend.models.pq_layout import PqImportacaoMapeamento, PqLayoutCliente
from backend.schemas.pq_layout import MapeamentoItem, PqLayoutCriarRequest
from backend.services.pq_layout_service import PqLayoutService


def _make_repo(layout=None):
    repo = AsyncMock()
    repo.get_by_cliente_id.return_value = layout
    repo.create.side_effect = lambda x: x
    repo.delete_by_cliente_id.return_value = None
    return repo


def _req(*campos_extras) -> PqLayoutCriarRequest:
    mapeamentos = [
        MapeamentoItem(campo_sistema=CampoSistemaPQ.DESCRICAO, coluna_planilha="Descricao"),
        MapeamentoItem(campo_sistema=CampoSistemaPQ.QUANTIDADE, coluna_planilha="Qtde"),
        MapeamentoItem(campo_sistema=CampoSistemaPQ.UNIDADE, coluna_planilha="Und"),
    ]
    for campo, col in campos_extras:
        mapeamentos.append(MapeamentoItem(campo_sistema=campo, coluna_planilha=col))
    return PqLayoutCriarRequest(nome="Layout Teste", mapeamentos=mapeamentos)


def _svc(repo) -> PqLayoutService:
    svc = PqLayoutService.__new__(PqLayoutService)
    svc._db = MagicMock()
    svc._repo = repo
    return svc


@pytest.mark.asyncio
async def test_criar_ou_substituir_deleta_existente_e_cria_novo():
    repo = _make_repo()
    svc = _svc(repo)
    cliente_id = uuid.uuid4()

    result = await svc.criar_ou_substituir(cliente_id, _req())

    repo.delete_by_cliente_id.assert_awaited_once_with(cliente_id)
    repo.create.assert_awaited_once()
    assert result.cliente_id == cliente_id
    assert result.nome == "Layout Teste"


@pytest.mark.asyncio
async def test_criar_ou_substituir_gera_mapeamentos_corretos():
    repo = _make_repo()
    svc = _svc(repo)

    result = await svc.criar_ou_substituir(uuid.uuid4(), _req((CampoSistemaPQ.CODIGO, "Cod")))

    campos = {m.campo_sistema for m in result.mapeamentos}
    assert CampoSistemaPQ.DESCRICAO in campos
    assert CampoSistemaPQ.QUANTIDADE in campos
    assert CampoSistemaPQ.UNIDADE in campos
    assert CampoSistemaPQ.CODIGO in campos


@pytest.mark.asyncio
async def test_obter_por_cliente_retorna_none_quando_nao_existe():
    svc = _svc(_make_repo(layout=None))
    assert await svc.obter_por_cliente(uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_obter_por_cliente_retorna_layout_existente():
    layout = MagicMock(spec=PqLayoutCliente)
    svc = _svc(_make_repo(layout=layout))
    assert await svc.obter_por_cliente(uuid.uuid4()) is layout


def test_build_coluna_map_retorna_dict_correto():
    m1 = MagicMock(spec=PqImportacaoMapeamento)
    m1.campo_sistema = CampoSistemaPQ.DESCRICAO
    m1.coluna_planilha = "Servico"
    m2 = MagicMock(spec=PqImportacaoMapeamento)
    m2.campo_sistema = CampoSistemaPQ.QUANTIDADE
    m2.coluna_planilha = "Qtde"
    layout = MagicMock(spec=PqLayoutCliente)
    layout.mapeamentos = [m1, m2]

    svc = PqLayoutService.__new__(PqLayoutService)
    result = svc.build_coluna_map(layout)

    assert result == {"descricao": "Servico", "quantidade": "Qtde"}


def test_request_valida_campos_obrigatorios_faltando_descricao():
    with pytest.raises(Exception):
        PqLayoutCriarRequest(
            nome="X",
            mapeamentos=[
                MapeamentoItem(campo_sistema=CampoSistemaPQ.QUANTIDADE, coluna_planilha="Q"),
                MapeamentoItem(campo_sistema=CampoSistemaPQ.UNIDADE, coluna_planilha="U"),
            ],
        )


def test_request_aceita_mapeamentos_validos():
    req = _req()
    assert len(req.mapeamentos) == 3
