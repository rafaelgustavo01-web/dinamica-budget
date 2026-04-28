# Plano de Implementacao: Frontend Tech Debt Cleanup (Sprint F2-DT-B)

**Data:** 2026-04-27
**Autor:** Supervisor (PO + Arquiteto)
**Branch:** `main` (regra global — sem feature branches)
**Worker:** kimi-k2.6
**Mode:** BUILD

## 1. Contexto

Checkpoint tecnico (2026-04-27) identificou 4 itens de divida tecnica
no frontend que devem ser corrigidos em paralelo ao trabalho backend
(Sprint F2-DT-A, Claude). Esta sprint estabelece a fundacao de testes
do frontend (zero hoje) e fecha 4 itens de polimento UI.

## 2. Escopo

Apenas `app/frontend/**`. Proibido tocar `app/backend/**`,
`app/alembic/**`, `scripts/**` (ownership da Sprint F2-DT-A, paralela).

## 3. Contrato de API (handshake com F2-DT-A)

**FROZEN — F2-DT-A esta entregando esse campo:**

```ts
// app/frontend/src/shared/services/api/composicoesApi.ts
export interface ComposicaoComponenteResponse {
  // ... campos existentes ...
  codigo_origem: string | null;   // NOVO — preenchido para todos os niveis
}
```

Voce pode codificar contra esse contrato imediatamente. Se F2-DT-A
mergear depois desta sprint, comportamento atual e preservado pois o
componente ja tolera `undefined` (mostra `—`). Verificacao end-to-end
acontece naturalmente apos as duas merges.

## 4. Ordem de Tarefas (2 commits atomicos)

### Commit 1 — Vitest + RTL scaffold

**Arquivos novos:**
- `app/frontend/vitest.config.ts`
- `app/frontend/src/test/setupTests.ts`
- `app/frontend/src/test/msw/handlers.ts` (handlers vazios — base)
- `app/frontend/src/test/msw/server.ts`

**Arquivos modificados:**
- `app/frontend/package.json` — adicionar devDependencies + scripts:
  ```json
  {
    "scripts": {
      "test": "vitest run",
      "test:watch": "vitest",
      "test:ui": "vitest --ui"
    },
    "devDependencies": {
      "vitest": "^2.x",
      "@testing-library/react": "^16.x",
      "@testing-library/jest-dom": "^6.x",
      "@testing-library/user-event": "^14.x",
      "jsdom": "^25.x",
      "msw": "^2.x"
    }
  }
  ```

**Configuracao:**
- `vitest.config.ts`: `environment: 'jsdom'`, `setupFiles: ['./src/test/setupTests.ts']`,
  globals true, `resolve.alias` igual ao do `vite.config.ts`.
- `setupTests.ts`: importar `@testing-library/jest-dom`, iniciar MSW server,
  limpar handlers entre testes.

**Gate:** `npm run test` retorna "no tests found" sem erro.
`npm run build` continua passando. `tsc --noEmit` sem erros novos.

**Fecha:** C-01 kimi (parcial — fundacao). Smoke tests em si vao para
sprint F2-DT-C (Solo).

---

### Commit 2 — Polimento UI

**Arquivos:**
- `app/frontend/src/features/proposals/components/ExportMenu.tsx`
- `app/frontend/src/features/proposals/components/ExpandableTreeRow.tsx`
- `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- `app/frontend/src/shared/services/api/composicoesApi.ts`
- decisao de tema: ou `app/frontend/src/app/theme.ts` ou
  `app/frontend/src/app/theme/theme.ts` — manter um, deletar o outro,
  atualizar imports

**Mudancas:**

**2.1 — `ExportMenu.tsx` (M-07 amazonq):**
- Adicionar `useState<string | null>` para erro local.
- Trocar `try/finally` por `try/catch/finally` em `handleExcel` e
  `handlePdf`.
- No catch, setar mensagem amigavel (ex: "Falha ao exportar. Tente
  novamente.") e exibir via `Snackbar` MUI ou Alert inline.

**2.2 — `composicoesApi.ts` (contrato handshake):**
- Adicionar `codigo_origem: string | null` em
  `ComposicaoComponenteResponse`.

**2.3 — `ExpandableTreeRow.tsx` (M-08 amazonq):**
- Trocar `codigo_origem: undefined` por
  `codigo_origem: child.codigo_origem ?? null` ao montar `item` para
  filhos recursivos.
- Coluna "Codigo" agora exibe codigo do filho em todos os niveis.

**2.4 — `ProposalDetailPage.tsx` linha 210 (Gemini #4):**
- TODO atual: `onClick={() => { /* TODO: implementar delete */ }}`
- Decisao: como o endpoint backend de delete pode nao existir ainda,
  **esconder o botao** (renderizar `null` se nao houver handler) ate
  que o endpoint esteja disponivel. Adicionar comentario de 1 linha
  explicando.
- Alternativa: se `DELETE /propostas/{id}` ja existe, implementar com
  confirmacao (`window.confirm` ou Dialog MUI) + `useMutation` +
  navegacao para lista.
- Verificar primeiro com `grep` no backend; se nao existir, esconder
  botao.

**2.5 — Dedup tema (B-07 amazonq):**
- Verificar conteudo de `app/theme.ts` e `app/theme/theme.ts`.
- Manter o que tiver mais imports apontando para ele.
- Deletar o outro.
- Atualizar imports onde necessario.

**Gate:** `npm run build` verde, `tsc --noEmit` sem erros novos,
`npm run test` continua "no tests found" (sem testes reais ainda).

**Fecha:** M-07, M-08(frontend), B-07 amazonq, Gemini #4.

---

## 5. Restricoes Criticas

- **Branch `main` apenas.** Sem feature branches.
- **2 commits atomicos** com mensagem `feat(f2-dt-b/N): <descricao>`.
- Build verde apos cada commit.
- **Nao tocar `app/backend/**`, `app/alembic/**`, `scripts/**`.**
- Nao marcar sprint como `DONE` — apenas `TESTED`.

## 6. Artefatos Obrigatorios Antes de TESTED

- `docs/sprints/F2-DT-B/technical-review/technical-review-2026-04-27-f2-dt-b.md`
- `docs/sprints/F2-DT-B/walkthrough/done/walkthrough-F2-DT-B.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-DT-B `TODO -> TESTED`

## 7. Fora de Escopo (parking lot)

- Escrever testes smoke reais (vai para Sprint F2-DT-C, Solo, depende
  de A+B em DONE).
- A-04 kimi (i18n)
- M-01 kimi (componentes grandes UsersPage/BcuPage/CompositionsPage)
- A-03 kimi (refactor HistogramaTabMaoObra/Generica para hook
  compartilhado)
- A-02 kimi (DecimalValue drift)

## 8. Itens Fechados

C-01 kimi (parcial — scaffold), M-07 amazonq, M-08 amazonq (frontend),
B-07 amazonq, Gemini #4. **Total: 5 itens.**
