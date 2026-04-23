"""
Endpoints for VersaoComposicao management.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_access
from app.core.exceptions import NotFoundError
from app.schemas.servico import VersaoComposicaoResponse
from app.services.versao_service import VersaoService
from app.repositories.versao_composicao_repository import VersaoComposicaoRepository
from app.repositories.itens_proprios_repository import ItensPropiosRepository

router = APIRouter(tags=["versoes"])


def _get_service(db: AsyncSession) -> VersaoService:
    return VersaoService(
        VersaoComposicaoRepository(db),
        ItensPropiosRepository(db),
    )


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
    svc = _get_service(db)
    # Validar acesso ao cliente do item antes de listar versões
    item = await svc.propria_repo.get_active_by_id(item_id)
    if not item:
        raise NotFoundError("ItemProprio", str(item_id))
    await require_cliente_access(item.cliente_id, current_user, db)

    versoes = await svc.list_versoes(item_id)
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
    svc = _get_service(db)
    await svc.assert_edit_permission(item_id, current_user, db)
    nova = await svc.criar_versao(item_id, current_user.id, db)
    return VersaoComposicaoResponse.model_validate(nova)


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
    svc = _get_service(db)
    # Resolve item_id from service (no SQL here)
    versao = await svc.versao_repo.get_by_id(versao_id)
    if not versao:
        raise NotFoundError("VersaoComposicao", str(versao_id))
    await svc.assert_edit_permission(versao.item_proprio_id, current_user, db)
    ativada = await svc.ativar_versao(versao_id, current_user.id, db)
    return VersaoComposicaoResponse.model_validate(ativada)
