from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_access
from app.core.exceptions import NotFoundError
from app.repositories.pq_importacao_repository import PqImportacaoRepository
from app.repositories.pq_item_repository import PqItemRepository
from app.repositories.proposta_repository import PropostaRepository
from app.schemas.proposta import PqImportacaoResponse, PqMatchResponse
from app.services.pq_import_service import PqImportService
from app.services.pq_match_service import PqMatchService

router = APIRouter(prefix="/propostas/{proposta_id}/pq", tags=["pq-importacao"])


async def _get_proposta_or_404(db: AsyncSession, proposta_id: UUID):
    proposta = await PropostaRepository(db).get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    return proposta


@router.post("/importar", response_model=PqImportacaoResponse, status_code=status.HTTP_201_CREATED)
async def upload_planilha(
    proposta_id: UUID,
    arquivo: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqImportacaoResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = PqImportService(
        proposta_repo=PropostaRepository(db),
        importacao_repo=PqImportacaoRepository(db),
        item_repo=PqItemRepository(db),
    )
    importacao = await svc.importar_planilha(proposta_id, arquivo)
    return PqImportacaoResponse(
        importacao_id=importacao.id,
        status=importacao.status.value,
        linhas_total=importacao.linhas_total,
        linhas_importadas=importacao.linhas_importadas,
        linhas_com_erro=importacao.linhas_com_erro,
    )


@router.post("/match", response_model=PqMatchResponse)
async def executar_match(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqMatchResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = PqMatchService(
        db=db,
        proposta_repo=PropostaRepository(db),
        item_repo=PqItemRepository(db),
    )
    resultados = await svc.executar_match_para_proposta(proposta_id, current_user.id)
    return PqMatchResponse(**resultados)
