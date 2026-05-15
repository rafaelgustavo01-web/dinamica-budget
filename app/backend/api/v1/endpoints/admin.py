from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_admin_user, get_current_catalog_import_user, get_db
from backend.core.database import async_session_factory
from backend.schemas.admin import ComputeEmbeddingsResponse, SystemSettingsResponse, SystemSettingsUpdate
from backend.schemas.etl import (
    EtlExecuteRequest,
    EtlExecuteResponse,
    EtlStatusResponse,
    EtlUploadResponse,
)
from backend.services.etl_service import etl_service
from backend.services.servico_catalog_service import servico_catalog_service
from fastapi import Form
from backend.schemas.etl import EtlMode
from backend.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

DEFAULT_PROPOSAL_NUMBER_PATTERN = "PROP-{YYYY}-{seq:04d}"

def _validate_proposal_number_pattern(pattern: str) -> str:
    value = pattern.strip()
    if not value or "{seq" not in value:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Pattern deve conter {seq} ou {seq:04d}")
    return value

@router.get("/settings", response_model=SystemSettingsResponse)
async def get_settings(_=Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)) -> SystemSettingsResponse:
    result = await db.execute(text("select value from operacional.app_config where key = 'proposal_number_pattern'"))
    return SystemSettingsResponse(proposal_number_pattern=result.scalar_one_or_none() or DEFAULT_PROPOSAL_NUMBER_PATTERN)

@router.patch("/settings", response_model=SystemSettingsResponse)
async def update_settings(body: SystemSettingsUpdate, _=Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)) -> SystemSettingsResponse:
    pattern = _validate_proposal_number_pattern(body.proposal_number_pattern)
    await db.execute(text("insert into operacional.app_config (key, value) values ('proposal_number_pattern', :value) on conflict (key) do update set value = excluded.value, updated_at = now()"), {"value": pattern})
    return SystemSettingsResponse(proposal_number_pattern=pattern)



async def _background_compute_embeddings() -> None:
    """Background task: compute missing embeddings with a fresh DB session."""
    try:
        async with async_session_factory() as db:
            count = await servico_catalog_service.compute_all_embeddings(db)
            logger.info("background_embeddings_done", count=count)
    except Exception as exc:  # noqa: BLE001
        logger.warning("background_embeddings_failed", error=str(exc))


@router.post("/compute-embeddings")
async def compute_embeddings(
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ComputeEmbeddingsResponse:
    count = await servico_catalog_service.compute_all_embeddings(db)
    return ComputeEmbeddingsResponse(status="ok", embeddings_computados=count)


@router.post(
    "/etl/upload-tcpo",
    response_model=EtlUploadResponse,
    summary="Fazer upload de Composicoes TCPO - PINI.xlsx e obter pre-visualizacao",
)
async def etl_upload_tcpo(
    file: UploadFile,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EtlUploadResponse:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo deve ser .xlsx ou .xls",
        )
    try:
        file_bytes = await file.read()
        return await etl_service.parse_tcpo_pini_and_store(file_bytes, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post(
    "/etl/execute",
    response_model=EtlExecuteResponse,
    summary="Executar carga ETL usando tokens de upload ja processados",
)
async def etl_execute(
    request: EtlExecuteRequest,
    background_tasks: BackgroundTasks,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EtlExecuteResponse:
    try:
        # Run ETL without blocking on embeddings (recomputar_embeddings=False here)
        result = await etl_service.execute_load(
            EtlExecuteRequest(
                parse_token_tcpo=request.parse_token_tcpo,
                parse_token_converter=request.parse_token_converter,
                mode=request.mode,
                recomputar_embeddings=False,  # handled by background task below
            ),
            db,
        )
        # Dispatch embedding computation in background after commit
        if request.recomputar_embeddings:
            background_tasks.add_task(_background_compute_embeddings)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get(
    "/etl/status",
    response_model=EtlStatusResponse,
    summary="Obter contagem atual de registros em referencia.*",
)
async def etl_status(
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EtlStatusResponse:
    return await etl_service.get_status(db)


# Compatibility endpoints for the newer frontend paths (/admin/import/*)
@router.post('/import/preview', summary='Compatibility: preview import (multipart)')
async def import_preview_compat(
    source_type: str = Form(...),
    file: UploadFile = File(...),
    _=Depends(get_current_catalog_import_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    st = (source_type or '').upper()
    # Map supported source types
    if st == 'TCPO':
        upload = await etl_service.parse_tcpo_pini_and_store(file_bytes, db)
    else:
        # default: try converter datacenter
        upload = await etl_service.parse_converter_datacenter_and_store(file_bytes, db)

    # Build a simplified ImportPreviewResponse compatible with frontend expectations
    return {
        'source_type': st,
        'file_name': upload.arquivo,
        'total_rows': upload.parse_preview.total_itens + upload.parse_preview.total_relacoes,
        'estimated_records': upload.parse_preview.total_itens,
        'warnings': upload.parse_preview.avisos,
        'sheets': [],
    }


@router.post('/import/execute', summary='Compatibility: execute import immediately')
async def import_execute_compat(
    source_type: str = Form(...),
    confirm: str = Form('true'),
    file: UploadFile | None = None,
    _=Depends(get_current_catalog_import_user),
    db: AsyncSession = Depends(get_db),
):
    # If a file is provided, parse and persist token first
    parse_token_tcpo = None
    parse_token_converter = None
    st = (source_type or '').upper()
    if file is not None:
        file_bytes = await file.read()
        if st == 'TCPO':
            upload = await etl_service.parse_tcpo_pini_and_store(file_bytes, db)
            parse_token_tcpo = upload.parse_token
        else:
            upload = await etl_service.parse_converter_datacenter_and_store(file_bytes, db)
            parse_token_converter = upload.parse_token

    # Build execute request
    from backend.schemas.etl import EtlExecuteRequest

    req = EtlExecuteRequest(
        parse_token_tcpo=parse_token_tcpo,
        parse_token_converter=parse_token_converter,
        mode=EtlMode.UPSERT,
        recomputar_embeddings=(confirm.lower() != 'false'),
    )

    result = await etl_service.execute_load(req, db)

    return {
        'status': 'ok',
        'source_type': st,
        'file_name': upload.arquivo if file is not None else None,
        'message': 'Import executed',
        'log_excerpt': None,
    }
