import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.bcu import BcuCabecalho, BcuMaoObraItem, BcuEquipamentoItem, BcuEpiItem, BcuFerramentaItem
from backend.services.bcu_service import BcuService


@pytest.fixture
def bcu_service(db_session: AsyncSession):
    return BcuService(db_session)


class FakeWorksheet:
    def __init__(self, data: list[list]):
        self._data = data

    def iter_rows(self, min_row=1, max_row=None, values_only=False):
        start = min_row - 1
        end = max_row if max_row else len(self._data)
        for row in self._data[start:end]:
            yield tuple(row)


class FakeWorkbook:
    def __init__(self, sheets: dict[str, FakeWorksheet]):
        self.sheetnames = list(sheets.keys())
        self._sheets = sheets

    def __getitem__(self, name: str):
        return self._sheets[name]


def _make_mao_obra_ws():
    return FakeWorksheet([
        [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ["Descrição", "Quantidade", "Salário", "Reajuste", "Encargos", "Periculosidade", "Refeição", "Água", "Vale Alimentação", "Plano Saúde", "Ferramentas", "Seguro", "Férias", "Uniforme", "EPI", "Custo Unitário (H)", "Custo Mensal", None, "Mobilização"],
        ["Eletricista", 1, 5000, 100, 0.3, 200, 150, 50, 200, 300, 100, 50, 200, 100, 150, 25.5, 5000, None, 300],
        ["Pedreiro", 1, 4000, 80, 0.25, 150, 120, 40, 150, 250, 80, 40, 150, 80, 100, 20.0, 4000, None, 200],
    ])


def _make_equipamentos_ws():
    return FakeWorksheet([
        [None, None, None, None, None, None, None, None, "Horas/mês", 220],
        [None, None, None, None, None, None, None, None, "Gasolina", 6.5],
        [None, None, None, None, None, None, None, None, "Diesel", 5.8],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None],
        ["CÓDIGO", "EQUIPAMENTO", "COMBUSTÍVEL", "CONSUMO", "ALUGUEL", "COMBUSTÍVEL/h", "MÃO DE OBRA/h", "H PRODUT.", "H IMPROD.", "MÊS", None, "ALUGUEL MENSAL"],
        ["EQP-001", "Britador", "D", 5.0, 50.0, 25.0, 15.0, 8.0, 2.0, 2000.0, None, 15000.0],
    ])


def _make_encargos_ws(tipo: str):
    return FakeWorksheet([
        [None, None, None, None, None, None],
        [None, None, None, None, None, None],
        [None, None, None, None, None, None],
        ["A", "001", "INSS", None, None, 0.11],
        ["A", "002", "FGTS", None, None, 0.08],
    ])


def _make_epi_ws():
    return FakeWorksheet([
        [None, None, None, None, None, None, None, None, "OFICIAL", "AJUDANTE"],
        [None, "EPI", "UNID", "CUSTO UNITÁRIO", "QTDE", "VIDA ÚTIL", "CUSTO COM EPI(MÊS)"],
        [None, "Capacete", "UN", 50.0, 1, 24, 2.08, "S", "S"],
    ])


def _make_ferramentas_ws():
    return FakeWorksheet([
        [None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None],
        [None, "ITEM", "DESCRIÇÃO", "UNID.", "QUANT.", "PREÇO", "PREÇO TOTAL"],
        [None, "FER-001", "Martelo", "UN", 2, 25.0, 50.0],
    ])


def _make_mobilizacao_ws():
    return FakeWorksheet([
        [None, None, None, None, None, None, None, None, None, None, None, None],
        [None, None, "ENG", "TEC", "AUX IND", "ADM", "ENC", "AJUD", "OFI", "OPE", "ELE"],
        [None, None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None, None, None, None, None],
        ["Exame admissional", "150", 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ])


def _make_workbook():
    return FakeWorkbook({
        "MÃO DE OBRA": _make_mao_obra_ws(),
        "EQUIPAMENTOS": _make_equipamentos_ws(),
        "ENCARGOS HORISTA": _make_encargos_ws("HORISTA"),
        "ENCARGOS MENSALISTA": _make_encargos_ws("MENSALISTA"),
        "EPI-UNIFORME": _make_epi_ws(),
        "FERRAMENTAS": _make_ferramentas_ws(),
        "MOBILIZAÇÃO": _make_mobilizacao_ws(),
    })


@pytest.mark.asyncio
async def test_importar_bcu_cria_cabecalho_e_itens(bcu_service: BcuService, db_session: AsyncSession):
    wb = _make_workbook()
    with patch("backend.services.bcu_service.openpyxl.load_workbook", return_value=wb):
        criador_id = uuid.uuid4()
        cab = await bcu_service.importar_bcu(b"fake", "BCU_test.xlsx", criador_id)

    assert cab is not None
    assert cab.nome_arquivo == "BCU_test.xlsx"
    assert cab.is_ativo is False
    assert cab.criado_por_id == criador_id


@pytest.mark.asyncio
async def test_importar_bcu_gera_codigo_origem_sequencial(bcu_service: BcuService, db_session: AsyncSession):
    wb = _make_workbook()
    with patch("backend.services.bcu_service.openpyxl.load_workbook", return_value=wb):
        cab = await bcu_service.importar_bcu(b"fake", "BCU_seq.xlsx", uuid.uuid4())

    result = await db_session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(BcuMaoObraItem).where(BcuMaoObraItem.cabecalho_id == cab.id)
    )
    items = result.scalars().all()
    assert len(items) == 2
    assert items[0].codigo_origem == "BCU-MO-001"
    assert items[1].codigo_origem == "BCU-MO-002"


