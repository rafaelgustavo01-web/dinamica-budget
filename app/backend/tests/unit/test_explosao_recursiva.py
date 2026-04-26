import pytest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.proposta import PropostaItemComposicao
from backend.models.enums import TipoRecurso


def _make_pic(nivel=0, e_composicao=False, pai_id=None) -> PropostaItemComposicao:
    c = PropostaItemComposicao()
    c.id = uuid.uuid4()
    c.proposta_item_id = uuid.uuid4()
    c.descricao_insumo = "Insumo Teste"
    c.unidade_medida = "UN"
    c.quantidade_consumo = Decimal("1.0")
    c.tipo_recurso = TipoRecurso.INSUMO
    c.nivel = nivel
    c.e_composicao = e_composicao
    c.composicao_explodida = False
    c.pai_composicao_id = pai_id
    c.insumo_base_id = uuid.uuid4()
    c.insumo_proprio_id = None
    c.fonte_custo = "base_tcpo"
    c.sub_composicoes = []
    return c


def test_pic_campos_padrao():
    c = _make_pic()
    assert c.nivel == 0
    assert not c.e_composicao
    assert not c.composicao_explodida
    assert c.pai_composicao_id is None


def test_pic_nivel_incrementado():
    pai = _make_pic(nivel=0, e_composicao=True)
    filho = _make_pic(nivel=1, pai_id=pai.id)
    assert filho.nivel == 1
    assert filho.pai_composicao_id == pai.id


def test_guard_nivel_permitido_aceita_ate_5():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    svc = CpuExplosaoService(AsyncMock())
    for n in range(6):
        svc._assert_nivel_permitido(n)  # nao deve levantar


def test_guard_nivel_rejeita_acima_de_5():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    svc = CpuExplosaoService(AsyncMock())
    with pytest.raises(ValueError, match="Profundidade maxima"):
        svc._assert_nivel_permitido(6)


@pytest.mark.asyncio
async def test_explodir_sub_rejeita_ja_explodida():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository

    pic = _make_pic(e_composicao=True)
    pic.composicao_explodida = True

    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(PropostaItemComposicaoRepository, "get_by_id", return_value=pic):
        with pytest.raises(ValueError, match="ja foi explodida"):
            await svc.explodir_sub_composicao(uuid.uuid4(), pic.id)


@pytest.mark.asyncio
async def test_explodir_sub_rejeita_sem_composicao():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository

    pic = _make_pic(e_composicao=False)
    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(PropostaItemComposicaoRepository, "get_by_id", return_value=pic):
        with pytest.raises(ValueError, match="nao possui composicao"):
            await svc.explodir_sub_composicao(uuid.uuid4(), pic.id)


@pytest.mark.asyncio
async def test_explodir_proposta_item_cria_apenas_filhos_diretos():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.models.base_tcpo import BaseTcpo
    from backend.models.proposta import PropostaItem

    proposta_item = MagicMock(spec=PropostaItem)
    proposta_item.id = uuid.uuid4()
    proposta_item.servico_id = uuid.uuid4()
    proposta_item.quantidade = Decimal("2")
    proposta_item.unidade_medida = "m2"

    filho_id = uuid.uuid4()
    snapshot = MagicMock(spec=BaseTcpo)
    snapshot.id = filho_id
    snapshot.descricao = "Cimento"
    snapshot.unidade_medida = "kg"
    snapshot.custo_base = Decimal("50")
    snapshot.tipo_recurso = TipoRecurso.INSUMO

    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(svc, "_listar_filhos_diretos", new=AsyncMock(return_value=[{
        "insumo_id": filho_id,
        "quantidade_consumo": Decimal("10"),
        "unidade_medida": "kg",
        "is_base": True,
    }])):
        with patch.object(svc, "_resolve_snapshot", new=AsyncMock(return_value=snapshot)):
            with patch.object(svc, "_verificar_e_marcar_sub_composicao", new=AsyncMock()):
                result = await svc.explodir_proposta_item(proposta_item)

    assert len(result) == 1
    assert result[0].nivel == 0
    assert result[0].quantidade_consumo == Decimal("20")  # 10 * 2
    assert result[0].tipo_recurso == TipoRecurso.INSUMO
    assert result[0].custo_unitario_insumo == Decimal("50")


@pytest.mark.asyncio
async def test_explodir_sub_composicao_cria_netos_sem_duplicar():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.models.base_tcpo import BaseTcpo
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository

    pai = _make_pic(nivel=0, e_composicao=True)
    pai.quantidade_consumo = Decimal("2")

    neto_id = uuid.uuid4()
    snapshot = MagicMock(spec=BaseTcpo)
    snapshot.id = neto_id
    snapshot.descricao = "Areia"
    snapshot.unidade_medida = "m3"
    snapshot.custo_base = Decimal("30")
    snapshot.tipo_recurso = TipoRecurso.INSUMO

    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(PropostaItemComposicaoRepository, "get_by_id", return_value=pai):
        with patch.object(svc, "_listar_filhos_diretos", new=AsyncMock(return_value=[{
            "insumo_id": neto_id,
            "quantidade_consumo": Decimal("5"),
            "unidade_medida": "m3",
            "is_base": True,
        }])):
            with patch.object(svc, "_resolve_snapshot", new=AsyncMock(return_value=snapshot)):
                with patch.object(svc, "_verificar_e_marcar_sub_composicao", new=AsyncMock()):
                    result = await svc.explodir_sub_composicao(uuid.uuid4(), pai.id)

    assert len(result) == 1
    assert result[0].nivel == 1
    assert result[0].pai_composicao_id == pai.id
    assert result[0].quantidade_consumo == Decimal("10")  # 5 * 2
    assert result[0].tipo_recurso == TipoRecurso.INSUMO
    assert result[0].custo_unitario_insumo == Decimal("30")


@pytest.mark.asyncio
async def test_explodir_sub_composicao_suporta_item_proprio():
    from backend.services.cpu_explosao_service import CpuExplosaoService
    from backend.models.itens_proprios import ItemProprio
    from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository

    pai = _make_pic(nivel=0, e_composicao=True)
    pai.insumo_base_id = None
    pai.insumo_proprio_id = uuid.uuid4()

    filho_id = uuid.uuid4()
    snapshot = MagicMock(spec=ItemProprio)
    snapshot.id = filho_id
    snapshot.descricao = "Item Custom"
    snapshot.unidade_medida = "UN"
    snapshot.custo_unitario = Decimal("100")
    snapshot.tipo_recurso = TipoRecurso.MO

    mock_db = AsyncMock()
    svc = CpuExplosaoService(mock_db)

    with patch.object(PropostaItemComposicaoRepository, "get_by_id", return_value=pai):
        with patch.object(svc, "_listar_filhos_diretos", new=AsyncMock(return_value=[{
            "insumo_id": filho_id,
            "quantidade_consumo": Decimal("1"),
            "unidade_medida": "UN",
            "is_base": False,
        }])):
            with patch.object(svc, "_resolve_snapshot", new=AsyncMock(return_value=snapshot)):
                with patch.object(svc, "_verificar_e_marcar_sub_composicao", new=AsyncMock()):
                    result = await svc.explodir_sub_composicao(uuid.uuid4(), pai.id)

    assert len(result) == 1
    assert result[0].nivel == 1
    assert result[0].insumo_proprio_id == filho_id
    assert result[0].insumo_base_id is None
    assert result[0].tipo_recurso == TipoRecurso.MO
    assert result[0].custo_unitario_insumo == Decimal("100")
