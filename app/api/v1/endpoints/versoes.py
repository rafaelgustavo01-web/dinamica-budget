"""
Endpoints for VersaoComposicao management.

GET    /servicos/{item_id}/versoes               — list versions for an ItemProprio
POST   /composicoes/{item_id}/versoes            — create new version (clone of active)
PATCH  /composicoes/versoes/{versao_id}/ativar   — activate a version
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_active_user,
    get_db,
    require_cliente_perfil,
)
from app.core.exceptions import NotFoundError
from app.models.composicao_cliente import ComposicaoCliente
from app.models.versao_composicao import VersaoComposicao
from app.repositories.itens_proprios_repository import ItensPropiosRepository
from app.repositories.versao_composicao_repository import VersaoComposicaoRepository
from app.schemas.servico import VersaoComposicaoResponse

router = APIRouter(tags=["versoes"])

_PERFIS_EDICAO = ["APROVADOR", "ADMIN"]


@router.get(
    "/servicos/{item_id}/versoes",
    response_model=list[VersaoComposicaoResponse],
    summary="Listar versões de composição de um item próprio",
)
async def list_versoes(
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[VersaoComposicaoResponse]:
    """
    Lists all VersaoComposicao for a PROPRIA item.
    On-premise model: any authenticated user may read versions.
    """
    propria_repo = ItensPropiosRepository(db)
    item = await propria_repo.get_active_by_id(item_id)
    if not item:
        raise NotFoundError("ItemProprio", str(item_id))

    versao_repo = VersaoComposicaoRepository(db)
    versoes = await versao_repo.list_versoes(item_id)
    return [VersaoComposicaoResponse.model_validate(v) for v in versoes]


@router.post(
    "/composicoes/{item_id}/versoes",
    response_model=VersaoComposicaoResponse,
    status_code=201,
    summary="Criar nova versão (clone da versão ativa atual)",
)
async def criar_versao(
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VersaoComposicaoResponse:
    """
    Clone the currently active VersaoComposicao into a new inactive version.
    The new version starts with is_ativa=False to allow editing before activating.
    If no active version exists, creates an empty version.
    Requires APROVADOR or ADMIN on the item's client.
    """
    propria_repo = ItensPropiosRepository(db)
    item = await propria_repo.get_active_by_id(item_id)
    if not item:
        raise NotFoundError("ItemProprio", str(item_id))

    await require_cliente_perfil(
        cliente_id=item.cliente_id,
        perfis_permitidos=_PERFIS_EDICAO,
        current_user=current_user,
        db=db,
    )

    versao_repo = VersaoComposicaoRepository(db)
    versoes_existentes = await versao_repo.list_versoes(item_id)
    next_numero = max((v.numero_versao for v in versoes_existentes), default=0) + 1

    nova_versao = VersaoComposicao(
        item_proprio_id=item_id,
        numero_versao=next_numero,
        is_ativa=False,
        criado_por_id=current_user.id,
    )
    db.add(nova_versao)
    await db.flush()

    # Clone ComposicaoCliente items from the current active version if it exists
    versao_ativa = await versao_repo.get_versao_ativa(item_id)
    if versao_ativa:
        result = await db.execute(
            select(ComposicaoCliente).where(ComposicaoCliente.versao_id == versao_ativa.id)
        )
        for comp in result.scalars().all():
            db.add(
                ComposicaoCliente(
                    versao_id=nova_versao.id,
                    insumo_base_id=comp.insumo_base_id,
                    insumo_proprio_id=comp.insumo_proprio_id,
                    quantidade_consumo=comp.quantidade_consumo,
                    unidade_medida=comp.unidade_medida,
                )
            )

    await db.flush()
    await db.refresh(nova_versao)
    return VersaoComposicaoResponse.model_validate(nova_versao)


@router.patch(
    "/composicoes/versoes/{versao_id}/ativar",
    response_model=VersaoComposicaoResponse,
    summary="Ativar uma versão de composição",
)
async def ativar_versao(
    versao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> VersaoComposicaoResponse:
    """
    Activate a VersaoComposicao.
    Deactivates any previously active version for the same item_proprio.
    Requires APROVADOR or ADMIN on the item's client.
    """
    result = await db.execute(
        select(VersaoComposicao).where(VersaoComposicao.id == versao_id)
    )
    versao = result.scalar_one_or_none()
    if not versao:
        raise NotFoundError("VersaoComposicao", str(versao_id))

    # Resolve client from the owning ItemProprio
    propria_repo = ItensPropiosRepository(db)
    item = await propria_repo.get_active_by_id(versao.item_proprio_id)
    if not item:
        raise NotFoundError("ItemProprio for versao", str(versao_id))

    await require_cliente_perfil(
        cliente_id=item.cliente_id,
        perfis_permitidos=_PERFIS_EDICAO,
        current_user=current_user,
        db=db,
    )

    # Deactivate all versions for this item, then activate the requested one
    versao_repo = VersaoComposicaoRepository(db)
    await versao_repo.deactivate_all(versao.item_proprio_id)
    versao.is_ativa = True
    await db.flush()
    await db.refresh(versao)
    return VersaoComposicaoResponse.model_validate(versao)
