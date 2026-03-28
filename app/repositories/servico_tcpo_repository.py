from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.composicao_tcpo import ComposicaoTcpo
from app.models.enums import OrigemItem, StatusHomologacao
from app.models.servico_tcpo import ServicoTcpo
from app.models.versao_composicao import VersaoComposicao
from app.repositories.base_repository import BaseRepository


class ServicoTcpoRepository(BaseRepository[ServicoTcpo]):
    model = ServicoTcpo

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_active_by_id(self, id: UUID) -> ServicoTcpo | None:
        result = await self.db.execute(
            select(ServicoTcpo).where(
                ServicoTcpo.id == id,
                ServicoTcpo.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_ids(self, ids: list[UUID]) -> dict[UUID, ServicoTcpo]:
        """
        Batch fetch — eliminates N+1 in Phase 3 semantic search.
        Returns dict keyed by id for O(1) lookup after fetch.
        """
        if not ids:
            return {}
        result = await self.db.execute(
            select(ServicoTcpo).where(
                ServicoTcpo.id.in_(ids),
                ServicoTcpo.deleted_at.is_(None),
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
    ) -> tuple[list[ServicoTcpo], int]:
        base_filter = [ServicoTcpo.deleted_at.is_(None)]
        if categoria_id is not None:
            base_filter.append(ServicoTcpo.categoria_id == categoria_id)
        if q:
            base_filter.append(ServicoTcpo.descricao.ilike(f"%{q}%"))
        if cliente_id is not None:
            base_filter.append(ServicoTcpo.cliente_id == cliente_id)
        if status_homologacao is not None:
            base_filter.append(ServicoTcpo.status_homologacao == status_homologacao)

        count_result = await self.db.execute(
            select(func.count()).select_from(ServicoTcpo).where(*base_filter)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(ServicoTcpo)
            .where(*base_filter)
            .order_by(ServicoTcpo.codigo_origem)
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def fuzzy_search_scoped(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
        cliente_id: UUID | None,
        origem: OrigemItem,
        status_homologacao: StatusHomologacao,
    ) -> list[tuple[ServicoTcpo, float]]:
        """
        Phase 0 and Phase 2 fuzzy search via pg_trgm.
        Mandatory filters: deleted_at IS NULL + status_homologacao + origem.
        For Phase 0: also filters by cliente_id (client's own items).
        For Phase 2: cliente_id=None queries global TCPO catalog.
        """
        params: dict = {
            "query": texto_busca,
            "threshold": threshold,
            "limit": limit,
            "origem": origem.value,
            "status_hom": status_homologacao.value,
        }

        if cliente_id is not None:
            cliente_filter = "AND s.cliente_id = :cliente_id"
            params["cliente_id"] = str(cliente_id)
        else:
            cliente_filter = "AND s.cliente_id IS NULL"

        stmt = text(
            f"""
            SELECT s.id, similarity(s.descricao, :query) AS sim_score
            FROM servico_tcpo s
            WHERE s.deleted_at IS NULL
              AND s.origem = :origem
              AND s.status_homologacao = :status_hom
              {cliente_filter}
              AND similarity(s.descricao, :query) > :threshold
            ORDER BY sim_score DESC
            LIMIT :limit
            """
        )
        result = await self.db.execute(stmt, params)
        rows = result.fetchall()

        if not rows:
            return []

        ids = [row[0] for row in rows]
        scores = {row[0]: float(row[1]) for row in rows}

        servicos_result = await self.db.execute(
            select(ServicoTcpo).where(ServicoTcpo.id.in_(ids))
        )
        servicos = {s.id: s for s in servicos_result.scalars().all()}

        return [(servicos[id_], scores[id_]) for id_ in ids if id_ in servicos]

    async def get_with_composicao(self, service_id: UUID) -> ServicoTcpo | None:
        result = await self.db.execute(
            select(ServicoTcpo)
            .options(
                selectinload(ServicoTcpo.composicoes_pai).selectinload(
                    ComposicaoTcpo.insumo_filho
                )
            )
            .where(ServicoTcpo.id == service_id, ServicoTcpo.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_pendentes_homologacao(
        self, cliente_id: UUID, offset: int, limit: int
    ) -> tuple[list[ServicoTcpo], int]:
        filters = [
            ServicoTcpo.deleted_at.is_(None),
            ServicoTcpo.cliente_id == cliente_id,
            ServicoTcpo.status_homologacao == StatusHomologacao.PENDENTE,
        ]
        count_result = await self.db.execute(
            select(func.count()).select_from(ServicoTcpo).where(*filters)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(ServicoTcpo)
            .where(*filters)
            .order_by(ServicoTcpo.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def list_catalogo_visivel(
        self,
        cliente_id: UUID | None,
        q: str | None,
        categoria_id: int | None,
        offset: int,
        limit: int,
    ) -> tuple[list[ServicoTcpo], int]:
        """
        Returns the visible catalog for a given client:
          - Global TCPO items (cliente_id IS NULL, status = APROVADO)
          - Client's own PROPRIA items (cliente_id = :id, status = APROVADO)
        If cliente_id is None (admin scenario), returns all approved active items.
        """
        from sqlalchemy import or_

        base_filter = [
            ServicoTcpo.deleted_at.is_(None),
            ServicoTcpo.status_homologacao == StatusHomologacao.APROVADO,
        ]

        if cliente_id is not None:
            base_filter.append(
                or_(
                    ServicoTcpo.cliente_id.is_(None),          # global TCPO
                    ServicoTcpo.cliente_id == cliente_id,      # client's own
                )
            )

        if categoria_id is not None:
            base_filter.append(ServicoTcpo.categoria_id == categoria_id)
        if q:
            base_filter.append(ServicoTcpo.descricao.ilike(f"%{q}%"))

        count_result = await self.db.execute(
            select(func.count()).select_from(ServicoTcpo).where(*base_filter)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(ServicoTcpo)
            .where(*base_filter)
            .order_by(ServicoTcpo.codigo_origem)
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def get_versao_ativa(
        self, servico_id: UUID, cliente_id: UUID | None
    ) -> VersaoComposicao | None:
        """
        Returns the active VersaoComposicao for a servico, with priority:
          1. Client's PROPRIA active version (if cliente_id provided)
          2. Global TCPO active version (fallback)
        """
        if cliente_id is not None:
            result = await self.db.execute(
                select(VersaoComposicao)
                .options(
                    selectinload(VersaoComposicao.itens).selectinload(
                        ComposicaoTcpo.insumo_filho
                    )
                )
                .where(
                    VersaoComposicao.servico_id == servico_id,
                    VersaoComposicao.cliente_id == cliente_id,
                    VersaoComposicao.is_ativa.is_(True),
                )
                .limit(1)
            )
            versao = result.scalar_one_or_none()
            if versao:
                return versao

        # Fallback: global TCPO version
        result = await self.db.execute(
            select(VersaoComposicao)
            .options(
                selectinload(VersaoComposicao.itens).selectinload(
                    ComposicaoTcpo.insumo_filho
                )
            )
            .where(
                VersaoComposicao.servico_id == servico_id,
                VersaoComposicao.cliente_id.is_(None),
                VersaoComposicao.is_ativa.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_versoes(
        self, servico_id: UUID, cliente_id: UUID | None
    ) -> list[VersaoComposicao]:
        """Lists all versions visible to the client (TCPO global + client's PROPRIA)."""
        from sqlalchemy import or_

        filters = [VersaoComposicao.servico_id == servico_id]
        if cliente_id is not None:
            filters.append(
                or_(
                    VersaoComposicao.cliente_id.is_(None),
                    VersaoComposicao.cliente_id == cliente_id,
                )
            )
        else:
            filters.append(VersaoComposicao.cliente_id.is_(None))

        result = await self.db.execute(
            select(VersaoComposicao)
            .where(*filters)
            .order_by(VersaoComposicao.numero_versao)
        )
        return list(result.scalars().all())

    async def get_without_embeddings(self, limit: int = 100) -> list[ServicoTcpo]:
        from app.models.tcpo_embeddings import TcpoEmbedding

        result = await self.db.execute(
            select(ServicoTcpo)
            .outerjoin(TcpoEmbedding, ServicoTcpo.id == TcpoEmbedding.id)
            .where(ServicoTcpo.deleted_at.is_(None), TcpoEmbedding.id.is_(None))
            .limit(limit)
        )
        return list(result.scalars().all())
