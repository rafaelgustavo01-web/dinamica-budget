# Worker Prompt — Sprint F2-03

**Para:** Claude Code (claude-sonnet-4-6)
**Modo:** BUILD / Always Proceed
**Sprint:** F2-03 — Tela de Revisao de Match
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget

---

Voce e o worker da Sprint F2-03. Implemente o plano completo em `docs/sprints/F2-03/plans/2026-04-25-match-review.md` do inicio ao fim sem pausas.

## Instrucoes de execucao

1. Leia o plano em `docs/sprints/F2-03/plans/2026-04-25-match-review.md`
2. Leia o briefing em `docs/sprints/F2-03/briefing/sprint-F2-03-briefing.md`
3. Execute cada task em ordem, fazendo commit apos cada uma
4. Execute `python -m pytest backend/tests/ -v --tb=short` apos cada task de backend
5. Execute `npx tsc --noEmit` apos cada task de frontend
6. Ao concluir: crie `docs/sprints/F2-03/technical-review/technical-review-2026-04-25-f2-03.md` e `docs/sprints/F2-03/walkthrough/done/walkthrough-F2-03.md`

## Criterios de conclusao

- 110+ PASS, 0 FAIL no pytest
- 0 erros no tsc --noEmit
- Todos os 7 tasks com checkbox marcado

## Diretorio de trabalho

```
app/backend/schemas/proposta.py
app/backend/api/v1/endpoints/pq_importacao.py
app/backend/tests/unit/test_pq_match_review.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/pages/MatchReviewPage.tsx
app/frontend/src/features/proposals/components/MatchItemRow.tsx
app/frontend/src/features/proposals/components/ServicoPickerDialog.tsx
app/frontend/src/features/proposals/routes.tsx
app/frontend/src/features/proposals/pages/ProposalImportPage.tsx
app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
```
