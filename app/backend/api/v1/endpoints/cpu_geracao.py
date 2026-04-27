from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_proposta_role
from backend.models.enums import PropostaPapel
from backend.core.exceptions import NotFoundError
from backend.repositories.proposta_repository import PropostaRepository
from backend.schemas.proposta import (
    ComposicaoDetalheResponse,
    CpuGeracaoResponse,
    CpuItemResponse,
    RecalcularBdiRequest,
    RecalcularBdiResponse,
)
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
    bcu_cabecalho_id: UUID | None = Query(default=None),
    percentual_bdi: Decimal = Query(default=Decimal("0"), ge=0),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CpuGeracaoResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    svc = CpuGeracaoService(db)
    resultado = await svc.gerar_cpu_para_proposta(
        proposta_id=proposta_id,
        bcu_cabecalho_id=bcu_cabecalho_id,
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
    await require_proposta_role(proposta_id, None, current_user, db)

    svc = CpuGeracaoService(db)
    items = await svc.listar_cpu_itens(proposta_id)
    return [CpuItemResponse.model_validate(item) for item in items]


@router.post(
    "/itens/{composicao_id}/explodir-sub",
    status_code=201,
)
async def explodir_sub_composicao(
    proposta_id: UUID,
    composicao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    from backend.services.cpu_explosao_service import CpuExplosaoService
    svc = CpuExplosaoService(db)
    try:
        filhos = await svc.explodir_sub_composicao(proposta_id, composicao_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    await db.commit()
    return [
        {
            "id": str(f.id),
            "descricao_insumo": f.descricao_insumo,
            "unidade_medida": f.unidade_medida,
            "quantidade_consumo": str(f.quantidade_consumo),
            "nivel": f.nivel,
            "e_composicao": f.e_composicao,
            "pai_composicao_id": str(f.pai_composicao_id),
        }
        for f in filhos
    ]


@router.get("/itens/{item_id}/composicoes", response_model=list[ComposicaoDetalheResponse])
async def listar_composicoes_proposta_item(
    proposta_id: UUID,
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComposicaoDetalheResponse]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, None, current_user, db)

    svc = CpuGeracaoService(db)
    composicoes = await svc.listar_composicoes_item(item_id)
    return [ComposicaoDetalheResponse.model_validate(c) for c in composicoes]


@router.post("/recalcular-bdi", response_model=RecalcularBdiResponse)
async def recalcular_bdi_proposta(
    proposta_id: UUID,
    body: RecalcularBdiRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecalcularBdiResponse:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)

    svc = CpuGeracaoService(db)
    resultado = await svc.recalcular_bdi(proposta_id, body.percentual_bdi)
    await db.commit()
    return RecalcularBdiResponse.model_validate(resultado)

