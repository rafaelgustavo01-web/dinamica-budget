from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.models.enums import StatusMatch, TipoServicoMatch
from backend.models.proposta import PqItem
from backend.schemas.busca import BuscaMetadados, BuscaServicoResponse, ResultadoBusca
from backend.services.pq_match_service import PqMatchService


@pytest.mark.asyncio
async def test_executar_match_para_proposta_atualiza_sugestao_e_sem_match():
    proposta_id = uuid4()
    cliente_id = uuid4()
    usuario_id = uuid4()

    proposta = MagicMock()
    proposta.id = proposta_id
    proposta.cliente_id = cliente_id

    item_match = PqItem(
        id=uuid4(),
        proposta_id=proposta_id,
        descricao_original="Escavacao manual",
        match_status=StatusMatch.PENDENTE,
    )
    item_sem_match = PqItem(
        id=uuid4(),
        proposta_id=proposta_id,
        descricao_original="Servico inexistente",
        match_status=StatusMatch.PENDENTE,
    )

    proposta_repo = AsyncMock()
    proposta_repo.get_by_id.return_value = proposta
    item_repo = AsyncMock()
    item_repo.list_by_proposta.return_value = [item_match, item_sem_match]

    busca_svc = AsyncMock()
    busca_svc.buscar.side_effect = [
        BuscaServicoResponse(
            texto_buscado="Escavacao manual",
            resultados=[
                ResultadoBusca(
                    id_tcpo=uuid4(),
                    codigo_origem="001",
                    descricao="Escavacao",
                    unidade="m2",
                    custo_unitario=10.0,
                    score=0.91,
                    score_confianca=0.91,
                    origem_match="PROPRIA_CLIENTE",
                    status_homologacao="APROVADO",
                )
            ],
            metadados=BuscaMetadados(tempo_processamento_ms=10, id_historico_busca=uuid4()),
        ),
        BuscaServicoResponse(
            texto_buscado="Servico inexistente",
            resultados=[],
            metadados=BuscaMetadados(tempo_processamento_ms=12, id_historico_busca=uuid4()),
        ),
    ]

    svc = PqMatchService(
        db=AsyncMock(),
        proposta_repo=proposta_repo,
        item_repo=item_repo,
        busca_svc=busca_svc,
    )

    resultado = await svc.executar_match_para_proposta(proposta_id, usuario_id)

    assert resultado == {"processados": 2, "sugeridos": 1, "sem_match": 1}
    item_repo.update_match.assert_awaited_once()
    assert item_repo.update_match.await_args.kwargs["servico_match_tipo"] == TipoServicoMatch.ITEM_PROPRIO
    assert item_repo.update_status.await_count == 3

