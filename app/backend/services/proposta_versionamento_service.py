"""Service for proposta versioning and approval workflow."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.models.enums import StatusProposta
from backend.models.proposta import Proposta
from backend.repositories.proposta_repository import PropostaRepository

UTC = timezone.utc


class PropostaVersionamentoService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PropostaRepository(db)

    async def nova_versao(
        self,
        proposta_id: UUID,
        criador_id: UUID,
        motivo_revisao: str | None = None,
    ) -> Proposta:
        """
        Clone metadata from current version, close it, and create a new numbered version.
        PQ and CPU start fresh (RASCUNHO). Only metadata is cloned.
        """
        atual = await self.repo.get_by_id(proposta_id)
        if atual is None:
            raise NotFoundError("Proposta", str(proposta_id))
        if not atual.is_versao_atual:
            raise UnprocessableEntityError(
                "Só é possível criar nova versão a partir da versão atual."
            )
        if atual.is_fechada:
            raise UnprocessableEntityError(
                "A versão atual está fechada. Não é possível gerar nova versão."
            )

        root_id = atual.proposta_root_id or atual.id
        max_versao = await self.repo.max_numero_versao(root_id)
        proximo_numero = (max_versao or 1) + 1

        # Close current version
        atual.is_versao_atual = False
        atual.is_fechada = True
        self.db.add(atual)
        await self.db.flush()

        # Extract base code (strip -vN suffix if present)
        codigo_base = atual.codigo.split("-v")[0]
        novo_codigo = f"{codigo_base}-v{proximo_numero}"

        nova = Proposta(
            cliente_id=atual.cliente_id,
            criado_por_id=criador_id,
            codigo=novo_codigo,
            titulo=atual.titulo,
            descricao=atual.descricao,
            status=StatusProposta.RASCUNHO,
            proposta_root_id=root_id,
            numero_versao=proximo_numero,
            versao_anterior_id=atual.id,
            is_versao_atual=True,
            is_fechada=False,
            requer_aprovacao=atual.requer_aprovacao,
            pc_cabecalho_id=atual.pc_cabecalho_id,
            motivo_revisao=motivo_revisao,
        )
        self.db.add(nova)
        await self.db.flush()
        await self.db.refresh(nova)
        return nova

    async def enviar_aprovacao(self, proposta_id: UUID) -> Proposta:
        """Move proposta from CPU_GERADA → AGUARDANDO_APROVACAO."""
        proposta = await self._get_or_404(proposta_id)
        if not proposta.requer_aprovacao:
            raise UnprocessableEntityError(
                "Esta proposta não requer aprovação formal."
            )
        if proposta.status != StatusProposta.CPU_GERADA:
            raise UnprocessableEntityError(
                f"Proposta deve estar em CPU_GERADA para enviar aprovação. "
                f"Status atual: {proposta.status.value}"
            )
        proposta.status = StatusProposta.AGUARDANDO_APROVACAO
        self.db.add(proposta)
        await self.db.flush()
        await self.db.refresh(proposta)
        return proposta

    async def aprovar(self, proposta_id: UUID, aprovador_id: UUID) -> Proposta:
        """Move proposta from AGUARDANDO_APROVACAO → APROVADA."""
        proposta = await self._get_or_404(proposta_id)
        if proposta.status != StatusProposta.AGUARDANDO_APROVACAO:
            raise UnprocessableEntityError(
                f"Proposta não está aguardando aprovação. "
                f"Status atual: {proposta.status.value}"
            )
        proposta.status = StatusProposta.APROVADA
        proposta.aprovado_por_id = aprovador_id
        proposta.aprovado_em = datetime.now(UTC)
        self.db.add(proposta)
        await self.db.flush()
        await self.db.refresh(proposta)
        return proposta

    async def rejeitar(
        self,
        proposta_id: UUID,
        aprovador_id: UUID,
        motivo: str | None = None,
    ) -> Proposta:
        """Move proposta from AGUARDANDO_APROVACAO → CPU_GERADA (rejected)."""
        proposta = await self._get_or_404(proposta_id)
        if proposta.status != StatusProposta.AGUARDANDO_APROVACAO:
            raise UnprocessableEntityError(
                f"Proposta não está aguardando aprovação. "
                f"Status atual: {proposta.status.value}"
            )
        proposta.status = StatusProposta.CPU_GERADA
        proposta.aprovado_por_id = None
        proposta.aprovado_em = None
        if motivo:
            proposta.motivo_revisao = motivo
        self.db.add(proposta)
        await self.db.flush()
        await self.db.refresh(proposta)
        return proposta

    async def listar_versoes(self, proposta_root_id: UUID) -> list[Proposta]:
        """Return all versions for a given root proposal, ordered by numero_versao."""
        return await self.repo.list_by_root(proposta_root_id)

    async def _get_or_404(self, proposta_id: UUID) -> Proposta:
        p = await self.repo.get_by_id(proposta_id)
        if p is None:
            raise NotFoundError("Proposta", str(proposta_id))
        return p
