import math
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.composicao_tcpo import ComposicaoTcpo
from app.models.enums import OrigemItem, StatusHomologacao, TipoRecurso
from app.models.servico_tcpo import ServicoTcpo
from app.models.versao_composicao import VersaoComposicao
from app.repositories.associacao_repository import normalize_text
from app.repositories.servico_tcpo_repository import ServicoTcpoRepository
from app.schemas.common import PaginatedResponse
from app.schemas.servico import (
    ComposicaoItemResponse,
    ExplodeComposicaoResponse,
    ServicoCreate,
    ServicoListParams,
    ServicoTcpoResponse,
    VersaoInfo,
)
from app.services.embedding_sync_service import embedding_sync_service

logger = get_logger(__name__)


class ServicoCatalogService:

    # ─── Listing / Get ────────────────────────────────────────────────────────

    async def list_servicos(
        self,
        params: ServicoListParams,
        db: AsyncSession,
        cliente_id: UUID | None = None,
    ) -> PaginatedResponse[ServicoTcpoResponse]:
        """
        Returns visible catalog: global TCPO approved + client's PROPRIA approved.
        When cliente_id is provided, scopes to that client's visibility.
        """
        repo = ServicoTcpoRepository(db)
        offset = (params.page - 1) * params.page_size
        items, total = await repo.list_catalogo_visivel(
            cliente_id=cliente_id,
            q=params.q,
            categoria_id=params.categoria_id,
            offset=offset,
            limit=params.page_size,
        )
        pages = math.ceil(total / params.page_size) if total else 0
        return PaginatedResponse(
            items=[ServicoTcpoResponse.model_validate(s) for s in items],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_servico(self, servico_id: UUID, db: AsyncSession) -> ServicoTcpoResponse:
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(servico_id))
        return ServicoTcpoResponse.model_validate(servico)

    # ─── Composição Explosion ─────────────────────────────────────────────────

    async def explode_composicao(
        self, servico_id: UUID, db: AsyncSession, cliente_id: UUID | None = None
    ) -> ExplodeComposicaoResponse:
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(servico_id))

        versao = await repo.get_versao_ativa(servico_id, cliente_id)
        itens, custo_total = await self._explode_recursivo(
            servico_id=servico_id,
            cliente_id=cliente_id,
            visited=set(),
            repo=repo,
        )

        versao_info: VersaoInfo | None = None
        if versao:
            versao_info = VersaoInfo(
                versao_id=versao.id,
                numero_versao=versao.numero_versao,
                origem=versao.origem.value,
                cliente_id=versao.cliente_id,
            )

        return ExplodeComposicaoResponse(
            servico=ServicoTcpoResponse.model_validate(servico),
            itens=itens,
            custo_total_composicao=custo_total,
            versao_info=versao_info,
        )

    async def _explode_recursivo(
        self,
        servico_id: UUID,
        cliente_id: UUID | None,
        visited: set[UUID],
        repo: "ServicoTcpoRepository",
    ) -> tuple[list[ComposicaoItemResponse], Decimal]:
        """
        DFS explosion of a service composition.
        - If a child has tipo_recurso=SERVICO, expand it recursively.
        - Otherwise, treat it as a leaf resource (MO, INSUMO, etc.).
        Cycle detection via `visited` set raises ValidationError on cycle.
        """
        if servico_id in visited:
            raise ValidationError("Ciclo detectado na composição — referência circular.")
        visited.add(servico_id)

        versao = await repo.get_versao_ativa(servico_id, cliente_id)
        if not versao:
            return [], Decimal("0")

        result: list[ComposicaoItemResponse] = []
        total = Decimal("0")

        for comp in versao.itens:
            filho = comp.insumo_filho
            if filho is None:
                # Lazy-load fallback
                filho = await repo.get_active_by_id(comp.insumo_filho_id)
            if filho is None:
                continue

            if filho.tipo_recurso == TipoRecurso.SERVICO:
                # Recursive expansion — accumulate sub-items with scaled quantities
                sub_itens, sub_custo = await self._explode_recursivo(
                    servico_id=filho.id,
                    cliente_id=cliente_id,
                    visited=visited,
                    repo=repo,
                )
                for item in sub_itens:
                    # Scale quantities by this composition's quantidade_consumo
                    result.append(
                        ComposicaoItemResponse(
                            id=item.id,
                            insumo_filho_id=item.insumo_filho_id,
                            descricao_filho=item.descricao_filho,
                            unidade_medida=item.unidade_medida,
                            quantidade_consumo=item.quantidade_consumo * comp.quantidade_consumo,
                            custo_unitario=item.custo_unitario,
                            custo_total=item.custo_total * comp.quantidade_consumo,
                        )
                    )
                total += sub_custo * comp.quantidade_consumo
            else:
                custo_item = comp.quantidade_consumo * filho.custo_unitario
                result.append(
                    ComposicaoItemResponse(
                        id=comp.id,
                        insumo_filho_id=filho.id,
                        descricao_filho=filho.descricao,
                        unidade_medida=comp.unidade_medida,
                        quantidade_consumo=comp.quantidade_consumo,
                        custo_unitario=filho.custo_unitario,
                        custo_total=custo_item,
                    )
                )
                total += custo_item

        return result, total

    # ─── Anti-Loop Validation ─────────────────────────────────────────────────

    async def _detectar_ciclo(
        self,
        pai_id: UUID,
        filho_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        DFS to detect circular references before inserting a composition.
        Returns True if adding (pai_id → filho_id) would create a cycle.

        A cycle exists if filho_id is an ancestor of pai_id,
        i.e., pai_id can be reached from filho_id via existing compositions.
        """
        # Build a descendant set of filho_id — if pai_id is in it, it's a cycle
        visited: set[UUID] = set()
        queue: list[UUID] = [filho_id]

        while queue:
            current = queue.pop()
            if current == pai_id:
                return True  # cycle detected
            if current in visited:
                continue
            visited.add(current)

            # Find all children of current
            result = await db.execute(
                select(ComposicaoTcpo.insumo_filho_id).where(
                    ComposicaoTcpo.servico_pai_id == current
                )
            )
            for (child_id,) in result.fetchall():
                queue.append(child_id)

        # Also check self-reference
        if pai_id == filho_id:
            return True

        return False

    async def adicionar_composicao(
        self,
        pai_id: UUID,
        filho_id: UUID,
        quantidade_consumo: Decimal,
        unidade_medida: str,
        db: AsyncSession,
    ) -> ComposicaoTcpo:
        """
        Add a composition item with anti-loop guard.
        Raises ValidationError if the addition would create a circular reference.
        Requires an active PROPRIA VersaoComposicao for pai_id.
        """
        repo = ServicoTcpoRepository(db)

        pai = await repo.get_active_by_id(pai_id)
        if not pai:
            raise NotFoundError("ServicoTcpo (pai)", str(pai_id))
        filho = await repo.get_active_by_id(filho_id)
        if not filho:
            raise NotFoundError("ServicoTcpo (filho)", str(filho_id))

        # Get the active PROPRIA versao for this service
        versao = await repo.get_versao_ativa(pai_id, pai.cliente_id)
        if not versao:
            raise ValidationError(
                "Nenhuma versão ativa de composição encontrada. "
                "Crie uma versão antes de adicionar componentes."
            )

        if await self._detectar_ciclo(pai_id, filho_id, db):
            raise ValidationError(
                f"Referência circular detectada: adicionar '{filho.descricao}' "
                f"a '{pai.descricao}' criaria um loop na composição."
            )

        comp = ComposicaoTcpo(
            id=uuid.uuid4(),
            servico_pai_id=pai_id,
            insumo_filho_id=filho_id,
            quantidade_consumo=quantidade_consumo,
            versao_id=versao.id,
            unidade_medida=unidade_medida,
        )
        db.add(comp)
        await db.flush()

        # Propagate cost change to PROPRIA parent (price roll-up)
        await self.recalcular_custo_pai(filho_id, db)

        logger.info(
            "composicao_adicionada",
            pai_id=str(pai_id),
            filho_id=str(filho_id),
            qtd=str(quantidade_consumo),
        )
        return comp

    # ─── Price Roll-up ────────────────────────────────────────────────────────

    async def recalcular_custo_pai(
        self, filho_id: UUID, db: AsyncSession
    ) -> list[UUID]:
        """
        When a child's custo_unitario changes, recalculate all parent services
        that include this child in their composition.
        Returns list of updated parent IDs.

        Note: This updates custo_unitario of the PAI based on sum of its
        composicao children — only for PROPRIA items (TCPO prices are immutable).

        Optimized: uses 4 batch queries instead of N+1 per parent.
        """
        # Query 1: find all compositions where this child is used
        result = await db.execute(
            select(ComposicaoTcpo).where(ComposicaoTcpo.insumo_filho_id == filho_id)
        )
        compositions = list(result.scalars().all())

        pai_ids = list({c.servico_pai_id for c in compositions})
        if not pai_ids:
            return []

        # Query 2: batch-load all PROPRIA parents at once
        pais_result = await db.execute(
            select(ServicoTcpo).where(
                ServicoTcpo.id.in_(pai_ids),
                ServicoTcpo.origem == OrigemItem.PROPRIA,
            )
        )
        pais = list(pais_result.scalars().all())

        if not pais:
            return []

        propria_pai_ids = [p.id for p in pais]

        # Query 3: load ALL compositions for ALL PROPRIA parents
        all_comps_result = await db.execute(
            select(ComposicaoTcpo).where(
                ComposicaoTcpo.servico_pai_id.in_(propria_pai_ids)
            )
        )
        all_comps = list(all_comps_result.scalars().all())

        # Query 4: batch-load ALL referenced children
        all_filho_ids = list({c.insumo_filho_id for c in all_comps})
        filhos_result = await db.execute(
            select(ServicoTcpo).where(ServicoTcpo.id.in_(all_filho_ids))
        )
        filhos_map = {f.id: f for f in filhos_result.scalars().all()}

        # In-memory: group compositions by parent and compute costs
        comps_by_pai: dict[UUID, list[ComposicaoTcpo]] = {}
        for c in all_comps:
            comps_by_pai.setdefault(c.servico_pai_id, []).append(c)

        updated_pais: list[UUID] = []
        for pai in pais:
            children = comps_by_pai.get(pai.id, [])
            total = sum(
                (c.quantidade_consumo * filhos_map[c.insumo_filho_id].custo_unitario
                 for c in children if c.insumo_filho_id in filhos_map),
                Decimal("0"),
            )

            if total != pai.custo_unitario:
                old_val = pai.custo_unitario
                pai.custo_unitario = total
                updated_pais.append(pai.id)
                logger.info(
                    "preco_pai_atualizado",
                    pai_id=str(pai.id),
                    old=float(old_val),
                    new=float(total),
                )

        if updated_pais:
            await db.flush()

        return updated_pais

    # ─── Create / Delete ──────────────────────────────────────────────────────

    async def create_servico(
        self, data: ServicoCreate, db: AsyncSession
    ) -> ServicoTcpoResponse:
        repo = ServicoTcpoRepository(db)
        servico = ServicoTcpo(
            id=uuid.uuid4(),
            codigo_origem=data.codigo_origem,
            descricao=data.descricao,
            unidade_medida=data.unidade_medida,
            custo_unitario=data.custo_unitario,
            categoria_id=data.categoria_id,
            origem=OrigemItem.TCPO,
            status_homologacao=StatusHomologacao.APROVADO,
            descricao_tokens=normalize_text(data.descricao),
        )
        servico = await repo.create(servico)
        await embedding_sync_service.sync_create_or_update(servico.id, db)
        logger.info("servico_tcpo_created", id=str(servico.id))
        return ServicoTcpoResponse.model_validate(servico)

    async def soft_delete_servico(self, servico_id: UUID, db: AsyncSession) -> None:
        repo = ServicoTcpoRepository(db)
        servico = await repo.get_active_by_id(servico_id)
        if not servico:
            raise NotFoundError("ServicoTcpo", str(servico_id))
        servico.deleted_at = datetime.now(UTC)
        await repo.update(servico)
        await embedding_sync_service.sync_delete(servico_id, db)

    async def compute_all_embeddings(self, db: AsyncSession) -> int:
        return await embedding_sync_service.compute_all_missing(db)

    # ─── Composição por Cópia ─────────────────────────────────────────────────

    async def clonar_composicao(
        self,
        servico_origem_id: UUID,
        cliente_id: UUID,
        codigo_clone: str,
        descricao: str | None,
        db: AsyncSession,
    ) -> ExplodeComposicaoResponse:
        """
        Clone a servico_tcpo (with its composicao_tcpo children) into a new
        independent PROPRIA item bound to cliente_id.

        Children are NOT cloned — only the link records are copied so the new
        item references the same insumos as the original.
        The clone starts with origem=PROPRIA and status_homologacao=PENDENTE.
        """
        repo = ServicoTcpoRepository(db)
        original = await repo.get_with_composicao(servico_origem_id)
        if not original:
            raise NotFoundError("ServicoTcpo", str(servico_origem_id))

        novo = ServicoTcpo(
            id=uuid.uuid4(),
            cliente_id=cliente_id,
            codigo_origem=codigo_clone,
            descricao=descricao if descricao is not None else original.descricao,
            unidade_medida=original.unidade_medida,
            custo_unitario=original.custo_unitario,
            categoria_id=original.categoria_id,
            origem=OrigemItem.PROPRIA,
            status_homologacao=StatusHomologacao.PENDENTE,
            descricao_tokens=normalize_text(descricao if descricao is not None else original.descricao),
        )
        db.add(novo)
        await db.flush()

        # Create VersaoComposicao for the new PROPRIA service
        nova_versao = VersaoComposicao(
            id=uuid.uuid4(),
            servico_id=novo.id,
            numero_versao=1,
            origem=OrigemItem.PROPRIA,
            cliente_id=cliente_id,
            is_ativa=True,
        )
        db.add(nova_versao)
        await db.flush()

        for comp in original.composicoes_pai:
            filho = comp.insumo_filho
            db.add(
                ComposicaoTcpo(
                    id=uuid.uuid4(),
                    servico_pai_id=novo.id,
                    insumo_filho_id=comp.insumo_filho_id,
                    quantidade_consumo=comp.quantidade_consumo,
                    versao_id=nova_versao.id,
                    unidade_medida=filho.unidade_medida if filho else original.unidade_medida,
                )
            )

        await db.flush()
        logger.info(
            "composicao_clonada",
            origem_id=str(servico_origem_id),
            clone_id=str(novo.id),
            cliente_id=str(cliente_id),
        )
        return await self.explode_composicao(novo.id, db)

    async def remover_componente(
        self,
        pai_id: UUID,
        componente_id: UUID,
        db: AsyncSession,
    ) -> None:
        """
        Remove a ComposicaoTcpo link record from a PROPRIA service.
        Raises NotFoundError if the link does not belong to this pai.
        Raises ValidationError if pai is not PROPRIA (prevents mutating TCPO catalog).
        """
        from sqlalchemy import select as sa_select

        repo = ServicoTcpoRepository(db)
        pai = await repo.get_active_by_id(pai_id)
        if not pai:
            raise NotFoundError("ServicoTcpo", str(pai_id))
        if pai.origem != OrigemItem.PROPRIA:
            raise ValidationError(
                "Apenas itens de origem PROPRIA podem ter componentes removidos."
            )

        result = await db.execute(
            sa_select(ComposicaoTcpo).where(
                ComposicaoTcpo.id == componente_id,
                ComposicaoTcpo.servico_pai_id == pai_id,
            )
        )
        comp = result.scalar_one_or_none()
        if not comp:
            raise NotFoundError("ComposicaoTcpo", str(componente_id))

        filho_id_salvo = comp.insumo_filho_id
        await db.delete(comp)
        await db.flush()

        # Propagate cost change to PROPRIA parent (price roll-up)
        await self.recalcular_custo_pai(filho_id_salvo, db)

        logger.info(
            "componente_removido",
            pai_id=str(pai_id),
            componente_id=str(componente_id),
        )


servico_catalog_service = ServicoCatalogService()
