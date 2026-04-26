from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_proposta_role
from backend.core.exceptions import NotFoundError
from backend.models.enums import PropostaPapel
from backend.repositories.proposta_acl_repository import PropostaAclRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.repositories.usuario_repository import UsuarioRepository
from backend.schemas.proposta import PropostaAclCreate, PropostaAclResponse
from backend.services.proposta_acl_service import PropostaAclService

router = APIRouter(prefix="/propostas/{proposta_id}/acl", tags=["proposta-acl"])


async def _get_proposta_or_404(db, proposta_id: UUID):
    proposta = await PropostaRepository(db).get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    return proposta


@router.get("/", response_model=list[PropostaAclResponse])
async def listar_acl(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PropostaAclResponse]:
    await require_proposta_role(proposta_id, None, current_user, db)
    items = await PropostaAclRepository(db).list_by_proposta(proposta_id)
    # Enriquecer com nome/email do usuário
    usuario_ids = {i.usuario_id for i in items} | {i.created_by for i in items}
    usuarios = {}
    if usuario_ids:
        user_repo = UsuarioRepository(db)
        for uid in usuario_ids:
            user = await user_repo.get_by_id(uid)
            if user:
                usuarios[uid] = user
    return [
        PropostaAclResponse(
            id=i.id,
            proposta_id=i.proposta_id,
            usuario_id=i.usuario_id,
            usuario_nome=getattr(usuarios.get(i.usuario_id), "nome", ""),
            usuario_email=getattr(usuarios.get(i.usuario_id), "email", ""),
            papel=i.papel,
            created_at=i.created_at,
            created_by=i.created_by,
        )
        for i in items
    ]


@router.post("/", response_model=PropostaAclResponse, status_code=status.HTTP_201_CREATED)
async def conceder_papel(
    proposta_id: UUID,
    body: PropostaAclCreate,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PropostaAclResponse:
    await require_proposta_role(proposta_id, PropostaPapel.OWNER, current_user, db)
    svc = PropostaAclService(db)
    acl = await svc.conceder(proposta_id, body.usuario_id, body.papel, current_user.id)
    user_repo = UsuarioRepository(db)
    user = await user_repo.get_by_id(acl.usuario_id)
    return PropostaAclResponse(
        id=acl.id,
        proposta_id=acl.proposta_id,
        usuario_id=acl.usuario_id,
        usuario_nome=getattr(user, "nome", ""),
        usuario_email=getattr(user, "email", ""),
        papel=acl.papel,
        created_at=acl.created_at,
        created_by=acl.created_by,
    )


@router.delete("/{usuario_id}/{papel}", status_code=status.HTTP_204_NO_CONTENT)
async def revogar_papel(
    proposta_id: UUID,
    usuario_id: UUID,
    papel: PropostaPapel,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await require_proposta_role(proposta_id, PropostaPapel.OWNER, current_user, db)
    svc = PropostaAclService(db)
    await svc.revogar(proposta_id, usuario_id, papel)
