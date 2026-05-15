import asyncio
import inspect
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session_factory
from backend.core.dependencies import get_current_active_user, get_db, require_proposta_role
from backend.models.enums import PropostaPapel
from backend.core.exceptions import NotFoundError
from backend.models.enums import StatusMatch, TipoServicoMatch
from backend.models.proposta import PqItem
from backend.core.logging import get_logger
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.pq_importacao_repository import PqImportacaoRepository
from backend.repositories.pq_item_repository import PqItemRepository
from backend.repositories.pq_layout_repository import PqLayoutRepository
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.schemas.proposta import (
    PqImportacaoResponse,
    PqItemResponse,
    PqItemManualCreate,
    PqMatchConfirmarRequest,
    PqMatchResponse,
    PqMatchStatusResponse,
)
from backend.schemas.pq_layout import PqPreviewResponse
from backend.services.pq_import_service import PqImportService
from backend.services.pq_match_service import PqMatchService
from backend.services.cpu_geracao_service import CpuGeracaoService

logger = get_logger(__name__)
router = APIRouter(prefix="/propostas/{proposta_id}/pq", tags=["pq-importacao"])

# ---------------------------------------------------------------------------
# In-memory registry for background match tasks (keyed by str(proposta_id))
# ---------------------------------------------------------------------------
_match_tasks: dict[str, dict] = {}


async def _run_match_background(proposta_id: UUID, user_id: UUID) -> None:
    """Execute match in background using its own DB session."""
    key = str(proposta_id)
    _match_tasks[key]["status"] = "running"
    try:
        async with async_session_factory() as db:
            try:
                svc = PqMatchService(
                    db=db,
                    proposta_repo=PropostaRepository(db),
                    item_repo=PqItemRepository(db),
                )
                resultados = await svc.executar_match_para_proposta(proposta_id, user_id)
                await db.commit()
                _match_tasks[key].update(
                    status="completed",
                    processados=resultados["processados"],
                    sugeridos=resultados["sugeridos"],
                    sem_match=resultados["sem_match"],
                )
                logger.info(
                    "pq_match_concluido",
                    proposta_id=str(proposta_id),
                    **resultados,
                )
            except Exception as exc:
                await db.rollback()
                _match_tasks[key].update(status="failed", error=str(exc))
                logger.exception(
                    "pq_match_erro_background",
                    proposta_id=str(proposta_id),
                    error=str(exc),
                )
    except Exception as exc:
        _match_tasks[key].update(status="failed", error=str(exc))


async def _get_proposta_or_404(db: AsyncSession, proposta_id: UUID):
    proposta = await PropostaRepository(db).get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    return proposta


async def _attach_servico_match_data(db: AsyncSession, items: list[PqItem]) -> None:
    if not inspect.iscoroutinefunction(getattr(db, "execute", None)):
        return
    base_ids = [
        item.servico_match_id for item in items
        if item.servico_match_id and item.servico_match_tipo == TipoServicoMatch.BASE_TCPO
    ]
    proprio_ids = [
        item.servico_match_id for item in items
        if item.servico_match_id and item.servico_match_tipo == TipoServicoMatch.ITEM_PROPRIO
    ]

    base_map = await BaseTcpoRepository(db).get_by_ids(base_ids)
    proprio_map = await ItensPropiosRepository(db).get_active_by_ids(proprio_ids)

    for item in items:
        snapshot = None
        if item.servico_match_tipo == TipoServicoMatch.BASE_TCPO and item.servico_match_id:
            snapshot = base_map.get(item.servico_match_id)
        elif item.servico_match_tipo == TipoServicoMatch.ITEM_PROPRIO and item.servico_match_id:
            snapshot = proprio_map.get(item.servico_match_id)

        setattr(item, "servico_match_codigo", getattr(snapshot, "codigo_origem", None))
        setattr(item, "servico_match_descricao", getattr(snapshot, "descricao", None))
        setattr(item, "servico_match_unidade", getattr(snapshot, "unidade_medida", None))


async def _to_pq_item_response(db: AsyncSession, item: PqItem) -> PqItemResponse:
    await _attach_servico_match_data(db, [item])
    return PqItemResponse.model_validate(item)


@router.post("/preview", response_model=PqPreviewResponse)
async def preview_planilha(
    proposta_id: UUID,
    arquivo: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqPreviewResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    svc = PqImportService(
        proposta_repo=PropostaRepository(db),
        importacao_repo=PqImportacaoRepository(db),
        item_repo=PqItemRepository(db),
        pq_layout_repo=PqLayoutRepository(db),
    )
    preview = await svc.preview_planilha(proposta_id, arquivo)
    return PqPreviewResponse(**preview)


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
        linhas_ignoradas=importacao.linhas_ignoradas,
    )


