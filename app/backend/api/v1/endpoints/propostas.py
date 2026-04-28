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
from backend.schemas.proposta_pc import (
    AlocacaoOut,
    AlocarRecursoRequest,
    HistogramaCompletoResponse,
    MontarHistogramaResponse,
    RecursoExtraCreate,
    RecursoExtraOut,
    RecursoExtraUpdate,
)
from backend.services.histograma_service import HistogramaService
from backend.services.proposta_recurso_extra_service import PropostaRecursoExtraService
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


# ── Histograma ───────────────────────────────────────────────────────────────

@router.post("/{proposta_id}/montar-histograma", response_model=MontarHistogramaResponse)
async def montar_histograma(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MontarHistogramaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    counts = await svc.montar_histograma(proposta_id)
    await db.commit()
    return MontarHistogramaResponse(**counts)


@router.get("/{proposta_id}/histograma", response_model=HistogramaCompletoResponse)
async def get_histograma(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> HistogramaCompletoResponse:
    await require_proposta_role(proposta_id, None, current_user, db)
    svc = HistogramaService(db)
    data = await svc.get_histograma(proposta_id)
    return HistogramaCompletoResponse(**data)


@router.patch("/{proposta_id}/histograma/{tabela}/{item_id}")
async def editar_item_histograma(
    proposta_id: UUID,
    tabela: str,
    item_id: UUID,
    body: dict,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    await svc.editar_item(tabela, item_id, body)
    await db.commit()
    return {"status": "ok"}


@router.post("/{proposta_id}/histograma/{tabela}/{item_id}/aceitar-bcu")
async def aceitar_valor_bcu(
    proposta_id: UUID,
    tabela: str,
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    await svc.aceitar_valor_bcu(tabela, item_id)
    await db.commit()
    return {"status": "ok"}


# ── Recursos Extras ──────────────────────────────────────────────────────────

@router.post("/{proposta_id}/recursos-extras", response_model=RecursoExtraOut, status_code=status.HTTP_201_CREATED)
async def criar_recurso_extra(
    proposta_id: UUID,
    body: RecursoExtraCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecursoExtraOut:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    recurso = await svc.criar(proposta_id, body.model_dump(), current_user.id)
    await db.commit()
    return RecursoExtraOut(
        id=recurso.id,
        proposta_id=recurso.proposta_id,
        tipo_recurso=recurso.tipo_recurso,
        descricao=recurso.descricao,
        unidade_medida=recurso.unidade_medida,
        custo_unitario=recurso.custo_unitario,
        observacao=recurso.observacao,
        alocacoes_count=0,
    )


@router.get("/{proposta_id}/recursos-extras", response_model=list[RecursoExtraOut])
async def listar_recursos_extras(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecursoExtraOut]:
    await require_proposta_role(proposta_id, None, current_user, db)
    svc = PropostaRecursoExtraService(db)
    items = await svc.listar_por_proposta(proposta_id)
    return [RecursoExtraOut(**i) for i in items]


@router.patch("/{proposta_id}/recursos-extras/{recurso_id}", response_model=RecursoExtraOut)
async def atualizar_recurso_extra(
    proposta_id: UUID,
    recurso_id: UUID,
    body: RecursoExtraUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecursoExtraOut:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    recurso = await svc.atualizar(recurso_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return RecursoExtraOut(
        id=recurso.id,
        proposta_id=recurso.proposta_id,
        tipo_recurso=recurso.tipo_recurso,
        descricao=recurso.descricao,
        unidade_medida=recurso.unidade_medida,
        custo_unitario=recurso.custo_unitario,
        observacao=recurso.observacao,
        alocacoes_count=len(recurso.alocacoes),
    )


@router.delete("/{proposta_id}/recursos-extras/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_recurso_extra(
    proposta_id: UUID,
    recurso_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    await svc.deletar(recurso_id)
    await db.commit()


@router.post("/{proposta_id}/composicoes/{composicao_id}/alocar-recurso", response_model=AlocacaoOut, status_code=status.HTTP_201_CREATED)
async def alocar_recurso(
    proposta_id: UUID,
    composicao_id: UUID,
    body: AlocarRecursoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlocacaoOut:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    alocacao = await svc.alocar(proposta_id, composicao_id, body.recurso_extra_id, body.quantidade_consumo)
    await db.commit()
    return AlocacaoOut.model_validate(alocacao)


@router.delete("/{proposta_id}/alocacoes/{alocacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desalocar_recurso(
    proposta_id: UUID,
    alocacao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    await svc.desalocar(proposta_id, alocacao_id)
    await db.commit()


# ── Histograma ───────────────────────────────────────────────────────────────

@router.post("/{proposta_id}/montar-histograma", response_model=MontarHistogramaResponse)
async def montar_histograma(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MontarHistogramaResponse:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    counts = await svc.montar_histograma(proposta_id)
    await db.commit()
    return MontarHistogramaResponse(**counts)


@router.get("/{proposta_id}/histograma", response_model=HistogramaCompletoResponse)
async def get_histograma(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> HistogramaCompletoResponse:
    await require_proposta_role(proposta_id, None, current_user, db)
    svc = HistogramaService(db)
    data = await svc.get_histograma(proposta_id)
    return HistogramaCompletoResponse(**data)


@router.patch("/{proposta_id}/histograma/{tabela}/{item_id}")
async def editar_item_histograma(
    proposta_id: UUID,
    tabela: str,
    item_id: UUID,
    body: dict,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    await svc.editar_item(tabela, item_id, body)
    await db.commit()
    return {"status": "ok"}


@router.post("/{proposta_id}/histograma/{tabela}/{item_id}/aceitar-bcu")
async def aceitar_valor_bcu(
    proposta_id: UUID,
    tabela: str,
    item_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = HistogramaService(db)
    await svc.aceitar_valor_bcu(tabela, item_id)
    await db.commit()
    return {"status": "ok"}


# ── Recursos Extras ──────────────────────────────────────────────────────────

@router.post("/{proposta_id}/recursos-extras", response_model=RecursoExtraOut, status_code=status.HTTP_201_CREATED)
async def criar_recurso_extra(
    proposta_id: UUID,
    body: RecursoExtraCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecursoExtraOut:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    recurso = await svc.criar(proposta_id, body.model_dump(), current_user.id)
    await db.commit()
    return RecursoExtraOut(
        id=recurso.id,
        proposta_id=recurso.proposta_id,
        tipo_recurso=recurso.tipo_recurso,
        descricao=recurso.descricao,
        unidade_medida=recurso.unidade_medida,
        custo_unitario=recurso.custo_unitario,
        observacao=recurso.observacao,
        alocacoes_count=0,
    )


@router.get("/{proposta_id}/recursos-extras", response_model=list[RecursoExtraOut])
async def listar_recursos_extras(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecursoExtraOut]:
    await require_proposta_role(proposta_id, None, current_user, db)
    svc = PropostaRecursoExtraService(db)
    items = await svc.listar_por_proposta(proposta_id)
    return [RecursoExtraOut(**i) for i in items]


@router.patch("/{proposta_id}/recursos-extras/{recurso_id}", response_model=RecursoExtraOut)
async def atualizar_recurso_extra(
    proposta_id: UUID,
    recurso_id: UUID,
    body: RecursoExtraUpdate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecursoExtraOut:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    recurso = await svc.atualizar(recurso_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return RecursoExtraOut(
        id=recurso.id,
        proposta_id=recurso.proposta_id,
        tipo_recurso=recurso.tipo_recurso,
        descricao=recurso.descricao,
        unidade_medida=recurso.unidade_medida,
        custo_unitario=recurso.custo_unitario,
        observacao=recurso.observacao,
        alocacoes_count=len(recurso.alocacoes),
    )


@router.delete("/{proposta_id}/recursos-extras/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_recurso_extra(
    proposta_id: UUID,
    recurso_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    await svc.deletar(recurso_id)
    await db.commit()


@router.post("/{proposta_id}/composicoes/{composicao_id}/alocar-recurso", response_model=AlocacaoOut, status_code=status.HTTP_201_CREATED)
async def alocar_recurso(
    proposta_id: UUID,
    composicao_id: UUID,
    body: AlocarRecursoRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AlocacaoOut:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    alocacao = await svc.alocar(proposta_id, composicao_id, body.recurso_extra_id, body.quantidade_consumo)
    await db.commit()
    return AlocacaoOut.model_validate(alocacao)


@router.delete("/{proposta_id}/alocacoes/{alocacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desalocar_recurso(
    proposta_id: UUID,
    alocacao_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_proposta_role(proposta_id, PropostaPapel.EDITOR, current_user, db)
    svc = PropostaRecursoExtraService(db)
    await svc.desalocar(proposta_id, alocacao_id)
    await db.commit()

