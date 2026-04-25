"""
Unit tests for composition-by-copy (new dual-schema architecture).

Tests covered:
  1.  clonar_composicao creates a new ItemProprio with status PENDENTE
  2.  Clone gets a different id from the original
  3.  Clone inherits descricao from original when not overridden
  4.  Clone uses the provided descricao when given
  5.  clonar_composicao creates a VersaoComposicao linked to the new item
  6.  clonar_composicao copies child ComposicaoCliente link records
  7.  adicionar_componente calls _detectar_ciclo before insert
  8.  adicionar_componente triggers recalcular_custo_pai
  9.  remover_componente triggers recalcular_custo_pai
  10. POST /composicoes/clonar endpoint is async
  11. POST /composicoes/{pai_id}/componentes endpoint is async
  12. DELETE /composicoes/{pai_id}/componentes/{id} endpoint is async
  13. Composicoes router prefix is /composicoes
  14. ClonarComposicaoRequest schema structure
  15. AdicionarComponenteRequest rejects zero quantidade
"""

import inspect
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models.enums import StatusHomologacao


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_item_proprio(n_versoes: int = 0, cliente_id=None):
    item = MagicMock()
    item.id = uuid.uuid4()
    item.cliente_id = cliente_id or uuid.uuid4()
    item.descricao = "Serviço Original"
    item.unidade_medida = "m²"
    item.custo_unitario = Decimal("100.00")
    item.categoria_id = None
    item.deleted_at = None
    return item


def _make_versao_ativa(item_proprio_id=None, n_filhos: int = 2):
    versao = MagicMock()
    versao.id = uuid.uuid4()
    versao.item_proprio_id = item_proprio_id or uuid.uuid4()
    versao.is_ativa = True
    versao.numero_versao = 1

    filhos = []
    for _ in range(n_filhos):
        comp = MagicMock()
        comp.id = uuid.uuid4()
        comp.insumo_base_id = uuid.uuid4()
        comp.insumo_proprio_id = None
        comp.quantidade_consumo = Decimal("1.0")
        comp.unidade_medida = "un"
        filhos.append(comp)

    versao.itens = filhos
    return versao


def _make_base_tcpo(n_filhos: int = 0):
    item = MagicMock()
    item.id = uuid.uuid4()
    item.descricao = "Serviço Original"
    item.unidade_medida = "m²"
    item.custo_base = Decimal("100.00")
    item.categoria_id = None

    filhos = []
    for _ in range(n_filhos):
        comp = MagicMock()
        comp.insumo_filho_id = uuid.uuid4()
        comp.quantidade_consumo = Decimal("1.0")
        comp.unidade_medida = "un"
        filhos.append(comp)
    item.composicoes_pai = filhos
    return item


# ─── 1: clonar cria ItemProprio com status PENDENTE ──────────────────────────

@pytest.mark.asyncio
async def test_clonar_cria_item_proprio_pendente():
    from backend.services.servico_catalog_service import ServicoCatalogService
    from backend.models.itens_proprios import ItemProprio

    svc = ServicoCatalogService()
    original = _make_base_tcpo()
    cliente_id = uuid.uuid4()
    criado_por_id = uuid.uuid4()
    mock_db = AsyncMock()

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
    ):
        mock_base_repo = AsyncMock()
        mock_base_repo.get_with_composicao_base = AsyncMock(return_value=original)
        MockBaseRepo.return_value = mock_base_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=cliente_id,
            codigo_clone="CLONE-001",
            descricao=None,
            criado_por_id=criado_por_id,
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ItemProprio)]
    assert len(novos) == 1
    assert novos[0].status_homologacao == StatusHomologacao.PENDENTE


# ─── 2: Clone gets different id ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clonar_gera_id_diferente():
    from backend.services.servico_catalog_service import ServicoCatalogService
    from backend.models.itens_proprios import ItemProprio

    svc = ServicoCatalogService()
    original = _make_base_tcpo()
    mock_db = AsyncMock()
    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
    ):
        mock_base_repo = AsyncMock()
        mock_base_repo.get_with_composicao_base = AsyncMock(return_value=original)
        MockBaseRepo.return_value = mock_base_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            criado_por_id=uuid.uuid4(),
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ItemProprio)]
    assert novos[0].id != original.id


# ─── 3: Clone inherits descricao ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clonar_herda_descricao_quando_nao_informada():
    from backend.services.servico_catalog_service import ServicoCatalogService
    from backend.models.itens_proprios import ItemProprio

    svc = ServicoCatalogService()
    original = _make_base_tcpo()
    original.descricao = "Descrição Original"
    mock_db = AsyncMock()
    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
    ):
        mock_base_repo = AsyncMock()
        mock_base_repo.get_with_composicao_base = AsyncMock(return_value=original)
        MockBaseRepo.return_value = mock_base_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            criado_por_id=uuid.uuid4(),
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ItemProprio)]
    assert novos[0].descricao == "Descrição Original"