@router.post("/match", response_model=PqMatchStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def executar_match(
    proposta_id: UUID,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqMatchStatusResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    key = str(proposta_id)
    task = _match_tasks.get(key)

    # If already running, return current state (409-like but still 202)
    if task and task["status"] == "running":
        return PqMatchStatusResponse(**task)

    # If completed/failed, clear so it can be re-run
    _match_tasks[key] = {"status": "queued", "processados": 0, "sugeridos": 0, "sem_match": 0, "error": None}

    background_tasks.add_task(_run_match_background, proposta_id, current_user.id)
    logger.info("pq_match_enfileirado", proposta_id=key, usuario_id=str(current_user.id))
    return PqMatchStatusResponse(status="queued")


@router.get("/match/status", response_model=PqMatchStatusResponse)
async def status_match(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqMatchStatusResponse:
    """Retorna o estado atual do match em background para esta proposta."""
    await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, None, current_user, db)

    task = _match_tasks.get(str(proposta_id))
    if task is None:
        return PqMatchStatusResponse(status="not_started")
    return PqMatchStatusResponse(**task)


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
    await _attach_servico_match_data(db, items)
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
    elif body.acao == "manual":
        if body.codigo_original is not None:
            item.codigo_original = body.codigo_original
        if body.descricao_original is not None:
            item.descricao_original = body.descricao_original
        if body.unidade_medida_original is not None:
            item.unidade_medida_original = body.unidade_medida_original
        item.servico_match_id = None
        item.servico_match_tipo = None
        item.match_confidence = None
        await repo.update_status(item, StatusMatch.SEM_MATCH)

    if body.quantidade is not None:
        item.quantidade_original = body.quantidade
        await db.flush()

    if inspect.iscoroutinefunction(getattr(db, "execute", None)):
        await CpuGeracaoService(db).upsert_proposta_item_for_pq(item, proposta.bcu_cabecalho_id)
    await db.commit()
    await db.refresh(item)
    return await _to_pq_item_response(db, item)


@router.post("/itens/confirmar-todos", status_code=200)
async def confirmar_todos_sugeridos(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Confirma em lote todos os itens com status SUGERIDO.

    Não altera MANUAL, CONFIRMADO, SEM_MATCH ou PENDENTE.
    Retorna o número de itens confirmados.
    """
    from sqlalchemy import update as sa_update

    await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    result = await db.execute(
        sa_update(PqItem)
        .where(PqItem.proposta_id == proposta_id)
        .where(PqItem.match_status == StatusMatch.SUGERIDO)
        .values(match_status=StatusMatch.CONFIRMADO)
    )
    await db.commit()
    return {"confirmados": result.rowcount}


@router.post("/itens", response_model=PqItemResponse, status_code=status.HTTP_201_CREATED)
async def criar_pq_item_manual(
    proposta_id: UUID,
    body: PqItemManualCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqItemResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    existing = await PqItemRepository(db).list_by_proposta(proposta_id)
    max_linha = max((item.linha_planilha or 0 for item in existing), default=0)
    item = PqItem(proposta_id=proposta_id, codigo_original=body.codigo_original, descricao_original=body.descricao_original, unidade_medida_original=body.unidade_medida_original, quantidade_original=body.quantidade_original, servico_match_id=body.servico_match_id, servico_match_tipo=body.servico_match_tipo, match_confidence=1 if body.servico_match_id else None, match_status=StatusMatch.MANUAL if body.servico_match_id else StatusMatch.SEM_MATCH, linha_planilha=max_linha + 1, observacao="Incluido manualmente na revisao de match")
    db.add(item)
    await db.flush()
    await CpuGeracaoService(db).upsert_proposta_item_for_pq(item, proposta.bcu_cabecalho_id)
    await db.commit()
    await db.refresh(item)
    return await _to_pq_item_response(db, item)

@router.delete("/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_pq_item(
    proposta_id: UUID,
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    repo = PqItemRepository(db)
    item = await repo.get_by_id(item_id)
    if item is None or item.proposta_id != proposta_id:
        raise NotFoundError("PqItem", str(item_id))
    await PropostaItemRepository(db).delete_by_pq_item_id(item_id)
    await db.delete(item)
    await db.commit()
    return None
