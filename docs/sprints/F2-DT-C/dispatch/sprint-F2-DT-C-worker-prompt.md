# Worker Handoff Prompt — Sprint F2-DT-C

> Delivered by: Scrum Master (PO + Arquiteto)
> Date: 2026-04-27
> Status: HOLD — entregar ao worker apenas apos F2-DT-A E F2-DT-B em DONE

```
Kimi (kimi-k2.6), voce e o worker de execucao da sprint F2-DT-C no
projeto Dinamica Budget — Frontend Smoke Tests (Solo).

PRE-REQUISITO: NAO INICIE se F2-DT-A ou F2-DT-B nao estiverem em DONE.
Verifique antes em @docs/shared/governance/BACKLOG.md.

Leia o briefing primeiro:
@docs/sprints/F2-DT-C/briefing/sprint-F2-DT-C-briefing.md

Execute o plano aprovado:
@docs/sprints/F2-DT-C/plans/2026-04-27-frontend-smoke-tests.md

Arquivos de contexto:
@docs/shared/governance/BACKLOG.md
@docs/sprints/F2-DT-A/walkthrough/done/walkthrough-F2-DT-A.md
@docs/sprints/F2-DT-B/walkthrough/done/walkthrough-F2-DT-B.md
@app/frontend/vitest.config.ts
@app/frontend/src/test/setupTests.ts
@app/frontend/src/test/msw/handlers.ts
@app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx
@app/frontend/src/features/catalogo/components/ExpandableTreeRow.tsx
@app/frontend/src/features/proposals/pages/ProposalsListPage.tsx
@app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx

Worker assignment:
- Worker ID: kimi-k2.6
- Provider: Moonshot
- Mode: BUILD

Regras:
- Branch `main` apenas. Sem feature branches.
- 1 commit unico:
  `test(f2-dt-c): smoke tests for histograma, composicoes, propostas`
- 4 arquivos de teste novos em `**/__tests__/**`, 12+ asserts.
- `npm run test` deve passar; `npm run build` continua verde.
- Apenas arquivos novos. NAO modificar codigo de producao do frontend
  nem nada do backend. Se algum componente for intestavel sem refactor,
  registre no walkthrough como debito — NAO refactore producao.
- Para botao Excluir em ProposalDetailPage: verifique decisao tomada
  em F2-DT-B (botao escondido OU implementado) e teste conforme estado
  atual em main.
- Gerar:
  docs/sprints/F2-DT-C/technical-review/technical-review-YYYY-MM-DD-f2-dt-c.md
- Salvar walkthrough em:
  docs/sprints/F2-DT-C/walkthrough/done/walkthrough-F2-DT-C.md
- Atualizar docs/shared/governance/BACKLOG.md de TODO para TESTED ao
  concluir.
- Nao marcar a sprint como DONE.
```
