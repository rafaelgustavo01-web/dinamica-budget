import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_admin_user, get_current_catalog_import_user, get_db
from app.core.exceptions import ValidationError
from app.schemas.admin import (
    ComputeEmbeddingsResponse,
    ImportExecuteResponse,
    ImportPreviewResponse,
    ImportSourceType,
)
from app.services.import_preview_service import generate_import_preview
from app.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/compute-embeddings")
async def compute_embeddings(
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> ComputeEmbeddingsResponse:
    count = await servico_catalog_service.compute_all_embeddings(db)
    return ComputeEmbeddingsResponse(status="ok", embeddings_computados=count)


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_import(
    source_type: ImportSourceType = Form(...),
    file: UploadFile = File(...),
    _=Depends(get_current_catalog_import_user),
) -> ImportPreviewResponse:
    if not file.filename:
        raise ValidationError("Arquivo inválido para preview.")
    if not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx são suportados no preview.")

    payload = await file.read()
    if not payload:
        raise ValidationError("Arquivo vazio.")

    return generate_import_preview(source_type=source_type, file_name=file.filename, file_bytes=payload)


@router.post("/import/execute", response_model=ImportExecuteResponse)
async def execute_import(
    source_type: ImportSourceType = Form(...),
    confirm: bool = Form(False),
    file: UploadFile = File(...),
    _=Depends(get_current_catalog_import_user),
) -> ImportExecuteResponse:
    if not confirm:
        raise ValidationError("Confirmação obrigatória para executar a carga.")
    if not file.filename:
        raise ValidationError("Arquivo inválido para carga.")
    if not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx são suportados na carga.")

    data = await file.read()
    if not data:
        raise ValidationError("Arquivo vazio.")

    preview = generate_import_preview(
        source_type=source_type,
        file_name=file.filename,
        file_bytes=data,
    )
    mapped_confidences = [
        field.confidence
        for sheet in preview.sheets
        for field in sheet.mapped_fields
    ]
    avg_confidence = (
        sum(mapped_confidences) / len(mapped_confidences)
        if mapped_confidences
        else 0.0
    )
    if len(mapped_confidences) < 3 or avg_confidence < 0.45:
        raise ValidationError(
            "Mapeamento semântico insuficiente para executar a carga com segurança.",
            details={
                "average_confidence": round(avg_confidence, 4),
                "mapped_fields": len(mapped_confidences),
                "warnings": preview.warnings,
            },
        )

    upload_dir = Path("logs") / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename).suffix or ".xlsx"

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=upload_dir) as tmp:
            tmp.write(data)
            temp_path = Path(tmp.name)

        script_path = Path("scripts") / "etl_popular_base_consulta.py"
        if not script_path.exists():
            raise ValidationError("Script ETL não encontrado no servidor.")

        cmd = [
            sys.executable,
            str(script_path),
            "--database-url",
            settings.DATABASE_URL,
        ]

        if source_type == ImportSourceType.TCPO:
            cmd += ["--only-tcpo", "--tcpo-file", str(temp_path)]
        else:
            cmd += ["--only-pc", "--pc-file", str(temp_path)]

        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1200,
            check=False,
        )

        logs = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
        excerpt = logs[-4000:] if logs else None

        if completed.returncode != 0:
            raise ValidationError(
                "Falha na execução da carga ETL.",
                details={"log_excerpt": excerpt},
            )

        return ImportExecuteResponse(
            status="ok",
            source_type=source_type,
            file_name=file.filename,
            message="Carga executada com sucesso.",
            log_excerpt=excerpt,
        )
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
