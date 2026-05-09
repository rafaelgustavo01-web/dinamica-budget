import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.enums import CampoSistemaPQ
from backend.models.pq_layout import PqImportacaoMapeamento, PqLayoutCliente, PqLayoutHistorico
from backend.schemas.pq_layout import MapeamentoItem, PqLayoutCriarRequest
from backend.services.pq_layout_service import PqLayoutService, _calcular_score


def _make_repo(layout=None):
    repo = AsyncMock()
    repo.get_by_cliente_id.return_value = layout
    repo.get_by_id.return_value = layout
    repo.create.side_effect = lambda x: x
    repo.delete_by_cliente_id.return_value = None
    repo.aprovar.return_value = None
    repo.registrar_historico.side_effect = lambda x: x
    repo.list_historico_by_layout.return_value = []
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
    assert result.is_aprovado is False


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


@pytest.mark.asyncio
async def test_aprovar_marca_layout_como_aprovado_e_registra_historico():
    layout = MagicMock(spec=PqLayoutCliente)
    layout.id = uuid.uuid4()
    layout.cliente_id = uuid.uuid4()
    repo = _make_repo(layout=layout)
    svc = _svc(repo)
    usuario_id = uuid.uuid4()

    result = await svc.aprovar(layout.id, usuario_id)

    repo.aprovar.assert_awaited_once_with(layout, usuario_id)
    repo.registrar_historico.assert_awaited_once()
    historico_call = repo.registrar_historico.await_args[0][0]
    assert historico_call.acao == "APROVADO"
    assert historico_call.usuario_id == usuario_id


@pytest.mark.asyncio
async def test_aprovar_levanta_notfound_quando_layout_inexistente():
    repo = _make_repo(layout=None)
    svc = _svc(repo)

    from backend.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await svc.aprovar(uuid.uuid4(), uuid.uuid4())


def test_sugerir_mapeamento_detecta_colunas_conhecidas():
    svc = PqLayoutService.__new__(PqLayoutService)
    headers = ["Código", "Descrição", "Unidade", "Quantidade"]
    sugestao = svc.sugerir_mapeamento(headers)
    campos = {s["campo_sistema"] for s in sugestao}
    assert "codigo" in campos
    assert "descricao" in campos
    assert "unidade" in campos
    assert "quantidade" in campos


def test_calcular_score_100_quando_todas_colunas_presentes():
    m1 = MagicMock(spec=PqImportacaoMapeamento)
    m1.campo_sistema = CampoSistemaPQ.DESCRICAO
    m1.coluna_planilha = "Descrição"
    layout = MagicMock(spec=PqLayoutCliente)
    layout.mapeamentos = [m1]
    layout.aliases_json = None

    score = _calcular_score(["Descrição"], layout)
    assert score == Decimal("1")


def test_calcular_score_0_quando_nenhuma_coluna_presente():
    m1 = MagicMock(spec=PqImportacaoMapeamento)
    m1.campo_sistema = CampoSistemaPQ.DESCRICAO
    m1.coluna_planilha = "Descrição"
    layout = MagicMock(spec=PqLayoutCliente)
    layout.mapeamentos = [m1]
    layout.aliases_json = None

    score = _calcular_score(["Outra"], layout)
    assert score == Decimal("0")


def test_calcular_score_0_sem_layout():
    assert _calcular_score(["Descricao"], None) == Decimal("0")
