# Walkthrough — Sprint F2-03
**Sprint:** F2-03 — Tela de Revisão de Match
**Data:** 2026-04-26
**Status:** TESTED

---

## Resumo

Implementação completa da tela de revisão de match: backend (2 endpoints) + frontend (MatchReviewPage + componentes + navegação).

---

## Tasks Concluídas

- [x] Task 1: Schemas `PqItemResponse` + `PqMatchConfirmarRequest`
- [x] Task 2: `GET /pq/itens` + `PATCH /pq/itens/{id}/match`
- [x] Task 3: Tipos e métodos em `proposalsApi`
- [x] Task 4: `ServicoPickerDialog`
- [x] Task 5: `MatchItemRow`
- [x] Task 6: `MatchReviewPage` + rota `/propostas/:id/match-review`
- [x] Task 7: Botões de acesso em `ProposalDetailPage` e `ProposalImportPage`

---

## Fluxo Implementado

1. Usuário executa match em `ProposalImportPage` → aparece botão "Revisar e Confirmar Match"
2. Usuário navega para `/propostas/:id/match-review`
3. `MatchReviewPage` carrega todos os `PqItems` da proposta via `GET /pq/itens`
4. Barra de progresso mostra `(confirmados + rejeitados) / total * 100%`
5. Por linha (`MatchItemRow`):
   - **Confirmar** → `PATCH` com `acao=confirmar` → status → `CONFIRMADO`
   - **Substituir** → abre `ServicoPickerDialog`, busca via `searchApi`, seleciona → `PATCH` com `acao=substituir` + `servico_match_id` → status → `MANUAL`
   - **Rejeitar** → `PATCH` com `acao=rejeitar` → status → `SEM_MATCH`
6. Botão "Ir para CPU" habilitado quando pelo menos 1 item foi revisado
7. `ProposalDetailPage` exibe botão "Revisar Match" (desabilitado em `RASCUNHO`)

---

## Validações

- `python -m pytest backend/tests/` → **124 passed, 0 failed**
- `npx tsc --noEmit` → **0 erros**
