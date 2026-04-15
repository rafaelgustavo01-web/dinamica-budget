from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user, get_db
from app.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/compute-embeddings")
async def compute_embeddings(
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    count = await servico_catalog_service.compute_all_embeddings(db)
    return {"status": "ok", "embeddings_computados": count}