# ─── 4: Clone uses provided descricao ────────────────────────────────────────

@pytest.mark.asyncio
async def test_clonar_usa_descricao_fornecida():
    from backend.services.servico_catalog_service import ServicoCatalogService
    from backend.models.itens_proprios import ItemProprio

    svc = ServicoCatalogService()
    original = _make_base_tcpo()
    mock_db = AsyncMock()
    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
    ):
        mock_base_repo = AsyncMock()
        mock_base_repo.get_with_composicao_base = AsyncMock(return_value=original)
        MockBaseRepo.return_value = mock_base_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao="Nova Descrição",
            criado_por_id=uuid.uuid4(),
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ItemProprio)]
    assert novos[0].descricao == "Nova Descrição"


# ─── 5: clonar cria VersaoComposicao ligada ao item ──────────────────────────

@pytest.mark.asyncio
async def test_clonar_cria_versao_composicao():
    from backend.services.servico_catalog_service import ServicoCatalogService
    from backend.models.versao_composicao import VersaoComposicao

    svc = ServicoCatalogService()
    original = _make_base_tcpo()
    mock_db = AsyncMock()
    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
    ):
        mock_base_repo = AsyncMock()
        mock_base_repo.get_with_composicao_base = AsyncMock(return_value=original)
        MockBaseRepo.return_value = mock_base_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            criado_por_id=uuid.uuid4(),
            db=mock_db,
        )

    versoes = [o for o in added_objects if isinstance(o, VersaoComposicao)]
    assert len(versoes) == 1


# ─── 6: clonar copia filhos da versão ativa ──────────────────────────────────

@pytest.mark.asyncio
async def test_clonar_copia_todos_os_filhos():
    from backend.services.servico_catalog_service import ServicoCatalogService
    from backend.models.composicao_cliente import ComposicaoCliente

    svc = ServicoCatalogService()
    original = _make_base_tcpo(n_filhos=3)
    mock_db = AsyncMock()
    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()
    mock_db.refresh = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
    ):
        mock_base_repo = AsyncMock()
        mock_base_repo.get_with_composicao_base = AsyncMock(return_value=original)
        MockBaseRepo.return_value = mock_base_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            criado_por_id=uuid.uuid4(),
            db=mock_db,
        )

    links = [o for o in added_objects if isinstance(o, ComposicaoCliente)]
    assert len(links) == 3


# ─── 7: adicionar_componente calls _detectar_ciclo ───────────────────────────

@pytest.mark.asyncio
async def test_adicionar_componente_chama_detectar_ciclo():
    from backend.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    filho_id = uuid.uuid4()
    mock_db = AsyncMock()

    versao_ativa = MagicMock()
    versao_ativa.id = uuid.uuid4()

    with (
        patch("app.services.servico_catalog_service.ItensPropiosRepository") as MockItemRepo,
        patch("app.services.servico_catalog_service.VersaoComposicaoRepository") as MockVersaoRepo,
        patch("app.services.servico_catalog_service.BaseTcpoRepository") as MockBaseRepo,
        patch.object(svc, "_detectar_ciclo", new=AsyncMock(return_value=False)) as mock_ciclo,
        patch.object(svc, "recalcular_custo_pai", new=AsyncMock()),
    ):
        mock_item_repo = AsyncMock()
        mock_item_repo.get_active_by_id = AsyncMock(return_value=MagicMock(id=pai_id))
        MockItemRepo.return_value = mock_item_repo
        mock_versao_repo = AsyncMock()
        mock_versao_repo.get_versao_ativa = AsyncMock(return_value=versao_ativa)
        MockVersaoRepo.return_value = mock_versao_repo
        mock_base_repo = AsyncMock()
        mock_base_repo.get_by_id = AsyncMock(return_value=None)
        MockBaseRepo.return_value = mock_base_repo
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        await svc.adicionar_composicao(
            pai_id=pai_id,
            filho_id=filho_id,
            quantidade_consumo=Decimal("1.0"),
            unidade_medida="m²",
            db=mock_db,
        )

    mock_ciclo.assert_awaited_once_with(pai_id, filho_id, mock_db)


# ─── 8: adicionar triggers recalcular_custo_pai ──────────────────────────────

