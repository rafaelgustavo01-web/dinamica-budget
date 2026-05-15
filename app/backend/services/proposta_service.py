from datetime import datetime, timezone
import re
import inspect
from uuid import UUID

from sqlalchemy import text

from backend.core.exceptions import ConflictError, NotFoundError, ValidationError
from backend.models.enums import PropostaPapel, StatusProposta
from backend.models.proposta import Proposta
from backend.repositories.proposta_repository import PropostaRepository
from backend.services.proposta_acl_service import PropostaAclService


class PropostaService:
    def __init__(self, proposta_repo: PropostaRepository) -> None:
        self.proposta_repo = proposta_repo

    async def criar_proposta(self, cliente_id: UUID, usuario_id: UUID, dados) -> Proposta:
        codigo = dados.codigo or await self._gerar_codigo()
        proposta = Proposta(
            cliente_id=cliente_id,
            criado_por_id=usuario_id,
            codigo=codigo,
            titulo=dados.titulo,
            descricao=dados.descricao,
            status=StatusProposta.RASCUNHO,
            versao_cpu=1,
        )
        try:
            proposta = await self.proposta_repo.create(proposta)
        except Exception as exc:
            if "codigo" in str(exc).lower():
                raise ConflictError("Proposta", "codigo", codigo) from exc
            raise
        acl_svc = PropostaAclService(self.proposta_repo.db)
        await acl_svc.conceder(proposta.id, usuario_id, PropostaPapel.OWNER, usuario_id)
        return proposta

    async def listar_propostas(
        self,
        cliente_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Proposta], int]:
        offset = (page - 1) * page_size
        return await self.proposta_repo.list_by_cliente(cliente_id, offset=offset, limit=page_size)

    async def obter_por_id(self, proposta_id: UUID) -> Proposta:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))
        return proposta

    async def obter_detalhe(self, proposta_id: UUID, cliente_id: UUID) -> Proposta:
        proposta = await self.obter_por_id(proposta_id)
        if proposta.cliente_id != cliente_id:
            raise NotFoundError("Proposta", str(proposta_id))
        return proposta

    async def atualizar_metadados(self, proposta_id: UUID, cliente_id: UUID, dados) -> Proposta:
        proposta = await self.obter_detalhe(proposta_id, cliente_id)
        if proposta.status in {StatusProposta.APROVADA, StatusProposta.ARQUIVADA}:
            raise ValidationError("Proposta não pode ser editada neste status.")
        if dados.codigo is not None:
            codigo = dados.codigo.strip()
            if await self.proposta_repo.exists_by_codigo(codigo, exclude_id=proposta_id):
                raise ConflictError("Proposta", "codigo", codigo)
            proposta.codigo = codigo
        if dados.titulo is not None:
            proposta.titulo = dados.titulo
        if dados.descricao is not None:
            proposta.descricao = dados.descricao
        return await self.proposta_repo.update(proposta)

    async def atualizar_status(
        self,
        proposta_id: UUID,
        cliente_id: UUID,
        novo_status: StatusProposta,
    ) -> Proposta:
        proposta = await self.obter_detalhe(proposta_id, cliente_id)
        proposta.status = novo_status
        if novo_status in {StatusProposta.APROVADA, StatusProposta.ARQUIVADA}:
            proposta.data_finalizacao = datetime.now(timezone.utc)
        elif novo_status == StatusProposta.RASCUNHO:
            proposta.data_finalizacao = None
        return await self.proposta_repo.update(proposta)

    async def soft_delete(self, proposta_id: UUID, cliente_id: UUID) -> None:
        proposta = await self.obter_detalhe(proposta_id, cliente_id)
        await self.proposta_repo.soft_delete(proposta)

    async def _gerar_codigo(self) -> str:
        now = datetime.now(timezone.utc)
        pattern = await self._get_codigo_pattern()
        seq_match = re.search(r"\{seq(?::0?(\d+)d)?\}", pattern)
        seq_width = int(seq_match.group(1)) if seq_match and seq_match.group(1) else 4
        base_total = await self.proposta_repo.count_by_code_prefix("") + 1
        for offset in range(1000):
            seq = base_total + offset
            codigo = pattern.replace("{YYYY}", f"{now.year:04d}").replace("{YY}", f"{now.year % 100:02d}").replace("{MM}", f"{now.month:02d}")
            codigo = re.sub(r"\{seq(?::0?\d+d)?\}", f"{seq:0{seq_width}d}", codigo)
            exists = await self.proposta_repo.exists_by_codigo(codigo) if hasattr(self.proposta_repo, "exists_by_codigo") else False
            if not isinstance(exists, bool):
                exists = False
            if not exists:
                return codigo
        raise ConflictError("Proposta", "codigo", pattern)

    async def _get_codigo_pattern(self) -> str:
        try:
            result = await self.proposta_repo.db.execute(text("select value from operacional.app_config where key = 'proposal_number_pattern'"))
            value = result.scalar_one_or_none()
            if inspect.isawaitable(value):
                value.close()
                return "PROP-{YYYY}-{seq:04d}"
            return value if isinstance(value, str) and value else "PROP-{YYYY}-{seq:04d}"
        except Exception:
            return "PROP-{YYYY}-{seq:04d}"

