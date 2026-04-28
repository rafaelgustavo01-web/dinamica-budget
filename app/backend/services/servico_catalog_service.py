import math
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.base_tcpo import BaseTcpo
from backend.models.composicao_base import ComposicaoBase
from backend.models.composicao_cliente import ComposicaoCliente
from backend.models.enums import StatusHomologacao, TipoRecurso
from backend.models.itens_proprios import ItemProprio
from backend.models.versao_composicao import VersaoComposicao
from backend.repositories.associacao_repository import normalize_text
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.versao_composicao_repository import VersaoComposicaoRepository
from backend.schemas.common import PaginatedResponse
from backend.schemas.servico import (
    ComposicaoComponenteResponse,
    ComposicaoItemResponse,
    ExplodeComposicaoResponse,
    ServicoCreate,
    ServicoListParams,
    ServicoTcpoResponse,
    VersaoInfo,
)
from backend.services.embedding_sync_service import embedding_sync_service

logger = get_logger(__name__)


class ServicoCatalogService:

    # â”€â”€â”€ Listing / Get â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def list_servicos(
        self,
        params: ServicoListParams,
        db: AsyncSession,
        cliente_id: UUID | None = None,
    ) -> PaginatedResponse[ServicoTcpoResponse]:
        """
        Returns paginated catalog view:
          - referencia.base_tcpo items (TCPO, always visible, listed first)
          - operacional.itens_proprios APROVADO scoped to cliente_id (appended after)
        Pagination spans both sources in sequence.
        """
        base_repo = BaseTcpoRepository(db)
        offset = (params.page - 1) * params.page_size
        limit = params.page_size

        tcpo_items, tcpo_total = await base_repo.list_paginated(
            q=params.q, categoria_id=params.categoria_id, offset=offset, limit=limit
        )

        propria_items: list[ItemProprio] = []
        propria_total = 0
        if cliente_id:
            propria_repo = ItensPropiosRepository(db)
            propria_offset = max(0, offset - tcpo_total)
            propria_limit = limit - len(tcpo_items)
            if propria_limit > 0:
                propria_items, propria_total = await propria_repo.list_catalogo_visivel(
                    cliente_id=cliente_id,
                    q=params.q,
                    categoria_id=params.categoria_id,
                    offset=propria_offset,
                    limit=propria_limit,
                )

        combined: list = tcpo_items + propria_items
        total = tcpo_total + propria_total
        pages = math.ceil(total / params.page_size) if total else 0
        return PaginatedResponse(
            items=[ServicoTcpoResponse.model_validate(s) for s in combined],
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        )

    async def get_servico(self, servico_id: UUID, db: AsyncSession) -> ServicoTcpoResponse:
        """Try BaseTcpo first (referencia), then ItemProprio (operacional)."""
        base_repo = BaseTcpoRepository(db)
        item = await base_repo.get_by_id(servico_id)
        if item is None:
            propria_repo = ItensPropiosRepository(db)
            item = await propria_repo.get_active_by_id(servico_id)
        if item is None:
            raise NotFoundError("Item", str(servico_id))
        return ServicoTcpoResponse.model_validate(item)

    # â”€â”€â”€ ComposiÃ§Ã£o Explosion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def explode_composicao(
        self, servico_id: UUID, db: AsyncSession, cliente_id: UUID | None = None
    ) -> ExplodeComposicaoResponse:
        """
        Explode BOM of a catalog item.
        - BaseTcpo: DFS via referencia.composicao_base (immutable TCPO BOM)
        - ItemProprio: DFS via active VersaoComposicao â†’ ComposicaoCliente (XOR FKs)
        """
        base_repo = BaseTcpoRepository(db)
        item = await base_repo.get_by_id(servico_id)
        is_tcpo = item is not None

        if not is_tcpo:
            propria_repo = ItensPropiosRepository(db)
            item = await propria_repo.get_active_by_id(servico_id)

        if item is None:
            raise NotFoundError("Item", str(servico_id))

        versao_info: VersaoInfo | None = None

        if is_tcpo:
            itens, custo_total = await self._explode_recursivo_tcpo(
                item_id=servico_id, visited=set(), db=db
            )
        else:
            versao_repo = VersaoComposicaoRepository(db)
            versao = await versao_repo.get_versao_ativa(servico_id)
            if versao:
                versao_info = VersaoInfo(
                    versao_id=versao.id,
                    numero_versao=versao.numero_versao,
                )
            itens, custo_total = await self._explode_recursivo_propria(
                item_id=servico_id, visited=set(), db=db
            )

        return ExplodeComposicaoResponse(
            servico=ServicoTcpoResponse.model_validate(item),
            itens=itens,
            custo_total_composicao=custo_total,
            versao_info=versao_info,
        )

    async def listar_componentes_diretos(
        self, servico_id: UUID, db: AsyncSession
    ) -> list[ComposicaoComponenteResponse]:
        """Return direct children (level 1) of a composition, with tipo_recurso for tree UI."""
        base_repo = BaseTcpoRepository(db)
        item = await base_repo.get_by_id(servico_id)
        is_tcpo = item is not None

        if not is_tcpo:
            propria_repo = ItensPropiosRepository(db)
            item = await propria_repo.get_active_by_id(servico_id)

        if item is None:
            raise NotFoundError("Item", str(servico_id))

        items: list[ComposicaoComponenteResponse] = []

        if is_tcpo:
            result_comp = await db.execute(
                select(ComposicaoBase).where(ComposicaoBase.servico_pai_id == servico_id)
            )
            composicoes = list(result_comp.scalars().all())
            # Batch-fetch all children in one query — eliminates N+1
            filho_ids = [c.insumo_filho_id for c in composicoes]
            filhos_map = await base_repo.get_by_ids(filho_ids)
            for comp in composicoes:
                filho = filhos_map.get(comp.insumo_filho_id)
                if filho is None:
                    continue
                custo_item = comp.quantidade_consumo * (filho.custo_base or Decimal("0"))
                items.append(
                    ComposicaoComponenteResponse(
                        id=comp.id,
                        insumo_filho_id=filho.id,
                        descricao_filho=filho.descricao,
                        unidade_medida=comp.unidade_medida or filho.unidade_medida,
                        quantidade_consumo=comp.quantidade_consumo,
                        custo_unitario=filho.custo_base or Decimal("0"),
                        custo_total=custo_item,
                        tipo_recurso=filho.tipo_recurso.value if filho.tipo_recurso else None,
                        codigo_origem=filho.codigo_origem,
                    )
                )
        else:
            versao_repo = VersaoComposicaoRepository(db)
            versao = await versao_repo.get_versao_ativa(servico_id)
            if versao:
                # Batch-fetch all BaseTcpo children in one query
                base_ids = [c.insumo_base_id for c in versao.itens if c.insumo_base_id is not None]
                base_filhos_map = await base_repo.get_by_ids(base_ids)
                for comp in versao.itens:
                    if comp.insumo_base_id is not None:
                        filho = base_filhos_map.get(comp.insumo_base_id)
                        if filho is None:
                            continue
                        custo_item = comp.quantidade_consumo * (filho.custo_base or Decimal("0"))
                        items.append(
                            ComposicaoComponenteResponse(
                                id=comp.id,
                                insumo_filho_id=filho.id,
                                descricao_filho=filho.descricao,
                                unidade_medida=comp.unidade_medida or filho.unidade_medida,
                                quantidade_consumo=comp.quantidade_consumo,
                                custo_unitario=filho.custo_base or Decimal("0"),
                                custo_total=custo_item,
                                tipo_recurso=filho.tipo_recurso.value if filho.tipo_recurso else None,
                                codigo_origem=filho.codigo_origem,
                            )
                        )
                    elif comp.insumo_proprio_id is not None:
                        propria_repo = ItensPropiosRepository(db)
                        filho = await propria_repo.get_active_by_id(comp.insumo_proprio_id)
                        if filho is None:
                            continue
                        custo_item = comp.quantidade_consumo * (filho.custo_unitario or Decimal("0"))
                        items.append(
                            ComposicaoComponenteResponse(
                                id=comp.id,
                                insumo_filho_id=filho.id,
                                descricao_filho=filho.descricao,
                                unidade_medida=comp.unidade_medida or filho.unidade_medida,
                                quantidade_consumo=comp.quantidade_consumo,
                                custo_unitario=filho.custo_unitario or Decimal("0"),
                                custo_total=custo_item,
                                tipo_recurso=filho.tipo_recurso.value if filho.tipo_recurso else None,
                                codigo_origem=getattr(filho, "codigo_origem", None),
                            )
                        )

        return items

    async def _explode_recursivo_tcpo(
        self,
        item_id: UUID,
        visited: set[UUID],
        db: AsyncSession,
    ) -> tuple[list[ComposicaoItemResponse], Decimal]:
        """DFS over referencia.composicao_base (immutable TCPO BOM)."""
        if item_id in visited:
            raise ValidationError("Ciclo detectado na composiÃ§Ã£o TCPO.")
        visited.add(item_id)

        result_comp = await db.execute(
            select(ComposicaoBase).where(ComposicaoBase.servico_pai_id == item_id)
        )
        composicoes = list(result_comp.scalars().all())

        items: list[ComposicaoItemResponse] = []
        total = Decimal("0")
        base_repo = BaseTcpoRepository(db)

        for comp in composicoes:
            filho: BaseTcpo | None = await base_repo.get_by_id(comp.insumo_filho_id)
            if filho is None:
                continue

            if filho.tipo_recurso == TipoRecurso.SERVICO:
                sub_itens, sub_custo = await self._explode_recursivo_tcpo(
                    item_id=filho.id, visited=visited, db=db
                )
                for sub in sub_itens:
                    items.append(
                        ComposicaoItemResponse(
                            id=sub.id,
                            insumo_filho_id=sub.insumo_filho_id,
                            descricao_filho=sub.descricao_filho,
                            unidade_medida=sub.unidade_medida,
                            quantidade_consumo=sub.quantidade_consumo * comp.quantidade_consumo,
                            custo_unitario=sub.custo_unitario,
                            custo_total=sub.custo_total * comp.quantidade_consumo,
                        )
                    )
                total += sub_custo * comp.quantidade_consumo
            else:
                custo_item = comp.quantidade_consumo * filho.custo_base
                items.append(
                    ComposicaoItemResponse(
                        id=comp.id,
                        insumo_filho_id=filho.id,
                        descricao_filho=filho.descricao,
                        unidade_medida=comp.unidade_medida,
                        quantidade_consumo=comp.quantidade_consumo,
                        custo_unitario=filho.custo_base,
                        custo_total=custo_item,
                    )
                )
                total += custo_item

        return items, total

    async def _explode_recursivo_propria(
        self,
        item_id: UUID,
        visited: set[UUID],
        db: AsyncSession,
    ) -> tuple[list[ComposicaoItemResponse], Decimal]:
        """DFS over ComposicaoCliente (PROPRIA BOM with XOR BaseTcpo/ItemProprio children)."""
        if item_id in visited:
            raise ValidationError("Ciclo detectado na composiÃ§Ã£o PROPRIA.")
        visited.add(item_id)

        versao_repo = VersaoComposicaoRepository(db)
        versao = await versao_repo.get_versao_ativa(item_id)
        if versao is None:
            return [], Decimal("0")

        items: list[ComposicaoItemResponse] = []
        total = Decimal("0")
        base_repo = BaseTcpoRepository(db)
        propria_repo = ItensPropiosRepository(db)

        for comp in versao.itens:
            if comp.insumo_base_id is not None:
                # TCPO child: leaf â€” no further expansion in PROPRIA context
                filho_base: BaseTcpo | None = comp.insumo_base
                if filho_base is None:
                    filho_base = await base_repo.get_by_id(comp.insumo_base_id)
                if filho_base is None:
                    continue
                custo_item = comp.quantidade_consumo * filho_base.custo_base
                items.append(
                    ComposicaoItemResponse(
                        id=comp.id,
                        insumo_filho_id=filho_base.id,
                        descricao_filho=filho_base.descricao,
                        unidade_medida=comp.unidade_medida or filho_base.unidade_medida,
                        quantidade_consumo=comp.quantidade_consumo,
                        custo_unitario=filho_base.custo_base,
                        custo_total=custo_item,
                    )
                )
                total += custo_item

            elif comp.insumo_proprio_id is not None:
                filho_prop: ItemProprio | None = comp.insumo_proprio
                if filho_prop is None:
                    filho_prop = await propria_repo.get_active_by_id(comp.insumo_proprio_id)
                if filho_prop is None:
                    continue

                if filho_prop.tipo_recurso == TipoRecurso.SERVICO:
                    sub_itens, sub_custo = await self._explode_recursivo_propria(
                        item_id=filho_prop.id, visited=visited, db=db
                    )
                    for sub in sub_itens:
                        items.append(
                            ComposicaoItemResponse(
                                id=sub.id,
                                insumo_filho_id=sub.insumo_filho_id,
                                descricao_filho=sub.descricao_filho,
                                unidade_medida=sub.unidade_medida,
                                quantidade_consumo=sub.quantidade_consumo * comp.quantidade_consumo,
                                custo_unitario=sub.custo_unitario,
                                custo_total=sub.custo_total * comp.quantidade_consumo,
                            )
                        )
                    total += sub_custo * comp.quantidade_consumo
                else:
                    custo_item = comp.quantidade_consumo * filho_prop.custo_unitario
                    items.append(
                        ComposicaoItemResponse(
                            id=comp.id,
                            insumo_filho_id=filho_prop.id,
                            descricao_filho=filho_prop.descricao,
                            unidade_medida=comp.unidade_medida or filho_prop.unidade_medida,
                            quantidade_consumo=comp.quantidade_consumo,
                            custo_unitario=filho_prop.custo_unitario,
                            custo_total=custo_item,
                        )
                    )
                    total += custo_item

        return items, total

    # â”€â”€â”€ Anti-Loop Validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def _detectar_ciclo(
        self,
        pai_id: UUID,
        filho_id: UUID,
        db: AsyncSession,
    ) -> bool:
        """
        BFS to detect if (pai_id â†’ filho_id) would create a cycle in
        PROPRIA compositions (ComposicaoCliente via active VersaoComposicao).
        Only PROPRIAâ†’PROPRIA links can form cycles; BaseTcpo children are leaves.
        """
        if pai_id == filho_id:
            return True

        visited: set[UUID] = set()
        queue: list[UUID] = [filho_id]

        while queue:
            current = queue.pop()
            if current == pai_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            result = await db.execute(
                select(VersaoComposicao).where(
                    VersaoComposicao.item_proprio_id == current,
                    VersaoComposicao.is_ativa.is_(True),
                )
            )
            versao = result.scalar_one_or_none()
            if versao is None:
                continue

            comps_result = await db.execute(
                select(ComposicaoCliente.insumo_proprio_id).where(
                    ComposicaoCliente.versao_id == versao.id,
                    ComposicaoCliente.insumo_proprio_id.isnot(None),
                )
            )
            for (child_id,) in comps_result.fetchall():
                queue.append(child_id)

        return False

    async def adicionar_composicao(
        self,
        pai_id: UUID,
        filho_id: UUID,
        quantidade_consumo: Decimal,
        unidade_medida: str,
        db: AsyncSession,
    ) -> ComposicaoCliente:
        """
        Add a ComposicaoCliente link to the active PROPRIA VersaoComposicao.
        filho_id may point to either a BaseTcpo (â†’ insumo_base_id) or
        an ItemProprio (â†’ insumo_proprio_id). XOR FK is enforced by model constraint.
        """
        propria_repo = ItensPropiosRepository(db)
        pai = await propria_repo.get_active_by_id(pai_id)
        if not pai:
            raise NotFoundError("ItemProprio (pai)", str(pai_id))

        versao_repo = VersaoComposicaoRepository(db)
        versao = await versao_repo.get_versao_ativa(pai_id)
        if versao is None:
            raise ValidationError(
                "Nenhuma versÃ£o ativa de composiÃ§Ã£o encontrada. "
                "Crie uma versÃ£o antes de adicionar componentes."
            )

        base_repo = BaseTcpoRepository(db)
        filho_base: BaseTcpo | None = await base_repo.get_by_id(filho_id)
        filho_proprio: ItemProprio | None = None
        if filho_base is None:
            filho_proprio = await propria_repo.get_active_by_id(filho_id)
            if filho_proprio is None:
                raise NotFoundError("Item (filho)", str(filho_id))
            # Cycle detection only needed for PROPRIA â†’ PROPRIA edges
            if await self._detectar_ciclo(pai_id, filho_id, db):
                raise ValidationError(
                    f"ReferÃªncia circular detectada: adicionar '{filho_proprio.descricao}' "
                    f"a '{pai.descricao}' criaria um loop na composiÃ§Ã£o."
                )

        comp = ComposicaoCliente(
            versao_id=versao.id,
            insumo_base_id=filho_base.id if filho_base else None,
            insumo_proprio_id=filho_proprio.id if filho_proprio else None,
            quantidade_consumo=quantidade_consumo,
            unidade_medida=unidade_medida,
        )
        db.add(comp)
        await db.flush()

        await self.recalcular_custo_pai(pai_id, db)
        logger.info(
            "composicao_adicionada",
            pai_id=str(pai_id),
            filho_id=str(filho_id),
            qtd=str(quantidade_consumo),
        )
        return comp

    # â”€â”€â”€ Price Roll-up â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def recalcular_custo_pai(
        self, item_proprio_id: UUID, db: AsyncSession
    ) -> None:
        """
        Recalculate custo_unitario for a PROPRIA item from its active composition.
        Child cost is custo_base (BaseTcpo) or custo_unitario (ItemProprio).
        Only flushes if the computed total changed.
        """
        propria_repo = ItensPropiosRepository(db)
        item = await propria_repo.get_active_by_id(item_proprio_id)
        if item is None:
            return

        versao_repo = VersaoComposicaoRepository(db)
        versao = await versao_repo.get_versao_ativa(item_proprio_id)
        if versao is None:
            return

        total = Decimal("0")
        base_repo = BaseTcpoRepository(db)
        for comp in versao.itens:
            if comp.insumo_base_id is not None:
                filho_base = comp.insumo_base
                if filho_base is None:
                    filho_base = await base_repo.get_by_id(comp.insumo_base_id)
                if filho_base:
                    total += comp.quantidade_consumo * filho_base.custo_base
            elif comp.insumo_proprio_id is not None:
                filho_prop = comp.insumo_proprio
                if filho_prop is None:
                    filho_prop = await propria_repo.get_active_by_id(comp.insumo_proprio_id)
                if filho_prop:
                    total += comp.quantidade_consumo * filho_prop.custo_unitario

        if total != item.custo_unitario:
            old_val = item.custo_unitario
            item.custo_unitario = total
            await db.flush()
            logger.info(
                "preco_pai_atualizado",
                item_id=str(item.id),
                old=float(old_val),
                new=float(total),
            )

    # â”€â”€â”€ Create / Delete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def create_servico(
        self, data: ServicoCreate, db: AsyncSession
    ) -> ServicoTcpoResponse:
        """Admin ETL path: creates a BaseTcpo entry in referencia.base_tcpo."""
        item = BaseTcpo(
            codigo_origem=data.codigo_origem,
            descricao=data.descricao,
            unidade_medida=data.unidade_medida,
            custo_base=data.custo_unitario,  # ServicoCreate.custo_unitario maps to BaseTcpo.custo_base
            categoria_id=data.categoria_id,
            descricao_tokens=normalize_text(data.descricao),
        )
        db.add(item)
        await db.flush()
        await embedding_sync_service.sync_create_or_update(item.id, db)
        logger.info("base_tcpo_created", id=str(item.id))
        return ServicoTcpoResponse.model_validate(item)

    async def soft_delete_servico(self, servico_id: UUID, db: AsyncSession) -> None:
        """Soft-delete a PROPRIA item only. BaseTcpo is immutable (managed by ETL)."""
        propria_repo = ItensPropiosRepository(db)
        item = await propria_repo.get_active_by_id(servico_id)
        if not item:
            raise NotFoundError("ItemProprio", str(servico_id))
        await propria_repo.soft_delete(item)

    async def compute_all_embeddings(self, db: AsyncSession) -> int:
        return await embedding_sync_service.compute_all_missing(db)

    # â”€â”€â”€ Clone BaseTcpo â†’ ItemProprio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def clonar_composicao(
        self,
        servico_origem_id: UUID,
        cliente_id: UUID,
        codigo_clone: str,
        descricao: str | None,
        criado_por_id: UUID,
        db: AsyncSession,
    ) -> ExplodeComposicaoResponse:
        """
        Clone a BaseTcpo (with its ComposicaoBase children) into a new
        ItemProprio bound to cliente_id. Each ComposicaoBase child becomes a
        ComposicaoCliente row with insumo_base_id set (preserving the reference).
        The clone starts with status_homologacao=PENDENTE.
        """
        base_repo = BaseTcpoRepository(db)
        original = await base_repo.get_with_composicao_base(servico_origem_id)
        if not original:
            raise NotFoundError("BaseTcpo", str(servico_origem_id))

        novo = ItemProprio(
            cliente_id=cliente_id,
            codigo_origem=codigo_clone,
            descricao=descricao if descricao is not None else original.descricao,
            unidade_medida=original.unidade_medida,
            custo_unitario=original.custo_base,
            categoria_id=original.categoria_id,
            status_homologacao=StatusHomologacao.PENDENTE,
            descricao_tokens=normalize_text(descricao if descricao is not None else original.descricao),
        )
        db.add(novo)
        await db.flush()

        nova_versao = VersaoComposicao(
            item_proprio_id=novo.id,
            numero_versao=1,
            is_ativa=True,
            criado_por_id=criado_por_id,
        )
        db.add(nova_versao)
        await db.flush()

        for comp in original.composicoes_pai:
            db.add(
                ComposicaoCliente(
                    versao_id=nova_versao.id,
                    insumo_base_id=comp.insumo_filho_id,
                    insumo_proprio_id=None,
                    quantidade_consumo=comp.quantidade_consumo,
                    unidade_medida=comp.unidade_medida,
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
        Remove a ComposicaoCliente link from the active VersaoComposicao of a PROPRIA item.
        Raises NotFoundError if the link is not in this item's active version.
        """
        propria_repo = ItensPropiosRepository(db)
        pai = await propria_repo.get_active_by_id(pai_id)
        if not pai:
            raise NotFoundError("ItemProprio", str(pai_id))

        versao_repo = VersaoComposicaoRepository(db)
        versao = await versao_repo.get_versao_ativa(pai_id)
        if versao is None:
            raise NotFoundError("VersaoComposicao ativa", str(pai_id))

        result = await db.execute(
            select(ComposicaoCliente).where(
                ComposicaoCliente.id == componente_id,
                ComposicaoCliente.versao_id == versao.id,
            )
        )
        comp = result.scalar_one_or_none()
        if not comp:
            raise NotFoundError("ComposicaoCliente", str(componente_id))

        await db.delete(comp)
        await db.flush()

        await self.recalcular_custo_pai(pai_id, db)
        logger.info(
            "componente_removido",
            pai_id=str(pai_id),
            componente_id=str(componente_id),
        )


servico_catalog_service = ServicoCatalogService()

