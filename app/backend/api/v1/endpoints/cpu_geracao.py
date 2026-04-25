from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_cliente_access
from backend.core.exceptions import NotFoundError
from backend.repositories.proposta_repository import PropostaRepository
from backend.schemas.proposta import CpuGeracaoResponse, CpuItemResponse
from backend.services.cpu_geracao_service import CpuGeracaoService

router = APIRouter(prefix="/propostas/{proposta_id}/cpu", tags=["cpu"])


async def _get_proposta_or_404(db: AsyncSession, proposta_id: UUID):
    proposta = await PropostaRepository(db).get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    return proposta


@router.post("/gerar", response_model=CpuGeracaoResponse)
async def gerar_cpu(
    proposta_id: UUID,
    pc_cabecalho_id: UUID | None = Query(default=None),
    percentual_bdi: Decimal = Query(default=Decimal("0"), ge=0),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CpuGeracaoResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = CpuGeracaoService(db)
    resultado = await svc.gerar_cpu_para_proposta(
        proposta_id=proposta_id,
        pc_cabecalho_id=pc_cabecalho_id,
        percentual_bdi=percentual_bdi,
    )
    return CpuGeracaoResponse.model_validate(resultado)


@router.get("/itens", response_model=list[CpuItemResponse])
async def listar_cpu_itens(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[CpuItemResponse]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    svc = CpuGeracaoService(db)
    items = await svc.listar_cpu_itens(proposta_id)
    return [CpuItemResponse.model_validate(item) for item in items]

