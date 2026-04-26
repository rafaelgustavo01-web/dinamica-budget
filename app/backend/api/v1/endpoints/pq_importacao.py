from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_proposta_role
from backend.models.enums import PropostaPapel
from backend.core.exceptions import NotFoundError
from backend.models.enums import StatusMatch
from backend.repositories.pq_importacao_repository import PqImportacaoRepository
from backend.repositories.pq_item_repository import PqItemRepository
from backend.repositories.pq_layout_repository import PqLayoutRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.schemas.proposta import (
    PqImportacaoResponse,
    PqItemResponse,
    PqMatchConfirmarRequest,
    PqMatchResponse,
)
from backend.services.pq_import_service import PqImportService
from backend.services.pq_match_service import PqMatchService

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
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    svc = PqImportService(
        proposta_repo=PropostaRepository(db),
        importacao_repo=PqImportacaoRepository(db),
        item_repo=PqItemRepository(db),
        pq_layout_repo=PqLayoutRepository(db),
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
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    svc = PqMatchService(
        db=db,
        proposta_repo=PropostaRepository(db),
        item_repo=PqItemRepository(db),
    )
    resultados = await svc.executar_match_para_proposta(proposta_id, current_user.id)
    return PqMatchResponse(**resultados)


@router.get("/itens", response_model=list[PqItemResponse])
async def listar_pq_itens(
    proposta_id: UUID,
    status_match: StatusMatch | None = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PqItemResponse]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, None, current_user, db)
    items = await PqItemRepository(db).list_by_proposta(proposta_id, status_match=status_match)
    return [PqItemResponse.model_validate(item) for item in items]


@router.patch("/itens/{item_id}/match", response_model=PqItemResponse)
async def atualizar_match_item(
    proposta_id: UUID,
    item_id: UUID,
    body: PqMatchConfirmarRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqItemResponse:
    from backend.core.exceptions import ValidationError as AppValidationError

    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    repo = PqItemRepository(db)
    item = await repo.get_by_id(item_id)
    if item is None or item.proposta_id != proposta_id:
        raise NotFoundError("PqItem", str(item_id))

    if body.acao == "rejeitar":
        await repo.update_status(item, StatusMatch.SEM_MATCH)
    elif body.acao == "confirmar":
        await repo.update_status(item, StatusMatch.CONFIRMADO)
    elif body.acao == "substituir":
        if body.servico_match_id is None or body.servico_match_tipo is None:
            raise AppValidationError("servico_match_id e servico_match_tipo sao obrigatorios para acao=substituir")
        await repo.update_match(
            pq_item=item,
            servico_match_id=body.servico_match_id,
            servico_match_tipo=body.servico_match_tipo,
            confidence=1.0,
        )
        await repo.update_status(item, StatusMatch.MANUAL)

    if body.quantidade is not None:
        item.quantidade_original = body.quantidade
        await db.flush()

    await db.commit()
    await db.refresh(item)
    return PqItemResponse.model_validate(item)

