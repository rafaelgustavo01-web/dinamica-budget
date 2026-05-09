"""Tests for BcuCrudService — create, update, delete items safely."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.models.bcu import (
    BcuCabecalho,
    BcuEncargoItem,
    BcuEquipamentoItem,
    BcuEpiItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuMobilizacaoItem,
)
from backend.services.bcu_crud_service import BcuCrudService


@pytest.fixture
def crud_service(db_session: AsyncSession):
    return BcuCrudService(db_session)


@pytest.fixture
async def cabecalho(db_session: AsyncSession):
    cab = BcuCabecalho(id=uuid.uuid4(), nome_arquivo="test.xlsx", is_ativo=False)
    db_session.add(cab)
    await db_session.commit()
    return cab


@pytest.mark.asyncio
async def test_criar_mao_obra(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("mo", cabecalho.id, {"descricao_funcao": "Soldador"}, seed_user)
    await db_session.commit()
    assert item.descricao_funcao == "Soldador"
    assert item.codigo_origem.startswith("BCU-MO-")


@pytest.mark.asyncio
async def test_criar_equipamento(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("equipamentos", cabecalho.id, {"equipamento": "Escavadeira"}, seed_user)
    await db_session.commit()
    assert item.equipamento == "Escavadeira"
    assert item.codigo_origem.startswith("BCU-EQP-")


@pytest.mark.asyncio
async def test_criar_encargo(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("encargos", cabecalho.id, {
        "tipo_encargo": "HORISTA",
        "discriminacao_encargo": "INSS",
    }, seed_user)
    await db_session.commit()
    assert item.discriminacao_encargo == "INSS"


@pytest.mark.asyncio
async def test_criar_epi(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("epi", cabecalho.id, {"epi": "Luva"}, seed_user)
    await db_session.commit()
    assert item.epi == "Luva"
    assert item.codigo_origem.startswith("BCU-EPI-")


@pytest.mark.asyncio
async def test_criar_ferramenta(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("ferramentas", cabecalho.id, {"descricao": "Alicate"}, seed_user)
    await db_session.commit()
    assert item.descricao == "Alicate"
    assert item.codigo_origem.startswith("BCU-FER-")


@pytest.mark.asyncio
async def test_criar_mobilizacao(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("mobilizacao", cabecalho.id, {"descricao": "Exame admissional"}, seed_user)
    await db_session.commit()
    assert item.descricao == "Exame admissional"


@pytest.mark.asyncio
async def test_atualizar_mao_obra(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("mo", cabecalho.id, {"descricao_funcao": "Soldador"}, seed_user)
    await db_session.commit()
    updated = await crud_service.atualizar("mo", cabecalho.id, item.id, {"descricao_funcao": "Soldador Avançado"})
    await db_session.commit()
    assert updated.descricao_funcao == "Soldador Avançado"


@pytest.mark.asyncio
async def test_deletar_mao_obra(crud_service: BcuCrudService, cabecalho, db_session: AsyncSession, seed_user):
    item = await crud_service.criar("mo", cabecalho.id, {"descricao_funcao": "Soldador"}, seed_user)
    await db_session.commit()
    await crud_service.deletar("mo", cabecalho.id, item.id)
    await db_session.commit()
    result = await db_session.get(BcuMaoObraItem, item.id)
    assert result is None


@pytest.mark.asyncio
async def test_criar_rejects_invalid_tipo(crud_service: BcuCrudService, cabecalho, seed_user):
    with pytest.raises(UnprocessableEntityError):
        await crud_service.criar("invalido", cabecalho.id, {}, seed_user)


@pytest.mark.asyncio
async def test_atualizar_rejects_missing_item(crud_service: BcuCrudService, cabecalho):
    with pytest.raises(NotFoundError):
        await crud_service.atualizar("mo", cabecalho.id, uuid.uuid4(), {"descricao_funcao": "X"})


@pytest.mark.asyncio
async def test_deletar_rejects_missing_item(crud_service: BcuCrudService, cabecalho):
    with pytest.raises(NotFoundError):
        await crud_service.deletar("mo", cabecalho.id, uuid.uuid4())


@pytest.mark.asyncio
async def test_criar_rejects_missing_cabecalho(crud_service: BcuCrudService, seed_user):
    with pytest.raises(NotFoundError):
        await crud_service.criar("mo", uuid.uuid4(), {"descricao_funcao": "X"}, seed_user)
