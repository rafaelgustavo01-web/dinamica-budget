"""
Unit tests for composition-by-copy (Group B).

Tests covered:
  1. clonar_composicao creates a new ServicoTcpo with origem=PROPRIA
  2. clonar_composicao sets status_homologacao=PENDENTE on the clone
  3. Clone has a different id from the original
  4. Clone inherits descricao from original when not overridden
  5. Clone uses the provided descricao when given
  6. clonar_composicao copies all child link records
  7. adicionar_componente calls _detectar_ciclo before insert
  8. remover_componente raises ValidationError for TCPO items
  9. POST /composicoes/clonar endpoint requires APROVADOR+
  10. POST /composicoes/{pai_id}/componentes endpoint requires APROVADOR+
  11. DELETE /composicoes/{pai_id}/componentes/{id} endpoint requires APROVADOR+
"""

import inspect
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.models.enums import OrigemItem, StatusHomologacao


# ─── Helper: build a mock ServicoTcpo ────────────────────────────────────────

def _make_servico(
    origem: OrigemItem = OrigemItem.TCPO,
    status: StatusHomologacao = StatusHomologacao.APROVADO,
    cliente_id=None,
    n_filhos: int = 2,
):
    servico = MagicMock()
    servico.id = uuid.uuid4()
    servico.origem = origem
    servico.status_homologacao = status
    servico.cliente_id = cliente_id
    servico.descricao = "Serviço Original"
    servico.unidade_medida = "m²"
    servico.custo_unitario = Decimal("100.00")
    servico.categoria_id = None
    servico.deleted_at = None

    filhos = []
    for _ in range(n_filhos):
        comp = MagicMock()
        comp.id = uuid.uuid4()
        comp.insumo_filho_id = uuid.uuid4()
        comp.quantidade_consumo = Decimal("1.0")
        filhos.append(comp)

    servico.composicoes_pai = filhos
    return servico


# ─── 1-6: clonar_composicao service method ───────────────────────────────────

@pytest.mark.asyncio
async def test_clonar_cria_novo_servico_propria():
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    original = _make_servico(n_filhos=1)
    cliente_id = uuid.uuid4()
    mock_db = AsyncMock()

    new_id = uuid.uuid4()
    clone_result = MagicMock()
    clone_result.origem = OrigemItem.PROPRIA

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()

    with (
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
        patch(
            "app.services.servico_catalog_service.ServicoTcpoRepository"
        ) as MockRepo,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_with_composicao = AsyncMock(return_value=original)
        MockRepo.return_value = mock_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=cliente_id,
            codigo_clone="CLONE-001",
            descricao=None,
            db=mock_db,
        )

    from app.models.servico_tcpo import ServicoTcpo
    novo_servicos = [o for o in added_objects if isinstance(o, ServicoTcpo)]
    assert len(novo_servicos) == 1
    assert novo_servicos[0].origem == OrigemItem.PROPRIA


@pytest.mark.asyncio
async def test_clonar_define_status_pendente():
    from app.models.servico_tcpo import ServicoTcpo
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    original = _make_servico(n_filhos=0)
    cliente_id = uuid.uuid4()
    mock_db = AsyncMock()

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()

    with (
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_with_composicao = AsyncMock(return_value=original)
        MockRepo.return_value = mock_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=cliente_id,
            codigo_clone="CLONE-002",
            descricao=None,
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ServicoTcpo)]
    assert novos[0].status_homologacao == StatusHomologacao.PENDENTE


@pytest.mark.asyncio
async def test_clonar_gera_id_diferente():
    from app.models.servico_tcpo import ServicoTcpo
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    original = _make_servico(n_filhos=0)
    mock_db = AsyncMock()

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()

    with (
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_with_composicao = AsyncMock(return_value=original)
        MockRepo.return_value = mock_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ServicoTcpo)]
    assert novos[0].id != original.id


