"""Tests for BcuUploadService — preview (no DB) and import (with DB)."""

import uuid
from io import BytesIO

import openpyxl
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError, ValidationError
from backend.models.bcu import BcuCabecalho, BcuMaoObraItem, BcuEquipamentoItem, BcuEncargoItem, BcuEpiItem, BcuFerramentaItem, BcuMobilizacaoItem
from backend.services.bcu_upload_service import BcuUploadService


def _make_xlsx(tipo: str, rows: list[list]):
    """Build a minimal XLSX in memory for the given tipo."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.read()


def _make_mo_xlsx():
    return _make_xlsx("mo", [
        ["codigo", "descricao", "salario", "reajuste", "periculosidade", "refeicao", "agua", "vale", "saude", "seguro", "ferias"],
        [None, "Eletricista", 5000, 100, 200, 150, 50, 200, 300, 50, 200],
        [None, "Pedreiro", 4000, 80, 150, 120, 40, 150, 250, 40, 150],
    ])


def _make_equipamentos_xlsx():
    return _make_xlsx("equipamentos", [
        ["codigo", "equipamento", "combustivel", "consumo", "aluguel", "aluguel_mensal"],
        ["EQP-001", "Britador", "Diesel", 5.0, 50.0, 15000.0],
    ])


def _make_encargos_xlsx():
    return _make_xlsx("encargos", [
        [None, "tipo", "grupo", "codigo", "discriminacao", "taxa"],
        [None, "HORISTA", "A", "001", "INSS", 0.11],
        [None, "MENSALISTA", "B", "002", "FGTS", 0.08],
    ])


def _make_epi_xlsx():
    return _make_xlsx("epi", [
        [None, "epi", "unidade", "custo", "vida_util"],
        [None, "Capacete", "UN", 50.0, 24],
    ])


def _make_ferramentas_xlsx():
    return _make_xlsx("ferramentas", [
        [None, "descricao", "unidade", "preco"],
        [None, "Martelo", "UN", 25.0],
    ])


def _make_mobilizacao_xlsx():
    return _make_xlsx("mobilizacao", [
        ["descricao", "funcao", "tipo"],
        ["Exame admissional", "150", "MO"],
    ])


@pytest.mark.asyncio
async def test_preview_mo_valid():
    svc = BcuUploadService(None)
    payload = _make_mo_xlsx()
    result = await svc.preview("mo", payload, "mo.xlsx")
    assert result.tipo == "mo"
    assert result.valid_rows == 2
    assert result.invalid_rows == 0
    assert len(result.db_items) == 2
    assert result.db_items[0].descricao_funcao == "Eletricista"


@pytest.mark.asyncio
async def test_preview_equipamentos_valid():
    svc = BcuUploadService(None)
    payload = _make_equipamentos_xlsx()
    result = await svc.preview("equipamentos", payload, "eqp.xlsx")
    assert result.valid_rows == 1
    assert result.db_items[0].equipamento == "Britador"


@pytest.mark.asyncio
async def test_preview_encargos_valid():
    svc = BcuUploadService(None)
    payload = _make_encargos_xlsx()
    result = await svc.preview("encargos", payload, "enc.xlsx")
    assert result.valid_rows == 2
    assert result.db_items[0].tipo_encargo == "HORISTA"


@pytest.mark.asyncio
async def test_preview_epi_valid():
    svc = BcuUploadService(None)
    payload = _make_epi_xlsx()
    result = await svc.preview("epi", payload, "epi.xlsx")
    assert result.valid_rows == 1
    assert result.db_items[0].epi == "Capacete"


@pytest.mark.asyncio
async def test_preview_ferramentas_valid():
    svc = BcuUploadService(None)
    payload = _make_ferramentas_xlsx()
    result = await svc.preview("ferramentas", payload, "fer.xlsx")
    assert result.valid_rows == 1
    assert result.db_items[0].descricao == "Martelo"


@pytest.mark.asyncio
async def test_preview_mobilizacao_valid():
    svc = BcuUploadService(None)
    payload = _make_mobilizacao_xlsx()
    result = await svc.preview("mobilizacao", payload, "mob.xlsx")
    assert result.valid_rows == 1
    assert result.db_items[0].descricao == "Exame admissional"


@pytest.mark.asyncio
async def test_preview_rejects_invalid_tipo():
    svc = BcuUploadService(None)
    with pytest.raises(ValidationError) as exc_info:
        await svc.preview("invalido", b"fake", "a.xlsx")
    assert "invalido" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_preview_rejects_non_xlsx():
    svc = BcuUploadService(None)
    with pytest.raises(ValidationError) as exc_info:
        await svc.preview("mo", b"fake", "a.csv")
    assert ".xlsx" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_preview_rejects_empty_file():
    svc = BcuUploadService(None)
    with pytest.raises(ValidationError) as exc_info:
        await svc.preview("mo", b"", "a.xlsx")
    assert "vazio" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_importar_mo_creates_items(db_session: AsyncSession, seed_user):
    cab = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="test.xlsx", is_ativo=False)
    db_session.add(cab)
    await db_session.commit()

    svc = BcuUploadService(db_session)
    payload = _make_mo_xlsx()
    result = await svc.importar("mo", payload, "mo.xlsx", cab.id, seed_user)
    await db_session.commit()

    assert result.valid_rows == 2
    items = await db_session.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(BcuMaoObraItem).where(BcuMaoObraItem.cabecalho_id == cab.id)
    )
    assert len(items.scalars().all()) == 2


@pytest.mark.asyncio
async def test_importar_rejects_invalid_rows(db_session: AsyncSession, seed_user):
    cab = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="test.xlsx", is_ativo=False)
    db_session.add(cab)
    await db_session.commit()

    svc = BcuUploadService(db_session)
    # xlsx with one invalid row (descricao too long) and one valid row
    payload = _make_xlsx("mo", [
        ["codigo", "descricao", "salario"],
        [None, "X" * 300, 5000],  # invalid: descricao > 255 chars
        [None, "Pedreiro", 4000],  # valid
    ])
    result = await svc.preview("mo", payload, "mo.xlsx")
    assert result.invalid_rows == 1
    with pytest.raises(UnprocessableEntityError) as exc_info:
        await svc.importar("mo", payload, "mo.xlsx", cab.id, seed_user)
    assert "inválida" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_importar_cabecalho_not_found(db_session: AsyncSession, seed_user):
    svc = BcuUploadService(db_session)
    with pytest.raises(NotFoundError):
        await svc.importar("mo", _make_mo_xlsx(), "mo.xlsx", uuid.uuid4(), seed_user)