@pytest.mark.asyncio
async def test_adicionar_componente_dispara_recalcular_custo():
    from backend.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    filho_id = uuid.uuid4()
    mock_db = AsyncMock()
    versao_ativa = MagicMock()
    versao_ativa.id = uuid.uuid4()

    with (
        patch("app.services.servico_catalog_service.ItensPropiosRepository") as MockItemRepo,
        patch("app.services.servico_catalog_service.VersaoComposicaoRepository") as MockVersaoRepo,
        patch.object(svc, "_detectar_ciclo", new=AsyncMock(return_value=False)),
        patch.object(svc, "recalcular_custo_pai", new=AsyncMock()) as mock_recalc,
    ):
        mock_item_repo = AsyncMock()
        mock_item_repo.get_active_by_id = AsyncMock(return_value=MagicMock(id=pai_id))
        MockItemRepo.return_value = mock_item_repo
        mock_versao_repo = AsyncMock()
        mock_versao_repo.get_versao_ativa = AsyncMock(return_value=versao_ativa)
        MockVersaoRepo.return_value = mock_versao_repo
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        await svc.adicionar_composicao(
            pai_id=pai_id,
            filho_id=filho_id,
            quantidade_consumo=Decimal("1.0"),
            unidade_medida="m²",
            db=mock_db,
        )

    mock_recalc.assert_awaited()


# ─── 9: remover_componente triggers recalcular_custo_pai ─────────────────────

@pytest.mark.asyncio
async def test_remover_componente_dispara_recalcular_custo():
    from backend.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    componente_id = uuid.uuid4()
    filho_id = uuid.uuid4()
    mock_db = AsyncMock()

    versao_ativa = MagicMock()
    versao_ativa.id = uuid.uuid4()

    comp = MagicMock()
    comp.id = componente_id
    comp.insumo_proprio_id = filho_id
    comp.insumo_base_id = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=comp)
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.delete = AsyncMock()
    mock_db.flush = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.ItensPropiosRepository") as MockItemRepo,
        patch("app.services.servico_catalog_service.VersaoComposicaoRepository") as MockVersaoRepo,
        patch.object(svc, "recalcular_custo_pai", new=AsyncMock()) as mock_recalc,
    ):
        mock_item_repo = AsyncMock()
        mock_item_repo.get_active_by_id = AsyncMock(return_value=MagicMock(id=pai_id))
        MockItemRepo.return_value = mock_item_repo
        mock_versao_repo = AsyncMock()
        mock_versao_repo.get_versao_ativa = AsyncMock(return_value=versao_ativa)
        MockVersaoRepo.return_value = mock_versao_repo

        await svc.remover_componente(
            pai_id=pai_id,
            componente_id=componente_id,
            db=mock_db,
        )

    mock_recalc.assert_awaited()


# ─── 10-13: RBAC on endpoints ────────────────────────────────────────────────

def test_clonar_endpoint_is_async():
    from backend.api.v1.endpoints.composicoes import clonar_composicao
    assert inspect.iscoroutinefunction(clonar_composicao)


def test_adicionar_componente_endpoint_is_async():
    from backend.api.v1.endpoints.composicoes import adicionar_componente
    assert inspect.iscoroutinefunction(adicionar_componente)


def test_remover_componente_endpoint_is_async():
    from backend.api.v1.endpoints.composicoes import remover_componente
    assert inspect.iscoroutinefunction(remover_componente)


def test_composicoes_router_prefix():
    from backend.api.v1.endpoints.composicoes import router
    assert router.prefix == "/composicoes"


# ─── 14: ClonarComposicaoRequest schema ──────────────────────────────────────

def test_composicoes_schema_request():
    from backend.schemas.composicao import ClonarComposicaoRequest, AdicionarComponenteRequest

    req = ClonarComposicaoRequest(
        servico_origem_id=uuid.uuid4(),
        cliente_id=uuid.uuid4(),
        codigo_clone="MY-CLONE-001",
    )
    assert req.descricao is None

    req2 = AdicionarComponenteRequest(
        insumo_filho_id=uuid.uuid4(),
        quantidade_consumo=Decimal("2.5"),
        unidade_medida="m²",
    )
    assert req2.quantidade_consumo == Decimal("2.5")


# ─── 15: AdicionarComponenteRequest rejects zero quantidade ──────────────────

def test_adicionar_componente_schema_rejects_zero_quantidade():
    from pydantic import ValidationError as PydanticValidationError
    from backend.schemas.composicao import AdicionarComponenteRequest

    with pytest.raises(PydanticValidationError):
        AdicionarComponenteRequest(
            insumo_filho_id=uuid.uuid4(),
            quantidade_consumo=Decimal("0"),
            unidade_medida="m²",
        )