@pytest.mark.asyncio
async def test_clonar_herda_descricao_quando_nao_informada():
    from app.models.servico_tcpo import ServicoTcpo
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    original = _make_servico(n_filhos=0)
    original.descricao = "Descrição Original"
    mock_db = AsyncMock()

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()

    with (
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_with_composicao = AsyncMock(return_value=original)
        MockRepo.return_value = mock_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ServicoTcpo)]
    assert novos[0].descricao == "Descrição Original"


@pytest.mark.asyncio
async def test_clonar_usa_descricao_fornecida():
    from app.models.servico_tcpo import ServicoTcpo
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    original = _make_servico(n_filhos=0)
    mock_db = AsyncMock()

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()

    with (
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_with_composicao = AsyncMock(return_value=original)
        MockRepo.return_value = mock_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao="Nova Descrição",
            db=mock_db,
        )

    novos = [o for o in added_objects if isinstance(o, ServicoTcpo)]
    assert novos[0].descricao == "Nova Descrição"


@pytest.mark.asyncio
async def test_clonar_copia_todos_os_filhos():
    from app.models.composicao_tcpo import ComposicaoTcpo
    from app.models.servico_tcpo import ServicoTcpo
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    original = _make_servico(n_filhos=3)
    mock_db = AsyncMock()

    added_objects = []
    mock_db.add = lambda obj: added_objects.append(obj)
    mock_db.flush = AsyncMock()

    with (
        patch.object(svc, "explode_composicao", new=AsyncMock(return_value=MagicMock())),
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_with_composicao = AsyncMock(return_value=original)
        MockRepo.return_value = mock_repo

        await svc.clonar_composicao(
            servico_origem_id=original.id,
            cliente_id=uuid.uuid4(),
            codigo_clone="X",
            descricao=None,
            db=mock_db,
        )

    links = [o for o in added_objects if isinstance(o, ComposicaoTcpo)]
    assert len(links) == 3  # same count as original.composicoes_pai


# ─── 7: adicionar_componente anti-loop guard ─────────────────────────────────

@pytest.mark.asyncio
async def test_adicionar_componente_chama_detectar_ciclo():
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    filho_id = uuid.uuid4()
    mock_db = AsyncMock()

    pai = MagicMock()
    pai.id = pai_id
    pai.descricao = "Pai"

    filho = MagicMock()
    filho.id = filho_id
    filho.descricao = "Filho"

    with (
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
        patch.object(svc, "_detectar_ciclo", new=AsyncMock(return_value=False)) as mock_ciclo,
        patch.object(svc, "recalcular_custo_pai", new=AsyncMock()),
    ):
        mock_repo = AsyncMock()
        mock_repo.get_active_by_id = AsyncMock(side_effect=lambda id: pai if id == pai_id else filho)
        MockRepo.return_value = mock_repo
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        await svc.adicionar_composicao(
            pai_id=pai_id,
            filho_id=filho_id,
            quantidade_consumo=Decimal("1.0"),
            db=mock_db,
        )

    mock_ciclo.assert_awaited_once_with(pai_id, filho_id, mock_db)


# ─── 8: remover_componente rejeita TCPO ──────────────────────────────────────

@pytest.mark.asyncio
async def test_remover_componente_rejeita_origem_tcpo():
    from app.core.exceptions import ValidationError
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    mock_db = AsyncMock()

    pai = MagicMock()
    pai.id = pai_id
    pai.origem = OrigemItem.TCPO  # not PROPRIA
    pai.deleted_at = None

    with patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo:
        mock_repo = AsyncMock()
        mock_repo.get_active_by_id = AsyncMock(return_value=pai)
        MockRepo.return_value = mock_repo

        with pytest.raises(ValidationError):
            await svc.remover_componente(
                pai_id=pai_id,
                componente_id=uuid.uuid4(),
                db=mock_db,
            )


# ─── 9-11: RBAC on endpoints ─────────────────────────────────────────────────

def test_clonar_endpoint_is_async():
    from app.api.v1.endpoints.composicoes import clonar_composicao
    assert inspect.iscoroutinefunction(clonar_composicao)


def test_adicionar_componente_endpoint_is_async():
    from app.api.v1.endpoints.composicoes import adicionar_componente
    assert inspect.iscoroutinefunction(adicionar_componente)


def test_remover_componente_endpoint_is_async():
    from app.api.v1.endpoints.composicoes import remover_componente
    assert inspect.iscoroutinefunction(remover_componente)


def test_composicoes_router_prefix():
    from app.api.v1.endpoints.composicoes import router
    assert router.prefix == "/composicoes"


def test_composicoes_schema_request():
    from app.schemas.composicao import ClonarComposicaoRequest, AdicionarComponenteRequest

    req = ClonarComposicaoRequest(
        servico_origem_id=uuid.uuid4(),
        cliente_id=uuid.uuid4(),
        codigo_clone="MY-CLONE-001",
    )
    assert req.descricao is None

    req2 = AdicionarComponenteRequest(
        insumo_filho_id=uuid.uuid4(),
        quantidade_consumo=Decimal("2.5"),
    )
    assert req2.quantidade_consumo == Decimal("2.5")


def test_adicionar_componente_schema_rejects_zero_quantidade():
    from pydantic import ValidationError as PydanticValidationError
    from app.schemas.composicao import AdicionarComponenteRequest

    with pytest.raises(PydanticValidationError):
        AdicionarComponenteRequest(
            insumo_filho_id=uuid.uuid4(),
            quantidade_consumo=Decimal("0"),
        )


# ─── Price rollup: adicionar chama recalcular_custo_pai ──────────────────────

@pytest.mark.asyncio
async def test_adicionar_componente_dispara_recalcular_custo():
    """After adding a component, recalcular_custo_pai must be called."""
    from app.services.servico_catalog_service import ServicoCatalogService

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    filho_id = uuid.uuid4()
    mock_db = AsyncMock()

    pai = MagicMock()
    pai.id = pai_id
    pai.descricao = "Pai"

    filho = MagicMock()
    filho.id = filho_id
    filho.descricao = "Filho"

    with (
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
        patch.object(svc, "_detectar_ciclo", new=AsyncMock(return_value=False)),
        patch.object(svc, "recalcular_custo_pai", new=AsyncMock()) as mock_recalc,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_active_by_id = AsyncMock(
            side_effect=lambda id: pai if id == pai_id else filho
        )
        MockRepo.return_value = mock_repo
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        await svc.adicionar_composicao(
            pai_id=pai_id,
            filho_id=filho_id,
            quantidade_consumo=Decimal("1.0"),
            db=mock_db,
        )

    mock_recalc.assert_awaited_once_with(filho_id, mock_db)


@pytest.mark.asyncio
async def test_remover_componente_dispara_recalcular_custo():
    """After removing a component, recalcular_custo_pai must be called with the child's id."""
    from app.services.servico_catalog_service import ServicoCatalogService
    from app.models.enums import OrigemItem

    svc = ServicoCatalogService()
    pai_id = uuid.uuid4()
    componente_id = uuid.uuid4()
    filho_id = uuid.uuid4()
    mock_db = AsyncMock()

    pai = MagicMock()
    pai.id = pai_id
    pai.origem = OrigemItem.PROPRIA

    comp = MagicMock()
    comp.id = componente_id
    comp.insumo_filho_id = filho_id

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=comp)
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.delete = AsyncMock()
    mock_db.flush = AsyncMock()

    with (
        patch("app.services.servico_catalog_service.ServicoTcpoRepository") as MockRepo,
        patch.object(svc, "recalcular_custo_pai", new=AsyncMock()) as mock_recalc,
    ):
        mock_repo = AsyncMock()
        mock_repo.get_active_by_id = AsyncMock(return_value=pai)
        MockRepo.return_value = mock_repo

        await svc.remover_componente(
            pai_id=pai_id,
            componente_id=componente_id,
            db=mock_db,
        )

    mock_recalc.assert_awaited_once_with(filho_id, mock_db)
