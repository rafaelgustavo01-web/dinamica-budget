"""
CRUD + governance repository for operacional.itens_proprios.
Client-owned items with soft-delete and homologation workflow.
"""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.composicao_cliente import ComposicaoCliente
from app.models.enums import StatusHomologacao
from app.models.itens_proprios import ItemProprio
from app.models.versao_composicao import VersaoComposicao
from app.repositories.base_repository import BaseRepository


class ItensPropiosRepository(BaseRepository[ItemProprio]):
    model = ItemProprio

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_active_by_id(self, id: UUID) -> ItemProprio | None:
        """Fetch by ID, respecting soft-delete."""
        result = await self.db.execute(
            select(ItemProprio).where(
                ItemProprio.id == id,
                ItemProprio.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_ids(self, ids: list[UUID]) -> dict[UUID, ItemProprio]:
        """Batch fetch, soft-delete aware. Returns dict keyed by id."""
        if not ids:
            return {}
        result = await self.db.execute(
            select(ItemProprio).where(
                ItemProprio.id.in_(ids),
                ItemProprio.deleted_at.is_(None),
            )
        )
        return {s.id: s for s in result.scalars().all()}

    async def list_paginated(
        self,
        q: str | None,
        categoria_id: int | None,
        offset: int,
        limit: int,
        cliente_id: UUID | None = None,
        status_homologacao: StatusHomologacao | None = None,
    ) -> tuple[list[ItemProprio], int]:
        """Paginated list with optional filters. Always excludes soft-deleted items."""
        base_filter = [ItemProprio.deleted_at.is_(None)]
        if categoria_id is not None:
            base_filter.append(ItemProprio.categoria_id == categoria_id)
        if q:
            base_filter.append(ItemProprio.descricao.ilike(f"%{q}%"))
        if cliente_id is not None:
            base_filter.append(ItemProprio.cliente_id == cliente_id)
        if status_homologacao is not None:
            base_filter.append(ItemProprio.status_homologacao == status_homologacao)

        count_result = await self.db.execute(
            select(func.count()).select_from(ItemProprio).where(*base_filter)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(ItemProprio)
            .where(*base_filter)
            .order_by(ItemProprio.codigo_origem)
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def fuzzy_search_scoped(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
        cliente_id: UUID,
        status_homologacao: StatusHomologacao,
    ) -> list[tuple[ItemProprio, float]]:
        """
        Phase 0 fuzzy search via pg_trgm scoped to a single client.
        Only searches items with the specified status (typically APROVADO).
        """
        stmt = text(
            """
            SELECT s.id, similarity(s.descricao, :query) AS sim_score
            FROM operacional.itens_proprios s
            WHERE s.deleted_at IS NULL
              AND s.cliente_id = :cliente_id
              AND s.status_homologacao = :status_hom
              AND similarity(s.descricao, :query) > :threshold
            ORDER BY sim_score DESC
            LIMIT :limit
            """
        )
        result = await self.db.execute(
            stmt,
            {
                "query": texto_busca,
                "threshold": threshold,
                "limit": limit,
                "cliente_id": str(cliente_id),
                "status_hom": status_homologacao.value,
            },
        )
        rows = result.fetchall()
        if not rows:
            return []

        ids = [row[0] for row in rows]
        scores = {row[0]: float(row[1]) for row in rows}

        items_result = await self.db.execute(
            select(ItemProprio).where(ItemProprio.id.in_(ids))
        )
        items_map = {s.id: s for s in items_result.scalars().all()}

        return [(items_map[id_], scores[id_]) for id_ in ids if id_ in items_map]

    async def get_with_composicao(self, item_id: UUID) -> ItemProprio | None:
        """
        Load an item with its active VersaoComposicao and all ComposicaoCliente items.
        Eagerly loads the insumo_base and insumo_proprio of each component.
        """
        result = await self.db.execute(
            select(ItemProprio)
            .options(
                selectinload(ItemProprio.versoes)
                .selectinload(VersaoComposicao.itens)
                .selectinload(ComposicaoCliente.insumo_base),
                selectinload(ItemProprio.versoes)
                .selectinload(VersaoComposicao.itens)
                .selectinload(ComposicaoCliente.insumo_proprio),
            )
            .where(ItemProprio.id == item_id, ItemProprio.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_pendentes_homologacao(
        self, cliente_id: UUID, offset: int, limit: int
    ) -> tuple[list[ItemProprio], int]:
        """Admin workflow: all items awaiting approval for a given client."""
        filters = [
            ItemProprio.deleted_at.is_(None),
            ItemProprio.cliente_id == cliente_id,
            ItemProprio.status_homologacao == StatusHomologacao.PENDENTE,
        ]
        count_result = await self.db.execute(
            select(func.count()).select_from(ItemProprio).where(*filters)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(ItemProprio)
            .where(*filters)
            .order_by(ItemProprio.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def list_catalogo_visivel(
        self,
        cliente_id: UUID,
        q: str | None,
        categoria_id: int | None,
        offset: int,
        limit: int,
    ) -> tuple[list[ItemProprio], int]:
        """
        Client's approved PROPRIA items visible in the catalog.
        The service layer merges these with BaseTcpo items for the full catalog view.
        """
        base_filter = [
            ItemProprio.deleted_at.is_(None),
            ItemProprio.cliente_id == cliente_id,
            ItemProprio.status_homologacao == StatusHomologacao.APROVADO,
        ]
        if categoria_id is not None:
            base_filter.append(ItemProprio.categoria_id == categoria_id)
        if q:
            base_filter.append(ItemProprio.descricao.ilike(f"%{q}%"))

        count_result = await self.db.execute(
            select(func.count()).select_from(ItemProprio).where(*base_filter)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(ItemProprio)
            .where(*base_filter)
            .order_by(ItemProprio.codigo_origem)
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def soft_delete(self, item: ItemProprio) -> None:
        """Mark item as deleted. Caller must commit the transaction."""
        from datetime import UTC, datetime

        item.deleted_at = datetime.now(UTC)
        await self.db.flush()