@pytest.mark.asyncio
async def test_importar_bcu_idempotencia_reimporta_atualiza(bcu_service: BcuService, db_session: AsyncSession):
    wb = _make_workbook()
    with patch("backend.services.bcu_service.openpyxl.load_workbook", return_value=wb):
        cab1 = await bcu_service.importar_bcu(b"fake", "BCU_idem.xlsx", uuid.uuid4())
        cab2 = await bcu_service.importar_bcu(b"fake", "BCU_idem.xlsx", uuid.uuid4())

    # Deve ter deletado o anterior e criado novo
    assert cab1.id != cab2.id


@pytest.mark.asyncio
async def test_ativar_cabecalho_desativa_anteriores(bcu_service: BcuService, db_session: AsyncSession):
    cab1 = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="a.xlsx", is_ativo=False)
    cab2 = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="b.xlsx", is_ativo=False)
    db_session.add_all([cab1, cab2])
    await db_session.commit()

    ativado = await bcu_service.ativar_cabecalho(cab2.id)
    assert ativado.is_ativo is True

    # cab1 deve estar desativado
    result = await db_session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(BcuCabecalho).where(BcuCabecalho.id == cab1.id)
    )
    cab1_refreshed = result.scalar_one()
    assert cab1_refreshed.is_ativo is False


@pytest.mark.asyncio
async def test_ativar_cabecalho_idempotente(bcu_service: BcuService, db_session: AsyncSession):
    cab = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="c.xlsx", is_ativo=True)
    db_session.add(cab)
    await db_session.commit()

    ativado = await bcu_service.ativar_cabecalho(cab.id)
    assert ativado.is_ativo is True


@pytest.mark.asyncio
async def test_get_cabecalho_ativo_retorna_ativo(bcu_service: BcuService, db_session: AsyncSession):
    cab = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="ativo.xlsx", is_ativo=True)
    db_session.add(cab)
    await db_session.commit()

    result = await bcu_service.get_cabecalho_ativo()
    assert result is not None
    assert result.id == cab.id


@pytest.mark.asyncio
async def test_get_cabecalho_ativo_sem_ativo_retorna_none(bcu_service: BcuService, db_session: AsyncSession):
    result = await bcu_service.get_cabecalho_ativo()
    assert result is None


@pytest.mark.asyncio
async def test_importar_bcu_sync_base_tcpo(bcu_service: BcuService, db_session: AsyncSession):
    wb = _make_workbook()
    with patch("backend.services.bcu_service.openpyxl.load_workbook", return_value=wb):
        await bcu_service.importar_bcu(b"fake", "BCU_sync.xlsx", uuid.uuid4())

    from backend.models.base_tcpo import BaseTcpo
    result = await db_session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(BaseTcpo).where(BaseTcpo.codigo_origem.like("BCU-%"))
    )
    items = result.scalars().all()
    # 2 MO + 1 EQP + 1 EPI + 1 FER = 5
    assert len(items) == 5


@pytest.mark.asyncio
async def test_importar_bcu_com_aba_faltante_rejeita(bcu_service: BcuService, db_session: AsyncSession):
    wb = FakeWorkbook({"SOMENTE UMA ABA": FakeWorksheet([["test"]])})
    with patch("backend.services.bcu_service.openpyxl.load_workbook", return_value=wb):
        cab = await bcu_service.importar_bcu(b"fake", "BCU_parcial.xlsx", uuid.uuid4())
    # Nao deve falhar, mas nao cria itens
    result = await db_session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(BcuMaoObraItem).where(BcuMaoObraItem.cabecalho_id == cab.id)
    )
    assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_importar_bcu_arquivo_vazio_rejeita(bcu_service: BcuService, db_session: AsyncSession):
    with pytest.raises(Exception):
        with patch("backend.services.bcu_service.openpyxl.load_workbook", side_effect=Exception("Arquivo vazio")):
            await bcu_service.importar_bcu(b"", "BCU_vazio.xlsx", uuid.uuid4())
