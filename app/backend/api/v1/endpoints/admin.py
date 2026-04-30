from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_admin_user, get_current_catalog_import_user, get_db
from backend.schemas.admin import ComputeEmbeddingsResponse
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

router = APIRouter(prefix="/admin", tags=["admin"])


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
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> EtlExecuteResponse:
    try:
        return await etl_service.execute_load(request, db)
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
