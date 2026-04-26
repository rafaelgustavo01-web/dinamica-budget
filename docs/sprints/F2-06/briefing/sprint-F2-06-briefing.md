# Sprint F2-06 — Briefing

**Sprint:** F2-06
**Titulo:** UX Complementar — Edicao de PQ, Filtros, Duplicacao
**Worker:** claude-sonnet-4-6 (Claude Code)
**Status:** TODO
**Data:** 2026-04-26

---

## Objetivo

Fechar fluxos pos-importacao que hoje exigem retrabalho manual:
- **Edicao de PqItem** apos upload (descricao/qtd/unidade/observacao) com tabela inline editavel
- **Filtros na lista de propostas**: status, periodo (data inicial/final), busca textual em codigo/titulo
- **Duplicacao de proposta** como base para nova (clona PqItens resetando match_status para PENDENTE)

Foco majoritariamente frontend (3 componentes novos + 3 paginas tocadas) com 3 endpoints atomicos de apoio.

## Criterios de Aceite

- PATCH /propostas/{id}/pq/itens/{item_id} aceita atualizacao parcial e persiste
- POST /propostas/{id}/duplicar cria nova proposta em RASCUNHO, clona PqItens com match_status=PENDENTE
- GET /propostas/ aceita params: status, data_inicial, data_final, q
- Frontend: tabela editavel inline em ProposalImportPage com botoes editar/salvar/cancelar
- Frontend: barra de filtros em ProposalsListPage com debounce de 300ms na busca
- Frontend: dialog de confirmacao para duplicacao com navegacao para proposta nova
- npx tsc --noEmit sem erros
- python -m pytest backend/tests/ com 130+ PASS, 0 FAIL

## Plano

Arquivo: `docs/sprints/F2-06/plans/2026-04-26-ux-complementar.md`

10 tasks:
1. Backend schema PqItemUpdateRequest + repo.update_dados
2. Backend endpoint PATCH /pq/itens/{item_id}
3. Backend duplicar_proposta (service + endpoint)
4. Backend filtros em GET /propostas (repo + endpoint)
5. Frontend proposalsApi (3 metodos novos)
6. Frontend PqItensEditableTable
7. Frontend ProposalFiltersBar + integracao em ProposalsListPage
8. Frontend DuplicarPropostaDialog + botao em ProposalsTable
9. Wire PqItensEditableTable em ProposalImportPage
10. Validacao final

## Contexto tecnico

- Backend reutiliza: `PqItemRepository`, `PropostaRepository`, `PropostaService` (extender, nao reescrever)
- Frontend reutiliza: `proposalsApi.listPqItens` (ja existe, vem de F2-03), padrao TanStack Query
- Geracao de codigo na duplicacao: reusar logica de `count_by_code_prefix` ja existente em `PropostaRepository`
- Status enum no frontend ja exportado: `StatusProposta` em `proposalsApi.ts`

## Dependencias

- F2-03 TESTED (PqItem editavel + lista de match)
- Sem conflito de arquivos com F2-05 (mexe em export, nao em pq)
- Conflito leve com F2-07: ambas mexem em `proposalsApi.ts` — coordenar imports/tipos

## Atencao especial (Claude Code)

- Duplicacao NAO clona `PropostaItem` (CPU) nem composicoes — apenas `PqItem`. Usuario regera via match -> CPU.
- Filtros devem ser combinaveis (status AND periodo AND busca) — nao excludentes
- Tabela editavel: validacao client-side antes de submit (qtd >= 0, descricao nao vazia)
- Debounce de busca: usar `useEffect` + `setTimeout`, nao adicionar lib nova
- Encoding: manter ASCII em codigo de teste pra evitar mojibake (sem caracteres especiais em strings literais)
