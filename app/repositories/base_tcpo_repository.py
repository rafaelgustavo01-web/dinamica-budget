"""
Read-only repository for referencia.base_tcpo — immutable TCPO catalog.
BaseTcpo has no soft-delete (catalog entries are permanent).
All mutation goes through the admin ETL layer, not this repo.
"""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base_tcpo import BaseTcpo
from app.models.composicao_base import ComposicaoBase
from app.models.tcpo_embeddings import TcpoEmbedding
from app.repositories.base_repository import BaseRepository


class BaseTcpoRepository(BaseRepository[BaseTcpo]):
    model = BaseTcpo

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_ids(self, ids: list[UUID]) -> dict[UUID, BaseTcpo]:
        """
        Batch fetch by ID list — O(1) lookup dict, used by Phase 3 semantic search.
        BaseTcpo has no deleted_at; catalog is always live.
        """
        if not ids:
            return {}
        result = await self.db.execute(
            select(BaseTcpo).where(BaseTcpo.id.in_(ids))
        )
        return {s.id: s for s in result.scalars().all()}

    async def list_paginated(
        self,
        q: str | None,
        categoria_id: int | None,
        offset: int,
        limit: int,
    ) -> tuple[list[BaseTcpo], int]:
        """List TCPO catalog with optional text + category filter."""
        base_filter = []
        if categoria_id is not None:
            base_filter.append(BaseTcpo.categoria_id == categoria_id)
        if q:
            base_filter.append(BaseTcpo.descricao.ilike(f"%{q}%"))

        count_result = await self.db.execute(
            select(func.count()).select_from(BaseTcpo).where(*base_filter)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(BaseTcpo)
            .where(*base_filter)
            .order_by(BaseTcpo.codigo_origem)
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def fuzzy_search(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
    ) -> list[tuple[BaseTcpo, float]]:
        """
        Phase 2 fuzzy search via pg_trgm over the full TCPO catalog.
        Returns (item, similarity_score) pairs ordered by score desc.
        """
        stmt = text(
            """
            SELECT s.id, similarity(s.descricao, :query) AS sim_score
            FROM referencia.base_tcpo s
            WHERE similarity(s.descricao, :query) > :threshold
            ORDER BY sim_score DESC
            LIMIT :limit
            """
        )
        result = await self.db.execute(
            stmt, {"query": texto_busca, "threshold": threshold, "limit": limit}
        )
        rows = result.fetchall()
        if not rows:
            return []

        ids = [row[0] for row in rows]
        scores = {row[0]: float(row[1]) for row in rows}

        items_result = await self.db.execute(
            select(BaseTcpo).where(BaseTcpo.id.in_(ids))
        )
        items_map = {s.id: s for s in items_result.scalars().all()}

        return [(items_map[id_], scores[id_]) for id_ in ids if id_ in items_map]

    async def get_with_composicao_base(self, item_id: UUID) -> BaseTcpo | None:
        """
        Load a TCPO item with its full composicao_base children (BOM).
        Used by explode_composicao for the TCPO side of the recursion.
        """
        result = await self.db.execute(
            select(BaseTcpo)
            .options(
                selectinload(BaseTcpo.composicoes_pai).selectinload(
                    ComposicaoBase.insumo_filho
                )
            )
            .where(BaseTcpo.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_without_embeddings(self, limit: int = 100) -> list[BaseTcpo]:
        """
        Returns TCPO items that have no embedding yet.
        Used by EmbeddingSyncService.compute_all_missing.
        """
        result = await self.db.execute(
            select(BaseTcpo)
            .outerjoin(TcpoEmbedding, BaseTcpo.id == TcpoEmbedding.id)
            .where(TcpoEmbedding.id.is_(None))
            .limit(limit)
        )
        return list(result.scalars().all())
