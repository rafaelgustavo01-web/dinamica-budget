"""
Homologation workflow service.

Manages the lifecycle of PROPRIA items:
  PENDENTE → APROVADO  (via POST /homologacao/aprovar with approved=True)
  PENDENTE → REPROVADO (via POST /homologacao/aprovar with approved=False)

RBAC enforcement is performed at the endpoint layer.
This service validates ownership (servico.cliente_id == request.cliente_id).
"""

import math
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.enums import OrigemItem, StatusHomologacao, TipoOperacaoAuditoria
from app.models.servico_tcpo import ServicoTcpo
from app.repositories.associacao_repository import normalize_text
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.homologacao import (
    AprovarHomologacaoRequest,
    AprovarHomologacaoResponse,
    CriarItemProprioRequest,
    ItemPendenteResponse,
)
from app.services.embedding_sync_service import embedding_sync_service

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
    from app.models.auditoria_log import AuditoriaLog

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
        repo = ServicoTcpoRepository(db)
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
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(request.servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(request.servico_id))

        # Ownership guard: servico must belong to the client in the request
        if servico.cliente_id != request.cliente_id:
            raise AuthorizationError(
                "Item não pertence ao cliente informado."
            )

        if servico.status_homologacao != StatusHomologacao.PENDENTE:
            raise ValidationError(
                f"Item já processado com status '{servico.status_homologacao.value}'."
            )

        now = datetime.now(UTC)
        status_anterior = servico.status_homologacao.value

        if request.aprovado:
            servico.status_homologacao = StatusHomologacao.APROVADO
            servico.aprovado_por_id = aprovador_id
            servico.data_aprovacao = now
            servico.descricao_tokens = normalize_text(servico.descricao)
            await embedding_sync_service.sync_create_or_update(servico.id, db)
            mensagem = "Item homologado e disponível para busca."
            operacao = TipoOperacaoAuditoria.APROVAR
            logger.info("item_aprovado", servico_id=str(servico.id), by=aprovador_email)
        else:
            servico.status_homologacao = StatusHomologacao.REPROVADO
            servico.aprovado_por_id = aprovador_id
            servico.data_aprovacao = now
            mensagem = f"Item reprovado. Motivo: {request.motivo_reprovacao or 'não informado'}."
            operacao = TipoOperacaoAuditoria.REPROVAR
            logger.info("item_reprovado", servico_id=str(servico.id), by=aprovador_email)

        await repo.update(servico)

        await _registrar_auditoria(
            db=db,
            tabela="servico_tcpo",
            registro_id=servico.id,
            operacao=operacao,
            campo_alterado="status_homologacao",
            dados_anteriores={"status_homologacao": status_anterior},
            dados_novos={"status_homologacao": servico.status_homologacao.value},
            usuario_id=aprovador_id,
            cliente_id=servico.cliente_id,
        )

        return AprovarHomologacaoResponse(
            servico_id=servico.id,
            status_homologacao=servico.status_homologacao.value,
            aprovado_por=aprovador_email,
            data_aprovacao=now,
            mensagem=mensagem,
        )

    async def criar_item_proprio(
        self,
        request: CriarItemProprioRequest,
        criado_por_id: UUID,
        db: AsyncSession,
    ) -> ServicoTcpo:
        """
        Creates a PROPRIA item for a client starting with PENDENTE status.
        Does NOT sync embeddings yet — only synced after approval.
        """
        repo = ServicoTcpoRepository(db)
        servico = ServicoTcpo(
            id=uuid.uuid4(),
            cliente_id=request.cliente_id,
            codigo_origem=request.codigo_origem,
            descricao=request.descricao,
            unidade_medida=request.unidade_medida,
            custo_unitario=request.custo_unitario,
            categoria_id=request.categoria_id,
            origem=OrigemItem.PROPRIA,
            status_homologacao=StatusHomologacao.PENDENTE,
            descricao_tokens=normalize_text(request.descricao),
        )
        servico = await repo.create(servico)

        await _registrar_auditoria(
            db=db,
            tabela="servico_tcpo",
            registro_id=servico.id,
            operacao=TipoOperacaoAuditoria.CREATE,
            dados_anteriores=None,
            dados_novos={
                "descricao": servico.descricao,
                "origem": servico.origem.value,
                "status_homologacao": servico.status_homologacao.value,
            },
            usuario_id=criado_por_id,
            cliente_id=servico.cliente_id,
        )

        return servico


homologacao_service = HomologacaoService()
