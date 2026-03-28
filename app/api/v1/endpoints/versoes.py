"""
Endpoints for VersaoComposicao management.

GET  /servicos/{servico_id}/versoes          — list versions visible to the client
POST /composicoes/{servico_id}/versoes       — create new PROPRIA version (clone of active TCPO)
PATCH /composicoes/versoes/{versao_id}/ativar — activate a version for the client
"""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_perfil
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.composicao_tcpo import ComposicaoTcpo
from app.models.enums import OrigemItem
from app.models.versao_composicao import VersaoComposicao
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.schemas.servico import VersaoComposicaoResponse

router = APIRouter(tags=["versoes"])

_PERFIS_EDICAO = ["APROVADOR", "ADMIN"]


@router.get(
    "/servicos/{servico_id}/versoes",
    response_model=list[VersaoComposicaoResponse],
    summary="Listar versões de composição de um serviço",
)
async def list_versoes(
    servico_id: UUID,
    cliente_id: UUID | None = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[VersaoComposicaoResponse]:
    """
    Lists all VersaoComposicao visible to the client:
      - Global TCPO versions (cliente_id IS NULL)
      - Client's own PROPRIA versions (when cliente_id provided)
    """
    repo = ServicoTcpoRepository(db)
    versoes = await repo.list_versoes(servico_id=servico_id, cliente_id=cliente_id)
    return [VersaoComposicaoResponse.model_validate(v) for v in versoes]


@router.post(
    "/composicoes/{servico_id}/versoes",
    response_model=VersaoComposicaoResponse,
    status_code=201,
    summary="Criar nova versão PROPRIA (clone da versão TCPO ativa)",
)
async def criar_versao(
    servico_id: UUID,
    cliente_id: UUID = Query(...),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VersaoComposicaoResponse:
    """
    Clone the active TCPO version into a new PROPRIA version for the client.
    The new version starts as inactive (is_ativa=False) to allow editing before activating.
    Requires APROVADOR or ADMIN role on the client.
    """
    await require_cliente_perfil(
        cliente_id=cliente_id,
        perfis_permitidos=_PERFIS_EDICAO,
        current_user=current_user,
        db=db,
    )

    repo = ServicoTcpoRepository(db)
    servico = await repo.get_active_by_id(servico_id)
    if not servico:
        raise NotFoundError("ServicoTcpo", str(servico_id))

    # Get active TCPO version to clone from
    tcpo_versao = await repo.get_versao_ativa(servico_id, cliente_id=None)
    if not tcpo_versao:
        raise ValidationError("Nenhuma versão TCPO ativa encontrada para clonar.")

    # Determine next version number for this client
    existing_versoes = await repo.list_versoes(servico_id=servico_id, cliente_id=cliente_id)
    propria_versoes = [v for v in existing_versoes if v.cliente_id == cliente_id]
    next_numero = max((v.numero_versao for v in propria_versoes), default=0) + 1

    # Create new PROPRIA version
    nova_versao = VersaoComposicao(
        id=uuid.uuid4(),
        servico_id=servico_id,
        numero_versao=next_numero,
        origem=OrigemItem.PROPRIA,
        cliente_id=cliente_id,
        is_ativa=False,
        criado_por_id=current_user.id,
    )
    db.add(nova_versao)
    await db.flush()

    # Clone ComposicaoTcpo items from TCPO version
    for item in tcpo_versao.itens:
        db.add(
            ComposicaoTcpo(
                id=uuid.uuid4(),
                servico_pai_id=item.servico_pai_id,
                insumo_filho_id=item.insumo_filho_id,
                quantidade_consumo=item.quantidade_consumo,
                versao_id=nova_versao.id,
                unidade_medida=item.unidade_medida,
            )
        )

    await db.flush()
    await db.refresh(nova_versao)
    return VersaoComposicaoResponse.model_validate(nova_versao)


@router.patch(
    "/composicoes/versoes/{versao_id}/ativar",
    response_model=VersaoComposicaoResponse,
    summary="Ativar uma versão de composição para o cliente",
)
async def ativar_versao(
    versao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VersaoComposicaoResponse:
    """
    Activate a VersaoComposicao for the client.
    Deactivates any previously active PROPRIA version for the same servico_id + cliente_id.
    Requires APROVADOR or ADMIN role on the client that owns this version.
    """
    result = await db.execute(
        select(VersaoComposicao).where(VersaoComposicao.id == versao_id)
    )
    versao = result.scalar_one_or_none()
    if not versao:
        raise NotFoundError("VersaoComposicao", str(versao_id))

    if versao.cliente_id is None:
        raise ValidationError("Versões TCPO globais não podem ser ativadas/desativadas por clientes.")

    await require_cliente_perfil(
        cliente_id=versao.cliente_id,
        perfis_permitidos=_PERFIS_EDICAO,
        current_user=current_user,
        db=db,
    )

    # Deactivate existing active PROPRIA versions for this servico + client
    other_result = await db.execute(
        select(VersaoComposicao).where(
            VersaoComposicao.servico_id == versao.servico_id,
            VersaoComposicao.cliente_id == versao.cliente_id,
            VersaoComposicao.is_ativa.is_(True),
            VersaoComposicao.id != versao_id,
        )
    )
    for other in other_result.scalars().all():
        other.is_ativa = False

    versao.is_ativa = True
    await db.flush()
    await db.refresh(versao)
    return VersaoComposicaoResponse.model_validate(versao)
