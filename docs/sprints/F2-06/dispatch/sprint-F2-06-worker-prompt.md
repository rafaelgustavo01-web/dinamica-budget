# Worker Prompt — Sprint F2-06

**Para:** Claude Code (claude-sonnet-4-6)
**Modo:** BUILD / Always Proceed
**Sprint:** F2-06 — UX Complementar (Edicao PQ, Filtros, Duplicacao)
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget

---

Voce e o worker da Sprint F2-06. Implemente o plano completo em `docs/sprints/F2-06/plans/2026-04-26-ux-complementar.md` do inicio ao fim sem pausas.

## Por que voce foi escolhido

Esta sprint tem maior superficie de UI/UX entre as 3 ativas:
- 3 componentes React novos com logica de estado nao-trivial (tabela inline editavel, barra de filtros com debounce, modal de duplicacao)
- 3 paginas tocadas (List, Import, plus reuso de Table)
- Backend e suporte minimo (3 endpoints atomicos)

Sua especialidade em React + MUI + TanStack Query e ideal para tabela editavel inline com otimismo + invalidate, debounce de busca e fluxo de duplicacao com navegacao.

## Instrucoes de execucao

1. Leia o briefing em `docs/sprints/F2-06/briefing/sprint-F2-06-briefing.md`
2. Leia o plano em `docs/sprints/F2-06/plans/2026-04-26-ux-complementar.md`
3. Execute cada task em ordem, commitando apos cada uma
4. Apos cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
5. Apos cada task de frontend: `cd app/frontend && npx tsc --noEmit`
6. Ao concluir TODAS as tasks: crie
   - `docs/sprints/F2-06/technical-review/technical-review-2026-04-26-f2-06.md`
   - `docs/sprints/F2-06/walkthrough/done/walkthrough-F2-06.md`
   - Atualize status do sprint para TESTED em `docs/shared/governance/BACKLOG.md`

## Atencao especial

- **Duplicacao NAO clona PropostaItem (CPU)** — apenas PqItens, resetando `match_status=PENDENTE` e limpando `servico_match_id/servico_match_tipo`. Usuario regera CPU depois.
- **Filtros sao combinaveis** (status AND periodo AND busca) — nao excludentes
- **Debounce de busca**: usar `useEffect` + `setTimeout` (300ms), sem adicionar lib nova
- **Validacao client-side** na tabela editavel: `quantidade >= 0` e `descricao.trim().length > 0` antes de submit
- **Geracao de codigo na duplicacao**: reusar `count_by_code_prefix` ja existente em `PropostaRepository`. NAO criar logica nova.
- **Conflito de arquivos com F2-07**: ambos tocam `proposalsApi.ts`. Coordene imports — adicione tipos novos ao final do arquivo, sem reescrever exports existentes.
- **Encoding**: ASCII puro em strings de teste para evitar mojibake

## Criterios de conclusao

- 130+ PASS, 0 FAIL no pytest
- 0 erros no tsc --noEmit
- Todos os 10 tasks com checkbox marcado
- Documentos technical-review e walkthrough criados
- BACKLOG atualizado para TESTED

## Diretorio de trabalho

```
app/backend/schemas/proposta.py
app/backend/repositories/pq_item_repository.py
app/backend/repositories/proposta_repository.py
app/backend/services/proposta_service.py
app/backend/api/v1/endpoints/pq_importacao.py
app/backend/api/v1/endpoints/propostas.py
app/backend/tests/unit/test_pq_item_edit.py
app/backend/tests/unit/test_proposta_duplicar.py
app/backend/tests/unit/test_proposta_filtros.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/components/PqItensEditableTable.tsx
app/frontend/src/features/proposals/components/ProposalFiltersBar.tsx
app/frontend/src/features/proposals/components/DuplicarPropostaDialog.tsx
app/frontend/src/features/proposals/pages/ProposalImportPage.tsx
app/frontend/src/features/proposals/pages/ProposalsListPage.tsx
app/frontend/src/features/proposals/components/ProposalsTable.tsx
```

## Commits esperados (sequencia minima)

1. `feat(f2-06): add PqItemUpdateRequest schema and update_dados repo method`
2. `feat(f2-06): add PATCH /pq/itens/{item_id} endpoint`
3. `feat(f2-06): add duplicar_proposta service and POST /propostas/{id}/duplicar`
4. `feat(f2-06): add filtros (status/periodo/q) to GET /propostas`
5. `feat(f2-06): add updatePqItem/duplicarProposta/listFilters to proposalsApi`
6. `feat(f2-06): add PqItensEditableTable with inline edit`
7. `feat(f2-06): add ProposalFiltersBar with debounced search`
8. `feat(f2-06): add DuplicarPropostaDialog and Duplicar action in ProposalsTable`
9. `feat(f2-06): wire PqItensEditableTable into ProposalImportPage`
10. `docs(f2-06): add technical-review and walkthrough, handoff to QA`
