import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.bcu import BcuTableType, DeParaTcpoBcu
from backend.services.bcu_de_para_service import BcuDeParaService, TIPO_COERENCIA


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    svc = BcuDeParaService(mock_db)
    svc.repo.get_by_id = AsyncMock()
    svc.repo.get_by_base_tcpo_id = AsyncMock()
    svc.repo.create = AsyncMock()
    svc.repo.delete = AsyncMock()
    return svc


@pytest.mark.asyncio
async def test_criar_mapeamento_valido(service, mock_db):
    from backend.models.base_tcpo import BaseTcpo
    bt = BaseTcpo(id=uuid.uuid4(), codigo_origem="MO-001", descricao="Eletricista", unidade_medida="H", custo_base=10.0, tipo_recurso="MO")
    mock_db.get.return_value = bt

    # Mock bcu item exists
    mock_db.execute.return_value.scalar_one_or_none = MagicMock(return_value=uuid.uuid4())

    service.repo.get_by_base_tcpo_id.return_value = None
    service.repo.create.return_value = DeParaTcpoBcu(id=uuid.uuid4(), base_tcpo_id=bt.id, bcu_table_type=BcuTableType.MO, bcu_item_id=uuid.uuid4())

    result = await service.criar(bt.id, BcuTableType.MO, uuid.uuid4(), uuid.uuid4())
    assert result is not None


@pytest.mark.asyncio
async def test_criar_tipo_incoerente(service, mock_db):
    from backend.models.base_tcpo import BaseTcpo
    bt = BaseTcpo(id=uuid.uuid4(), codigo_origem="MO-001", descricao="Eletricista", unidade_medida="H", custo_base=10.0, tipo_recurso="MO")
    mock_db.get.return_value = bt

    from backend.core.exceptions import UnprocessableEntityError
    with pytest.raises(UnprocessableEntityError):
        await service.criar(bt.id, BcuTableType.EQP, uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_lookup_bcu_para_base_tcpo(service):
    service.repo.get_by_base_tcpo_id.return_value = DeParaTcpoBcu(
        id=uuid.uuid4(), base_tcpo_id=uuid.uuid4(), bcu_table_type=BcuTableType.MO, bcu_item_id=uuid.uuid4()
    )
    result = await service.lookup_bcu_para_base_tcpo(uuid.uuid4())
    assert result is not None
    assert result[0] == BcuTableType.MO
