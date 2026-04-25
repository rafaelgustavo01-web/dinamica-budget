"""
Extração PC — endpoints para explosão de composição por cliente.

GET /extracao/servicos-cliente  → lista de associações do cliente (terminologia própria)
GET /extracao/{servico_id}/dados-brutos → BOM completo (ExplodeComposicaoResponse)
GET /extracao/{servico_id}/download-xlsx → .xlsx para download
"""

from __future__ import annotations

import io
from datetime import datetime
from uuid import UUID

import openpyxl
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import (
    get_current_active_user,
    get_db,
    require_cliente_access,
)
from backend.core.exceptions import NotFoundError
from backend.models.associacao_inteligente import AssociacaoInteligente
from backend.models.base_tcpo import BaseTcpo
from backend.schemas.common import PaginatedResponse
from backend.schemas.extracao import ServicoClienteAssociado
from backend.schemas.servico import ExplodeComposicaoResponse
from backend.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/extracao", tags=["extracao"])


@router.get(
    "/servicos-cliente",
    response_model=PaginatedResponse[ServicoClienteAssociado],
    summary="Listar serviços usando a terminologia do cliente",
)
async def listar_servicos_cliente(
    cliente_id: UUID = Query(..., description="ID do cliente (contexto)"),
    q: str | None = Query(None, description="Filtro por descrição do cliente"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ServicoClienteAssociado]:
    await require_cliente_access(cliente_id, current_user, db)

    base_query = (
        select(
            AssociacaoInteligente.id,
            AssociacaoInteligente.item_referencia_id,
            AssociacaoInteligente.texto_busca_normalizado,
            AssociacaoInteligente.frequencia_uso,
            BaseTcpo.codigo_origem,
            BaseTcpo.descricao,
            BaseTcpo.unidade_medida,
            BaseTcpo.custo_base,
            BaseTcpo.tipo_recurso,
        )
        .join(BaseTcpo, BaseTcpo.id == AssociacaoInteligente.item_referencia_id)
        .where(AssociacaoInteligente.cliente_id == cliente_id)
    )

    if q:
        base_query = base_query.where(
            AssociacaoInteligente.texto_busca_normalizado.ilike(f"%{q}%")
        )

    # Count
    from sqlalchemy import func, select as sa_select  # noqa: PLC0415

    count_sub = base_query.subquery()
    count_result = await db.execute(
        sa_select(func.count()).select_from(count_sub)
    )
    total = count_result.scalar_one()

    # Paginate — ordered by frequência desc (most-used first)
    paginated = base_query.order_by(
        AssociacaoInteligente.frequencia_uso.desc()
    ).offset((page - 1) * page_size).limit(page_size)

    rows = (await db.execute(paginated)).fetchall()

    import math  # noqa: PLC0415

    items = [
        ServicoClienteAssociado(
            id=str(row[0]),
            item_referencia_id=str(row[1]),
            descricao_cliente=row[2],
            frequencia_uso=row[3],
            codigo_origem=row[4],
            descricao_tcpo=row[5],
            unidade_medida=row[6],
            custo_base=float(row[7]),
            tipo_recurso=row[8].value if row[8] else None,
        )
        for row in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{servico_id}/dados-brutos",
    response_model=ExplodeComposicaoResponse,
    summary="Explodir composição de um serviço (BOM completo)",
)
async def dados_brutos(
    servico_id: UUID,
    cliente_id: UUID = Query(..., description="ID do cliente (contexto de acesso)"),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExplodeComposicaoResponse:
    await require_cliente_access(cliente_id, current_user, db)
    try:
        return await servico_catalog_service.explode_composicao(
            servico_id, db, cliente_id=cliente_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{servico_id}/download-xlsx",
    summary="Baixar BOM como planilha .xlsx",
    response_class=StreamingResponse,
)
async def download_xlsx(
    servico_id: UUID,
    cliente_id: UUID = Query(..., description="ID do cliente (contexto de acesso)"),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    await require_cliente_access(cliente_id, current_user, db)
    try:
        bom = await servico_catalog_service.explode_composicao(
            servico_id, db, cliente_id=cliente_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOM"

    # Header
    headers = [
        "Código",
        "Descrição",
        "Tipo Recurso",
        "Unidade",
        "Qtd Consumo",
        "Custo Unit. (R$)",
        "Custo Total (R$)",
    ]
    ws.append(headers)

    for item in bom.itens:
        ws.append(
            [
                item.insumo_filho_id,   # UUID — parent can look up code_origem separately
                item.descricao_filho,
                None,                   # tipo_recurso not in ComposicaoItemResponse
                item.unidade_medida,
                float(item.quantidade_consumo),
                float(item.custo_unitario),
                float(item.custo_total),
            ]
        )

    # Summary row
    ws.append([])
    ws.append(["", "", "", "TOTAL", "", "", float(bom.custo_total_composicao)])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PC_{bom.servico.codigo_origem}_{ts}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

