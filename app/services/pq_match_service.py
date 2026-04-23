import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.enums import StatusMatch, TipoServicoMatch
from app.repositories.pq_item_repository import PqItemRepository
from app.repositories.proposta_repository import PropostaRepository
from app.schemas.busca import BuscaServicoRequest
from app.services.busca_service import BuscaService, busca_service


class PqMatchService:
    def __init__(
        self,
        db: AsyncSession,
        proposta_repo: PropostaRepository,
        item_repo: PqItemRepository,
        busca_svc: BuscaService = busca_service,
    ) -> None:
        self.db = db
        self.proposta_repo = proposta_repo
        self.item_repo = item_repo
        self.busca_svc = busca_svc

    async def executar_match_para_proposta(self, proposta_id: uuid.UUID, usuario_id: uuid.UUID) -> dict[str, int]:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        itens = await self.item_repo.list_by_proposta(
            proposta_id=proposta_id,
            status_match=StatusMatch.PENDENTE,
            limit=1000,
        )
        resultados = {"processados": 0, "sugeridos": 0, "sem_match": 0}

        for item in itens:
            await self.item_repo.update_status(item, StatusMatch.BUSCANDO)
            resposta = await self.busca_svc.buscar(
                request=BuscaServicoRequest(
                    cliente_id=proposta.cliente_id,
                    texto_busca=item.descricao_original,
                    limite_resultados=5,
                    threshold_score=0.65,
                ),
                usuario_id=usuario_id,
                db=self.db,
            )

            if resposta.resultados:
                top = resposta.resultados[0]
                servico_tipo = (
                    TipoServicoMatch.ITEM_PROPRIO
                    if top.origem_match == "PROPRIA_CLIENTE"
                    else TipoServicoMatch.BASE_TCPO
                )
                await self.item_repo.update_match(
                    pq_item=item,
                    servico_match_id=top.id_tcpo,
                    servico_match_tipo=servico_tipo,
                    confidence=top.score_confianca,
                )
                resultados["sugeridos"] += 1
            else:
                await self.item_repo.update_status(item, StatusMatch.SEM_MATCH)
                resultados["sem_match"] += 1

            resultados["processados"] += 1

        return resultados
