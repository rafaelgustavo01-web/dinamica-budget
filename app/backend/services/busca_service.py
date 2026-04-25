"""
Motor de Busca em Cascata — V3 (dual-schema)

Fluxo:
  Fase 0 (Itens Próprios): Busca pg_trgm restrita a itens PROPRIA do cliente com status APROVADO
  Fase 1 (Associação Direta): Lookup em associacao_inteligente com cliente_id + texto normalizado
                               → se CONSOLIDADA: circuit break imediato
                               → se VALIDADA/SUGERIDA: retorna e fortalece
  Fase 2 (Fuzzy Global): pg_trgm sobre catálogo global TCPO (referencia.base_tcpo)
  Fase 3 (IA Semântica): pgvector cosine similarity

Normalização obrigatória em todas as fases:
  strip → lowercase → remoção de acentos → collapse whitespace

Histórico gravado de forma síncrona antes de retornar a resposta.
O id real do histórico é incluído nos metadados da resposta.
"""

import time
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.ml.embedder import embedder
from backend.ml.vector_search import vector_searcher
from backend.models.enums import OrigemAssociacao, StatusHomologacao, StatusValidacaoAssociacao
from backend.repositories.associacao_repository import AssociacaoRepository, normalize_text
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.historico_repository import HistoricoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.schemas.busca import (
    AssociacaoResponse,
    BuscaMetadados,
    BuscaServicoRequest,
    BuscaServicoResponse,
    CriarAssociacaoRequest,
    ResultadoBusca,
)

logger = get_logger(__name__)


