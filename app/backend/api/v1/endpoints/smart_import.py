from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db
from backend.core.exceptions import NotFoundError
from backend.models.smart_import import SmartImportJob
from backend.repositories.import_profile_repository import ImportProfileRepository
from backend.schemas.smart_import import (
    ClassifyRequest,
    CommitJobRequest,
    CommitJobResponse,
    SmartImportJobOut,
    StagingRowAdd,
    StagingRowEdit,
    StagingRowOut,
)
from backend.services.smart_import.row_classifier import RowClass
from backend.services.smart_import_service import SmartImportService

router = APIRouter(prefix="/smart-import", tags=["smart-import"])


async def _get_job(job_id: UUID, db: AsyncSession) -> SmartImportJob:
    result = await db.execute(select(SmartImportJob).where(SmartImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("SmartImportJob", str(job_id))
    return job


@router.post("", response_model=SmartImportJobOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    cliente_id: UUID = Form(...),
    proposta_id: UUID | None = Form(default=None),
    sheet_name: str | None = Form(default=None),
    profile_header_row: int | None = Form(default=None),
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SmartImportJobOut:
    content = await file.read()
    svc = SmartImportService()
    job = await svc.create_job(
        cliente_id=cliente_id,
        filename=file.filename or "upload",
        content=content,
        db=db,
        proposta_id=proposta_id,
        sheet_name=sheet_name,
        profile_header_row=profile_header_row,
    )
    return SmartImportJobOut.from_job(job)


@router.get("/{job_id}", response_model=SmartImportJobOut)
async def get_job(
    job_id: UUID,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SmartImportJobOut:
    job = await _get_job(job_id, db)
    return SmartImportJobOut.from_job(job)


@router.patch("/{job_id}/rows/{row_idx}", response_model=StagingRowOut)
async def edit_row(
    job_id: UUID,
    row_idx: int,
    body: StagingRowEdit,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StagingRowOut:
    job = await _get_job(job_id, db)
    SmartImportService().patch_row(job, row_idx, body.model_dump(exclude_none=True))
    await db.commit()
    rows = job.payload_staging["rows"]
    updated = next(r for r in rows if r["idx"] == row_idx)
    return StagingRowOut(**updated)


@router.post("/{job_id}/rows", response_model=StagingRowOut, status_code=201)
async def add_row(
    job_id: UUID,
    body: StagingRowAdd,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StagingRowOut:
    job = await _get_job(job_id, db)
    new_row = SmartImportService().add_row(job, body.model_dump())
    await db.commit()
    return StagingRowOut(**new_row)


@router.delete("/{job_id}/rows/{row_idx}", status_code=204)
async def delete_row(
    job_id: UUID,
    row_idx: int,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    job = await _get_job(job_id, db)
    SmartImportService().delete_row(job, row_idx)
    await db.commit()


@router.patch("/{job_id}/rows/{row_idx}/classify", response_model=StagingRowOut)
async def reclassify_row(
    job_id: UUID,
    row_idx: int,
    body: ClassifyRequest,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StagingRowOut:
    job = await _get_job(job_id, db)
    SmartImportService().reclassify_row(job, row_idx, RowClass(body.row_class))
    await db.commit()
    rows = job.payload_staging["rows"]
    updated = next(r for r in rows if r["idx"] == row_idx)
    return StagingRowOut(**updated)


@router.post("/{job_id}/commit", response_model=CommitJobResponse)
async def commit_job(
    job_id: UUID,
    body: CommitJobRequest,
    _current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommitJobResponse:
    job = await _get_job(job_id, db)
    svc = SmartImportService()
    job = await svc.commit_job(job, db, corrections=body.corrections)
    profile = await ImportProfileRepository(db).get_by_id(job.profile_id)
    return CommitJobResponse(
        job_id=job.id,
        status=job.status,
        profile_id=job.profile_id,
        score_confianca=float(profile.score_confianca) if profile else 0.0,
        uso_count=profile.uso_count if profile else 0,
        corrections_applied=len(body.corrections),
    )
