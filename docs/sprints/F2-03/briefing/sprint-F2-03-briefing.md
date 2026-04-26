# Sprint F2-03 — Briefing

**Sprint:** F2-03
**Titulo:** Tela de Revisao de Match
**Worker:** claude-sonnet-4-6 (Claude Code)
**Status:** TODO
**Data:** 2026-04-25

---

## Objetivo

Substituir o match automatico por uma tela de revisao onde o orcamentista confirma, substitui ou rejeita cada sugestao antes de gerar a CPU. Inclui backend (2 endpoints) e frontend completo (MatchReviewPage + componentes).

## Criterios de Aceite

- GET /propostas/{id}/pq/itens retorna lista de PqItems com status/confianca
- PATCH /propostas/{id}/pq/itens/{item_id}/match aceita acao confirmar/substituir/rejeitar
- Pagina /propostas/:id/match-review exibe tabela com barra de progresso
- Botoes de acao por linha: confirmar (verde), substituir (abre dialogo de busca), rejeitar (vermelho)
- Botao "Revisar Match" visivel em ProposalDetailPage e ProposalImportPage apos match
- npx tsc --noEmit sem erros
- python -m pytest backend/tests/ com 110+ PASS, 0 FAIL

## Plano

Arquivo: `docs/sprints/F2-03/plans/2026-04-25-match-review.md`

7 tasks, da mais rapida a mais complexa:
1. Schemas PqItemResponse + PqMatchConfirmarRequest
2. GET /pq/itens + PATCH /pq/itens/{id}/match
3. Tipos e metodos na proposalsApi
4. ServicoPickerDialog (dialogo de busca para substituicao)
5. MatchItemRow (linha de tabela com acoes)
6. MatchReviewPage + rota
7. Botoes de acesso nas paginas existentes

## Contexto tecnico

- Backend: `app/backend/api/v1/endpoints/pq_importacao.py` — router existente com prefixo `/propostas/{id}/pq`
- PqItem model: `app/backend/models/proposta.py` linhas 95-132
- StatusMatch enum: PENDENTE, BUSCANDO, SUGERIDO, CONFIRMADO, MANUAL, SEM_MATCH
- PqItemRepository: `app/backend/repositories/pq_item_repository.py` — ja tem `list_by_proposta`, `update_match`, `update_status`
- Frontend: MUI v6, TanStack Query v5, React Router v6
- searchApi existente: `app/frontend/src/shared/services/api/searchApi.ts`

## Dependencias

- F2-01 DONE (layout configuravel)
- F2-02 TESTED (explosao recursiva — nao bloqueia esta sprint)
- S-10 DONE (PqMatchService, StatusMatch, PqItemRepository)
