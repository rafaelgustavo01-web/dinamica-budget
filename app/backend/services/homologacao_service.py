"""
Homologation workflow service.

Manages the lifecycle of PROPRIA items (operacional.itens_proprios):
  PENDENTE → APROVADO  (via POST /homologacao/aprovar with approved=True)
  PENDENTE → REPROVADO (via POST /homologacao/aprovar with approved=False)

RBAC enforcement is performed at the endpoint layer.
This service validates ownership (item.cliente_id == request.cliente_id).
"""

import math
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.enums import StatusHomologacao, TipoOperacaoAuditoria
from backend.models.itens_proprios import ItemProprio
from backend.repositories.associacao_repository import normalize_text
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.schemas.common import PaginatedResponse
from backend.schemas.homologacao import (
    AprovarHomologacaoRequest,
    AprovarHomologacaoResponse,
    CriarItemProprioRequest,
    ItemPendenteResponse,
)

logger = get_logger(__name__)


async def _registrar_auditoria(
    db: AsyncSession,
    tabela: str,
    registro_id: UUID,
    operacao: TipoOperacaoAuditoria,
    dados_anteriores: dict | None,
    dados_novos: dict | None,
    usuario_id: UUID | None,
    cliente_id: UUID | None,
    campo_alterado: str | None = None,
) -> None:
    from backend.models.auditoria_log import AuditoriaLog

    log = AuditoriaLog(
        id=uuid.uuid4(),
        tabela=tabela,
        registro_id=str(registro_id),
        operacao=operacao,
        campo_alterado=campo_alterado,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        usuario_id=usuario_id,
        cliente_id=cliente_id,
    )
    db.add(log)
    await db.flush()


class HomologacaoService:

    async def listar_pendentes(
        self,
        cliente_id: UUID,
        page: int,
        page_size: int,
        db: AsyncSession,
    ) -> PaginatedResponse[ItemPendenteResponse]:
        repo = ItensPropiosRepository(db)
        offset = (page - 1) * page_size
        items, total = await repo.list_pendentes_homologacao(
            cliente_id=cliente_id, offset=offset, limit=page_size
        )
        pages = math.ceil(total / page_size) if total else 0
        return PaginatedResponse(
            items=[ItemPendenteResponse.model_validate(s) for s in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def aprovar(
        self,
        request: AprovarHomologacaoRequest,
        aprovador_id: UUID,
        aprovador_email: str,
        db: AsyncSession,
    ) -> AprovarHomologacaoResponse:
        repo = ItensPropiosRepository(db)
        item = await repo.get_active_by_id(request.servico_id)
        if not item:
            raise NotFoundError("ItemProprio", str(request.servico_id))

        # Ownership guard: item must belong to the client in the request
        if item.cliente_id != request.cliente_id:
            raise AuthorizationError(
                "Item não pertence ao cliente informado."
            )

        if item.status_homologacao != StatusHomologacao.PENDENTE:
            raise ValidationError(
                f"Item já processado com status '{item.status_homologacao.value}'."
            )

        now = datetime.now(UTC)
        status_anterior = item.status_homologacao.value

        if request.aprovado:
            item.status_homologacao = StatusHomologacao.APROVADO
            item.aprovado_por_id = aprovador_id
            item.data_aprovacao = now
            item.descricao_tokens = normalize_text(item.descricao)
            mensagem = "Item homologado e disponível para busca."
            operacao = TipoOperacaoAuditoria.APROVAR
            logger.info("item_aprovado", item_id=str(item.id), by=aprovador_email)
        else:
            item.status_homologacao = StatusHomologacao.REPROVADO
            item.aprovado_por_id = aprovador_id
            item.data_aprovacao = now
            mensagem = f"Item reprovado. Motivo: {request.motivo_reprovacao or 'não informado'}."
            operacao = TipoOperacaoAuditoria.REPROVAR
            logger.info("item_reprovado", item_id=str(item.id), by=aprovador_email)

        await repo.update(item)

        await _registrar_auditoria(
            db=db,
            tabela="itens_proprios",
            registro_id=item.id,
            operacao=operacao,
            campo_alterado="status_homologacao",
            dados_anteriores={"status_homologacao": status_anterior},
            dados_novos={"status_homologacao": item.status_homologacao.value},
            usuario_id=aprovador_id,
            cliente_id=item.cliente_id,
        )

        return AprovarHomologacaoResponse(
            servico_id=item.id,
            status_homologacao=item.status_homologacao.value,
            aprovado_por=aprovador_email,
            data_aprovacao=now,
            mensagem=mensagem,
        )

    async def criar_item_proprio(
        self,
        request: CriarItemProprioRequest,
        criado_por_id: UUID,
        db: AsyncSession,
    ) -> ItemProprio:
        """
        Creates a PROPRIA item for a client starting with PENDENTE status.
        Embeddings are NOT synced here — only after approval (if needed).
        """
        repo = ItensPropiosRepository(db)
        item = ItemProprio(
            cliente_id=request.cliente_id,
            codigo_origem=request.codigo_origem,
            descricao=request.descricao,
            unidade_medida=request.unidade_medida,
            custo_unitario=request.custo_unitario,
            categoria_id=request.categoria_id,
            status_homologacao=StatusHomologacao.PENDENTE,
            descricao_tokens=normalize_text(request.descricao),
        )
        item = await repo.create(item)

        await _registrar_auditoria(
            db=db,
            tabela="itens_proprios",
            registro_id=item.id,
            operacao=TipoOperacaoAuditoria.CREATE,
            dados_anteriores=None,
            dados_novos={
                "descricao": item.descricao,
                "status_homologacao": item.status_homologacao.value,
            },
            usuario_id=criado_por_id,
            cliente_id=item.cliente_id,
        )

        return item


homologacao_service = HomologacaoService()

