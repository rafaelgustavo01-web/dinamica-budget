# Technical Review — Sprint F2-DT-B

**Data:** 2026-04-28  
**Revisor:** Worker (kimi-k2.6) auto-revisao  
**Sprint:** F2-DT-B — Frontend Tech Debt Cleanup  
**Status:** TESTED

---

## Checklist de Entrega

| Criterio | Status | Evidencia |
|---|---|---|
| 2 commits atomicos | ✅ | `feat(f2-dt-b/1)` e `feat(f2-dt-b/2)` |
| Branch main apenas | ✅ | Sem feature branches |
| Nao tocou backend/alembic/scripts | ✅ | Apenas `app/frontend/**` alterado |
| `npm run build` verde | ✅ | 1241 modulos, 0 erros |
| `tsc --noEmit` sem erros novos | ✅ | 0 erros |
| `npm run test` "no tests found" code 0 | ✅ | `passWithNoTests: true` |

---

## Itens Fechados

### C-01 kimi (parcial) — Fundacao de Testes
- **Arquivos novos:**
  - `app/frontend/vitest.config.ts` — environment jsdom, alias `@`, `passWithNoTests: true`
  - `app/frontend/src/test/setupTests.ts` — import `@testing-library/jest-dom`, MSW lifecycle
  - `app/frontend/src/test/msw/handlers.ts` — placeholder handlers (health check)
  - `app/frontend/src/test/msw/server.ts` — `setupServer(...handlers)`
- **Arquivos modificados:**
  - `app/frontend/package.json` — scripts `test`, `test:watch`, `test:ui`; devDependencies: vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, msw
- **Gate:** `npm run test` retorna "No test files found, exiting with code 0"

### M-07 amazonq — ExportMenu Erro Silenciado
- **Arquivo:** `ExportMenu.tsx`
- **Mudanca:** `try/finally` -> `try/catch/finally` em `handleExcel` e `handlePdf`
- **UX:** Snackbar MUI com Alert severity="error" exibe mensagem amigavel por 6s
- **Estado local:** `useState<string | null>` para erro

### M-08 amazonq (frontend) — codigo_origem em Filhos
- **Arquivo:** `ExpandableTreeRow.tsx`
- **Mudanca:** `codigo_origem: undefined` -> `codigo_origem: child.codigo_origem ?? null`
- **Contrato:** `ComposicaoComponenteResponse` atualizado com `codigo_origem: string | null`
- **Impacto:** Coluna "Codigo" exibe codigo do filho em todos os niveis da arvore

### Gemini #4 — Botao Excluir TODO
- **Arquivo:** `ProposalDetailPage.tsx`
- **Verificacao:** `DELETE /propostas/{id}` existe em `app/backend/api/v1/endpoints/propostas.py:137`
- **Implementacao:** `deleteMutation` via `useMutation` (proposalsApi.delete) + `window.confirm` + navegacao para `/propostas` onSuccess
- **UX:** Botao desabilitado durante `isPending`

### B-07 amazonq — Dedup Tema
- **Arquivo removido:** `app/frontend/src/app/theme.ts` (barrel re-export obsoleto)
- **Arquivo preservado:** `app/frontend/src/app/theme/theme.ts` (implementacao real, importado por `providers.tsx`)
- **Imports:** Nenhum codigo de producao importava do barrel removido

---

## Riscos e Notas

1. **Nenhum teste real foi escrito** — conforme escopo, smoke tests vao para F2-DT-C (Solo, HOLD).
2. **Contrato `codigo_origem`** — backend (F2-DT-A) ainda pode nao estar entregue, mas o frontend ja declara o campo e tolera `null` (exibe `—`). Sem breaking change.
3. **Tema** — remocao do barrel `theme.ts` nao afeta nenhum import verificado (grep nao encontrou imports diretos).

---

## Conclusao

Todos os 5 itens de divida tecnica fechados. Build, typecheck e test runner verdes. Sprint apta para status TESTED.