class BuscaService:

    async def buscar(
        self,
        request: BuscaServicoRequest,
        usuario_id: UUID,
        db: AsyncSession,
    ) -> BuscaServicoResponse:
        t0 = time.monotonic()

        # ── Normalização obrigatória ──────────────────────────────────────────
        texto_norm = normalize_text(request.texto_busca)

        assoc_repo = AssociacaoRepository(db)
        base_repo = BaseTcpoRepository(db)
        proprios_repo = ItensPropiosRepository(db)

        # ─────────────────────────────────────────────────────────────────────
        # FASE 0: Itens Próprios do Cliente (PROPRIA + APROVADO)
        # Requer cliente_id — skip quando busca genérica
        # ─────────────────────────────────────────────────────────────────────
        if request.cliente_id is not None:
            resultado = await self._fase0_itens_proprios(
                cliente_id=request.cliente_id,
                texto_norm=texto_norm,
                threshold=request.threshold_score,
                limit=request.limite_resultados,
                proprios_repo=proprios_repo,
            )
            if resultado:
                return await self._build_response(
                    texto_busca=request.texto_busca,
                    resultados=resultado,
                    t0=t0,
                    cliente_id=request.cliente_id,
                    usuario_id=usuario_id,
                    db=db,
                )
            logger.info(
                "busca_fase_0_sem_resultados",
                cliente_id=str(request.cliente_id),
                texto=texto_norm,
            )
        else:
            logger.info("busca_sem_cliente_skip_fase0", texto=texto_norm)

        # ─────────────────────────────────────────────────────────────────────
        # FASE 1: Associação Direta (associacao_inteligente)
        # Requer cliente_id — skip quando busca genérica
        # ─────────────────────────────────────────────────────────────────────
        if request.cliente_id is not None:
            resultado, associacao = await self._fase1_associacao(
                cliente_id=request.cliente_id,
                texto_norm=texto_norm,
                assoc_repo=assoc_repo,
                base_repo=base_repo,
            )
            if resultado:
                if associacao:
                    await assoc_repo.fortalecer(associacao)
                return await self._build_response(
                    texto_busca=request.texto_busca,
                    resultados=resultado,
                    t0=t0,
                    cliente_id=request.cliente_id,
                    usuario_id=usuario_id,
                    db=db,
                )
            logger.info(
                "busca_fase_1_sem_resultados",
                cliente_id=str(request.cliente_id),
                texto=texto_norm,
            )
        else:
            logger.info("busca_sem_cliente_skip_fase1", texto=texto_norm)

        # ─────────────────────────────────────────────────────────────────────
        # FASE 2: Fuzzy Global (pg_trgm — catálogo TCPO)
        # ─────────────────────────────────────────────────────────────────────
        resultado = await self._fase2_fuzzy(
            texto_busca=texto_norm,
            threshold=request.threshold_score,
            limit=request.limite_resultados,
            base_repo=base_repo,
        )
        if resultado:
            return await self._build_response(
                texto_busca=request.texto_busca,
                resultados=resultado,
                t0=t0,
                cliente_id=request.cliente_id,
                usuario_id=usuario_id,
                db=db,
            )

        # ─────────────────────────────────────────────────────────────────────
        # FASE 3: IA Semântica (pgvector)
        # ─────────────────────────────────────────────────────────────────────
        resultado = await self._fase3_semantica(
            texto_busca=texto_norm,
            threshold=request.threshold_score,
            limit=request.limite_resultados,
            db=db,
            base_repo=base_repo,
        )

        return await self._build_response(
            texto_busca=request.texto_busca,
            resultados=resultado,
            t0=t0,
            cliente_id=request.cliente_id,
            usuario_id=usuario_id,
            db=db,
        )

    # ─── Fase 0: Itens Próprios do Cliente ───────────────────────────────────

    async def _fase0_itens_proprios(
        self,
        cliente_id: UUID,
        texto_norm: str,
        threshold: float,
        limit: int,
        proprios_repo: ItensPropiosRepository,
    ) -> list[ResultadoBusca] | None:
        rows = await proprios_repo.fuzzy_search_scoped(
            texto_busca=texto_norm,
            threshold=threshold,
            limit=limit,
            cliente_id=cliente_id,
            status_homologacao=StatusHomologacao.APROVADO,
        )
        if not rows:
            return None

        logger.info("fase0_proprios_hit", cliente_id=str(cliente_id), count=len(rows))
        return [
            ResultadoBusca(
                id_tcpo=s.id,
                codigo_origem=s.codigo_origem,
                descricao=s.descricao,
                unidade=s.unidade_medida,
                custo_unitario=float(s.custo_unitario),
                score=round(score, 4),
                score_confianca=round(score, 4),
                origem_match="PROPRIA_CLIENTE",
                status_homologacao=s.status_homologacao.value,
            )
            for s, score in rows
        ]

    # ─── Fase 1: Associação Direta ────────────────────────────────────────────

    async def _fase1_associacao(
        self,
        cliente_id: UUID,
        texto_norm: str,
        assoc_repo: AssociacaoRepository,
        base_repo: BaseTcpoRepository,
    ) -> tuple[list[ResultadoBusca] | None, object]:
        assoc = await assoc_repo.find_by_cliente_and_text(
            cliente_id=cliente_id,
            texto_normalizado=texto_norm,
        )
        if not assoc:
            return None, None

        # Associations always point to referencia.base_tcpo
        servico = await base_repo.get_by_id(assoc.item_referencia_id)
        if not servico:
            return None, None

        # Only circuit-break immediately for CONSOLIDADA; return for all matches
        if assoc.status_validacao == StatusValidacaoAssociacao.CONSOLIDADA:
            logger.info("fase1_consolidada_circuit_break", servico_id=str(servico.id))
        else:
            logger.info(
                "fase1_associacao_hit",
                status=assoc.status_validacao,
                freq=assoc.frequencia_uso,
            )

        return [
            ResultadoBusca(
                id_tcpo=servico.id,
                codigo_origem=servico.codigo_origem,
                descricao=servico.descricao,
                unidade=servico.unidade_medida,
                custo_unitario=float(servico.custo_base),
                score=1.0,
                score_confianca=float(assoc.confiabilidade_score or 1.0),
                origem_match="ASSOCIACAO_DIRETA",
                status_homologacao="APROVADO",  # BaseTcpo is always approved
            )
        ], assoc

    # ─── Fase 2: Fuzzy Global ─────────────────────────────────────────────────

    async def _fase2_fuzzy(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
        base_repo: BaseTcpoRepository,
    ) -> list[ResultadoBusca] | None:
        rows = await base_repo.fuzzy_search(
            texto_busca=texto_busca,
            threshold=threshold,
            limit=limit,
        )
        if not rows:
            return None

        logger.info("fase2_fuzzy_hit", count=len(rows))
        return [
            ResultadoBusca(
                id_tcpo=s.id,
                codigo_origem=s.codigo_origem,
                descricao=s.descricao,
                unidade=s.unidade_medida,
                custo_unitario=float(s.custo_base),
                score=round(score, 4),
                score_confianca=round(score, 4),
                origem_match="FUZZY",
                status_homologacao="APROVADO",  # BaseTcpo is always approved
            )
            for s, score in rows
        ]

    # ─── Fase 3: IA Semântica ─────────────────────────────────────────────────

    async def _fase3_semantica(
        self,
        texto_busca: str,
        threshold: float,
        limit: int,
        db: AsyncSession,
        base_repo: BaseTcpoRepository,
    ) -> list[ResultadoBusca]:
        if not embedder.ready:
            logger.warning("fase3_skipped_embedder_not_ready")
            return []

        query_vector = embedder.encode(texto_busca)
        candidates = await vector_searcher.search(
            query_vector=query_vector,
            db=db,
            threshold=threshold,
            limit=limit,
        )

        if not candidates:
            return []

        # Batch load — single query for all candidates, eliminates N+1
        candidate_ids = [c[0] for c in candidates]
        servicos_map = await base_repo.get_by_ids(candidate_ids)
        scores = {c[0]: c[1] for c in candidates}

        results = []
        for servico_id in candidate_ids:
            servico = servicos_map.get(servico_id)
            if not servico:
                continue
            score = scores[servico_id]
            results.append(
                ResultadoBusca(
                    id_tcpo=servico.id,
                    codigo_origem=servico.codigo_origem,
                    descricao=servico.descricao,
                    unidade=servico.unidade_medida,
                    custo_unitario=float(servico.custo_base),
                    score=round(score, 4),
                    score_confianca=round(score, 4),
                    origem_match="IA_SEMANTICA",
                    status_homologacao="APROVADO",  # BaseTcpo is always approved
                )
            )

        logger.info("fase3_semantica_hit", count=len(results))
        return results

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _build_response(
        self,
        texto_busca: str,
        resultados: list[ResultadoBusca],
        t0: float,
        cliente_id: UUID | None,
        usuario_id: UUID,
        db: AsyncSession,
    ) -> BuscaServicoResponse:
        elapsed = int((time.monotonic() - t0) * 1000)

        # Persist historico synchronously — real id returned in response
        historico_repo = HistoricoRepository(db)
        historico = await historico_repo.create_registro(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            texto_busca=texto_busca,
        )

        return BuscaServicoResponse(
            texto_buscado=texto_busca,
            resultados=resultados,
            metadados=BuscaMetadados(
                tempo_processamento_ms=elapsed,
                id_historico_busca=historico.id,
            ),
        )

    # ─── Criar Associação ─────────────────────────────────────────────────────

    async def criar_associacao(
        self,
        request: CriarAssociacaoRequest,
        usuario_id: UUID,
        db: AsyncSession,
    ) -> AssociacaoResponse:
        base_repo = BaseTcpoRepository(db)
        assoc_repo = AssociacaoRepository(db)
        historico_repo = HistoricoRepository(db)

        # Validate historico exists and belongs to the same client
        historico = await historico_repo.get_by_id_and_cliente(
            id=request.id_historico_busca,
            cliente_id=request.cliente_id,
        )
        if not historico:
            raise ValidationError(
                "Histórico de busca não encontrado ou não pertence ao cliente informado."
            )

        # Associations point to TCPO reference items only
        servico = await base_repo.get_by_id(request.id_tcpo_selecionado)
        if not servico:
            raise NotFoundError("BaseTcpo", str(request.id_tcpo_selecionado))

        associacao = await assoc_repo.upsert_associacao(
            cliente_id=request.cliente_id,
            texto_busca_original=request.texto_busca_original,
            item_referencia_id=request.id_tcpo_selecionado,
            origem=OrigemAssociacao.MANUAL_USUARIO,
            confiabilidade_score=Decimal("1.00"),
        )

        logger.info(
            "associacao_criada_ou_fortalecida",
            id=str(associacao.id),
            freq=associacao.frequencia_uso,
            status=associacao.status_validacao,
            usuario_id=str(usuario_id),
        )

        return AssociacaoResponse(
            status="ok",
            mensagem=f"Associação {associacao.status_validacao.value} (frequência: {associacao.frequencia_uso}).",
            id_associacao=associacao.id,
        )


busca_service = BuscaService()

