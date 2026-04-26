# Technical Feedback — F2-06 (QA Review)

## Sprint
F2-06 — UX Complementar (Edição de PQ, Filtros, Duplicação)

## Data
2026-04-26

## QA
Amazon Q (revisão documental)

## Status
**ACCEPTED → DONE**

## Verificação QA

| Item | Resultado |
|---|---|
| Walkthrough | `docs/sprints/F2-06/walkthrough/done/walkthrough-F2-06.md` |
| Technical Review | `docs/sprints/F2-06/technical-review/technical-review-2026-04-26-f2-06.md` |
| Testes unitários | `143 passed, 0 failed` |
| TypeScript | `0 erros (npx tsc --noEmit)` |

## Critérios de Aceite

- [x] `PATCH /pq/itens/{item_id}` aceita atualização parcial e persiste
- [x] `POST /propostas/{id}/duplicar` cria nova proposta em RASCUNHO, clona PqItens com `match_status=PENDENTE`
- [x] `GET /propostas/` aceita params: `status`, `data_inicial`, `data_final`, `q`
- [x] Frontend: tabela editável inline em `ProposalImportPage` com botões editar/salvar/cancelar
- [x] Frontend: barra de filtros em `ProposalsListPage` com debounce de 300ms na busca
- [x] Frontend: dialog de confirmação para duplicação com navegação para proposta nova
- [x] `npx tsc --noEmit` sem erros
- [x] `python -m pytest backend/tests/` com 143+ PASS, 0 FAIL

## Observações

- Bug de debounce identificado durante revisão QA: estado de busca não era limpo ao trocar de cliente. Corrigido pelo QA diretamente antes de marcar DONE.
- Duplicação não clona CPU (PropostaItem) — comportamento correto e esperado pelo PO.
- Filtros combináveis funcionando corretamente (status AND período AND busca).

## Scorecard

| Critério | Resultado |
|---|---|
| Escopo do plano entregue | YES |
| Testes aceitáveis | YES |
| Lint aceitável | YES |
| Documentação completa | YES |
| Estado do backlog correto | YES |

## Decisão

Sprint F2-06 → **DONE**.
