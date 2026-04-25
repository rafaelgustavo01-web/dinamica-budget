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
