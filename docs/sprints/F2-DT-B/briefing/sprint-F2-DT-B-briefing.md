# Sprint Briefing — F2-DT-B — Frontend Tech Debt Cleanup

> Data: 2026-04-27
> Preparado por: Supervisor (PO + Arquiteto)
> Worker designado: kimi-k2.6
> Execution mode: BUILD
> Plan: `docs/sprints/F2-DT-B/plans/2026-04-27-frontend-tech-debt-cleanup.md`

## Mission

O frontend hoje tem **0 testes unitarios** (95 arquivos, 13.498 linhas).
Esta sprint estabelece a fundacao Vitest + RTL + MSW e fecha 4 itens
pendentes de polimento UI (export error handling, codigo_origem em
arvore, botao delete TODO, dedup de arquivo de tema).

Roda em **paralelo total** com Sprint F2-DT-A (Claude, backend) — trees
de arquivo disjuntas. Unica linha de acoplamento: o contrato
`codigo_origem` em `ComposicaoComponenteResponse`, que F2-DT-A esta
entregando no Commit 3 e voce ja pode codificar contra ele.

Smoke tests reais vao para Sprint F2-DT-C (Solo, depende de A+B em
DONE) — esta sprint apenas estabelece o scaffold.

## Delegation Envelope

| Campo | Valor |
|---|---|
| Sprint | F2-DT-B |
| Status entrada | PLAN |
| Status saida | TESTED |
| Worker | kimi-k2.6 |
| Provider | Moonshot |
| Mode | BUILD |
| Branch | main (regra global) |
| Auth/Quota | PASS (worker default do projeto) |
| Paralela com | F2-DT-A (Claude, backend — disjoint) |

## Current Code State (hotspots validados)

### `app/frontend/src/features/proposals/components/ExportMenu.tsx`
- Erros de download silenciados: `try/finally` sem `catch`, usuario nao
  recebe feedback (M-07)

### `app/frontend/src/features/proposals/components/ExpandableTreeRow.tsx`
- `codigo_origem: undefined` para filhos recursivos — coluna "Codigo"
  exibe `—` em todos os niveis exceto raiz (M-08 frontend)

### `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- L210: `onClick={() => { /* TODO: implementar delete */ }}` — botao
  Excluir visivel mas sem acao (Gemini #4)

### Tema duplicado
- `app/frontend/src/app/theme.ts` E `app/frontend/src/app/theme/theme.ts`
  coexistem (B-07)

### Sem fundacao de teste
- Nenhum `*.test.ts` ou `*.spec.tsx` no projeto (C-01 kimi)

## Required Changes (resumo — detalhe no plan)

| # | Commit | Files | Itens fechados |
|---|---|---|---|
| 1 | vitest scaffold | vitest.config.ts, setupTests.ts, msw/, package.json | C-01 kimi (parcial) |
| 2 | polimento UI | ExportMenu, ExpandableTreeRow, ProposalDetailPage, composicoesApi, theme dedup | M-07, M-08fe, B-07, Gemini#4 |

## Mandatory Tests

- `npm run build` verde apos cada commit
- `tsc --noEmit` sem erros novos
- `npm run test` (apos Commit 1) retorna "no tests found" sem error

```bash
cd app/frontend
npm install
npm run test
npm run build
npx tsc --noEmit
```

## Required Artifacts Before Status `TESTED`

- `docs/sprints/F2-DT-B/technical-review/technical-review-2026-04-27-f2-dt-b.md`
- `docs/sprints/F2-DT-B/walkthrough/done/walkthrough-F2-DT-B.md`
- `docs/shared/governance/BACKLOG.md` atualizado de `TODO` para `TESTED`

## Critical Warnings

1. **Branch `main` apenas.** Sem feature branches. Regra global do PO.
2. **2 commits atomicos** com mensagem `feat(f2-dt-b/N): <descricao>`.
3. **Nao tocar `app/backend/**`, `app/alembic/**`, `scripts/**`.**
   Sprint paralela F2-DT-A (Claude) detem ownership exclusivo.
4. Contrato `codigo_origem` em `ComposicaoComponenteResponse` esta
   FROZEN — assinatura exata no plan secao 3.
5. Para o botao Excluir (2.4): **verifique primeiro se `DELETE
   /propostas/{id}` existe no backend.** Se nao existir, **esconder
   botao** ate sprint dedicada. Nao implementar endpoint backend nesta
   sprint (fora de ownership).
6. Nao marcar sprint como `DONE` — apenas `TESTED`.
7. Nao escrever testes smoke reais — isso e Sprint F2-DT-C (Solo,
   futura).
