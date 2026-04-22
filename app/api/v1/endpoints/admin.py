from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user, get_db
from app.schemas.etl import (
    EtlExecuteRequest,
    EtlExecuteResponse,
    EtlStatusResponse,
    EtlUploadResponse,
)
from app.services.etl_service import etl_service
from app.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/compute-embeddings")
async def compute_embeddings(
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    count = await servico_catalog_service.compute_all_embeddings(db)
    return {"status": "ok", "embeddings_computados": count}


# ── ETL endpoints ──────────────────────────────────────────────────────────────

@router.post(
    "/etl/upload-tcpo",
    response_model=EtlUploadResponse,
    summary="Fazer upload de Composições TCPO - PINI.xlsx e obter pré-visualização",
)
async def etl_upload_tcpo(
    file: UploadFile,
    _=Depends(get_current_admin_user),
) -> EtlUploadResponse:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo deve ser .xlsx ou .xls",
        )
    try:
        file_bytes = await file.read()
        return etl_service.parse_tcpo_pini(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post(
    "/etl/upload-converter",
    response_model=EtlUploadResponse,
    summary="Fazer upload de Converter em Data Center.xlsx e obter pré-visualização",
)
async def etl_upload_converter(
    file: UploadFile,
    _=Depends(get_current_admin_user),
) -> EtlUploadResponse:
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Arquivo deve ser .xlsx ou .xls",
        )
    try:
        file_bytes = await file.read()
        return etl_service.parse_converter_datacenter(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post(
    "/etl/execute",
    response_model=EtlExecuteResponse,
    summary="Executar carga ETL usando tokens de upload já processados",
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
