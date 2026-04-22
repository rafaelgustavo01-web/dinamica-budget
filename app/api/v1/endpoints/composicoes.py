"""
REST endpoints for composition-by-copy (cloning TCPO compositions).

Endpoints:
  POST  /composicoes/clonar                          — clone a service + its children
  POST  /composicoes/{pai_id}/componentes            — add child to a PROPRIA composition
  DELETE /composicoes/{pai_id}/componentes/{id}      — remove child from PROPRIA composition
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_cliente_perfil
from app.core.exceptions import AuthorizationError, NotFoundError
from app.repositories.itens_proprios_repository import ItensPropiosRepository
from app.schemas.composicao import AdicionarComponenteRequest, ClonarComposicaoRequest
from app.schemas.servico import ExplodeComposicaoResponse
from app.services.servico_catalog_service import servico_catalog_service

router = APIRouter(prefix="/composicoes", tags=["composicoes"])

_PERFIS_EDICAO = ["APROVADOR", "ADMIN"]


@router.post(
    "/clonar",
    response_model=ExplodeComposicaoResponse,
    status_code=201,
    summary="Clonar composição TCPO como item PROPRIA do cliente",
)
async def clonar_composicao(
    request: ClonarComposicaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExplodeComposicaoResponse:
    """
    Clone a servico_tcpo (with all its composicao_tcpo children) into a new
    independent PROPRIA item bound to the given cliente_id.

    Requires APROVADOR or ADMIN role on the target client.
    The clone starts with status_homologacao=PENDENTE.
    """
    await require_cliente_perfil(
        cliente_id=request.cliente_id,
        perfis_permitidos=_PERFIS_EDICAO,
        current_user=current_user,
        db=db,
    )
    return await servico_catalog_service.clonar_composicao(
        servico_origem_id=request.servico_origem_id,
        cliente_id=request.cliente_id,
        codigo_clone=request.codigo_clone,
        descricao=request.descricao,
        criado_por_id=current_user.id,
        db=db,
    )


async def _validate_pai_propria(pai_id: UUID, current_user, db: AsyncSession):
    """Load pai (ItemProprio), assert it exists, and check RBAC on its cliente_id."""
    repo = ItensPropiosRepository(db)
    pai = await repo.get_active_by_id(pai_id)
    if not pai:
        raise NotFoundError("ItemProprio", str(pai_id))
    if pai.cliente_id is None:
        raise AuthorizationError(
            "Apenas itens próprios do cliente podem ser editados."
        )
    await require_cliente_perfil(
        cliente_id=pai.cliente_id,
        perfis_permitidos=_PERFIS_EDICAO,
        current_user=current_user,
        db=db,
    )
    return pai


@router.post(
    "/{pai_id}/componentes",
    response_model=ExplodeComposicaoResponse,
    summary="Adicionar componente-filho a uma composição PROPRIA",
)
async def adicionar_componente(
    pai_id: UUID,
    request: AdicionarComponenteRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExplodeComposicaoResponse:
    """
    Add a child component to a cloned (PROPRIA) composition.
    Anti-loop DFS is applied before inserting.
    Requires APROVADOR or ADMIN on the client that owns this composition.
    """
    await _validate_pai_propria(pai_id, current_user, db)
    await servico_catalog_service.adicionar_composicao(
        pai_id=pai_id,
        filho_id=request.insumo_filho_id,
        quantidade_consumo=request.quantidade_consumo,
        unidade_medida=request.unidade_medida,
        db=db,
    )
    return await servico_catalog_service.explode_composicao(pai_id, db)


@router.delete(
    "/{pai_id}/componentes/{componente_id}",
    status_code=204,
    summary="Remover componente-filho de uma composição PROPRIA",
)
async def remover_componente(
    pai_id: UUID,
    componente_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a ComposicaoCliente link from a PROPRIA composition.
    `componente_id` is the ComposicaoCliente.id (link record), not the insumo UUID.
    Requires APROVADOR or ADMIN on the client that owns this composition.
    """
    await _validate_pai_propria(pai_id, current_user, db)
    await servico_catalog_service.remover_componente(
        pai_id=pai_id,
        componente_id=componente_id,
        db=db,
    )
