from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_proposta_role
from backend.models.enums import PropostaPapel, StatusProposta
from backend.repositories.proposta_acl_repository import PropostaAclRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.schemas.common import PaginatedResponse
from backend.schemas.proposta import (
    PropostaCreate,
    PropostaNovaVersaoRequest,
    PropostaRejeitarRequest,
    PropostaResponse,
    PropostaUpdate,
)
from backend.services.proposta_service import PropostaService
from backend.services.proposta_versionamento_service import PropostaVersionamentoService

router = APIRouter(prefix="/propostas", tags=["propostas"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PropostaService:
    return PropostaService(PropostaRepository(db))


@router.post("/", response_model=PropostaResponse, status_code=status.HTTP_201_CREATED)
async def criar_proposta(
    data: PropostaCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PropostaResponse:
    proposta = await svc.criar_proposta(data.cliente_id, current_user.id, data)
    return PropostaResponse.model_validate(proposta)


@router.get("/", response_model=PaginatedResponse[PropostaResponse])
async def listar_propostas(
    cliente_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PaginatedResponse[PropostaResponse]:
    items, total = await svc.listar_propostas(cliente_id, page=page, page_size=page_size)
    proposta_ids = [p.id for p in items]
    papeis_map = await PropostaAclRepository(db).get_papeis_bulk(proposta_ids, current_user.id)
    pages = ceil(total / page_size) if total else 0
    def _to_response(item):
        resp = PropostaResponse.model_validate(item)
        resp.meu_papel = papeis_map.get(item.id)
        return resp

    return PaginatedResponse[PropostaResponse](
        items=[_to_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/aprovacoes", response_model=list[PropostaResponse])
async def fila_aprovacoes(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropostaResponse]:
    """Propostas AGUARDANDO_APROVACAO onde o user é APROVADOR ou OWNER."""
    repo = PropostaRepository(db)
    acl_repo = PropostaAclRepository(db)
    candidatas = await repo.list_aguardando_aprovacao()
    result = []
    for p in candidatas:
        root_id = p.proposta_root_id or p.id
        papeis = await acl_repo.get_papeis_bulk([root_id], current_user.id)
        papel = papeis.get(root_id)
        if papel in (PropostaPapel.APROVADOR, PropostaPapel.OWNER) or current_user.is_admin:
            resp = PropostaResponse.model_validate(p)
            resp.meu_papel = PropostaPapel.OWNER if current_user.is_admin else papel
            result.append(resp)
    return result


@router.get("/root/{root_id}/versoes", response_model=list[PropostaResponse])
async def listar_versoes(
    root_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropostaResponse]:
    await require_proposta_role(root_id, None, current_user, db)
    svc = PropostaVersionamentoService(db)
    versoes = await svc.listar_versoes(root_id)
    return [PropostaResponse.model_validate(v) for v in versoes]


@router.get("/{proposta_id}", response_model=PropostaResponse)
async def obter_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PropostaResponse:
    proposta = await svc.obter_por_id(proposta_id)
    await require_proposta_role(proposta_id, None, current_user, db)
    return PropostaResponse.model_validate(proposta)


@router.patch("/{proposta_id}", response_model=PropostaResponse)
async def atualizar_proposta(
    proposta_id: UUID,
    data: PropostaUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> PropostaResponse:
    proposta = await svc.obter_por_id(proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    proposta = await svc.atualizar_metadados(proposta_id, proposta.cliente_id, data)
    return PropostaResponse.model_validate(proposta)


@router.delete("/{proposta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    svc: PropostaService = Depends(_get_service),
) -> None:
    proposta = await svc.obter_por_id(proposta_id)
    await require_proposta_role(proposta_id, PropostaPapel.OWNER, current_user, db)
    await svc.soft_delete(proposta_id, proposta.cliente_id)


@router.post("/{proposta_id}/nova-versao", response_model=PropostaResponse, status_code=status.HTTP_201_CREATED)
async def nova_versao(
    proposta_id: UUID,
    body: PropostaNovaVersaoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    nova = await svc.nova_versao(proposta_id, current_user.id, body.motivo_revisao)
    await db.commit()
    return PropostaResponse.model_validate(nova)


@router.post("/{proposta_id}/enviar-aprovacao", response_model=PropostaResponse)
async def enviar_aprovacao(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    proposta = await svc.enviar_aprovacao(proposta_id)
    await db.commit()
    return PropostaResponse.model_validate(proposta)


@router.post("/{proposta_id}/aprovar", response_model=PropostaResponse)
async def aprovar_proposta(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.APROVADOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    proposta = await svc.aprovar(proposta_id, current_user.id)
    await db.commit()
    return PropostaResponse.model_validate(proposta)


@router.post("/{proposta_id}/rejeitar", response_model=PropostaResponse)
async def rejeitar_proposta(
    proposta_id: UUID,
    body: PropostaRejeitarRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.APROVADOR, current_user, db)
    svc = PropostaVersionamentoService(db)
    proposta = await svc.rejeitar(proposta_id, current_user.id, body.motivo)
    await db.commit()
    return PropostaResponse.model_validate(proposta)

