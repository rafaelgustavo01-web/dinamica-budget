# Walkthrough — Sprint F2-DT-B — Frontend Tech Debt Cleanup

**Data:** 2026-04-28  
**Worker:** kimi-k2.6  
**Status:** TESTED

---

## Commit 1 — Vitest Scaffold

**Mensagem:** `feat(f2-dt-b/1): vitest scaffold com RTL, MSW e jsdom`

### Arquivos Novos

1. **`app/frontend/vitest.config.ts`**
   - `plugins: [react()]` (mesmo plugin do Vite)
   - `test.globals: true`, `environment: 'jsdom'`
   - `setupFiles: ['./src/test/setupTests.ts']`
   - `passWithNoTests: true` (evita falha quando nenhum teste existe)
   - `resolve.alias: { '@': './src' }`

2. **`app/frontend/src/test/setupTests.ts`**
   - Importa `@testing-library/jest-dom` para matchers customizados
   - Liga/desliga MSW server em `beforeAll` / `afterAll`
   - Reseta handlers em `afterEach`

3. **`app/frontend/src/test/msw/handlers.ts`**
   - Array `handlers` vazio com placeholder `http.get('/api/health')`
   - Base para futuros smoke tests (F2-DT-C)

4. **`app/frontend/src/test/msw/server.ts`**
   - Exporta `server = setupServer(...handlers)`

### Arquivos Modificados

- **`app/frontend/package.json`**
  - Scripts: `test`, `test:watch`, `test:ui`
  - DevDeps: vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, msw

---

## Commit 2 — Polimento UI

**Mensagem:** `feat(f2-dt-b/2): polimento UI — ExportMenu erro, codigo_origem arvore, botao delete, dedup tema`

### 2.1 ExportMenu.tsx (M-07)

- Novo estado `error: string | null`
- `handleExcel` e `handlePdf` agora usam `try/catch/finally`
- Em `catch`, seta mensagem: "Falha ao exportar Excel/PDF. Tente novamente."
- Snackbar MUI com Alert `severity="error"`, autoHideDuration 6000ms

### 2.2 ComposicaoComponenteResponse (M-08 contrato)

- **`app/frontend/src/shared/types/contracts/servicos.ts`**
- Adicionado `codigo_origem: string | null` em `ComposicaoComponenteResponse`

### 2.3 ExpandableTreeRow.tsx (M-08 frontend)

- Passa `codigo_origem: child.codigo_origem ?? null` para filhos recursivos
- Interface Props atualizada: `codigo_origem?: string | null`
- Antes exibia `—` em todos os filhos; agora exibe o codigo real quando disponivel

### 2.4 ProposalDetailPage.tsx (Gemini #4)

- Adicionado `deleteMutation` via `useMutation` chamando `proposalsApi.delete(id!)`
- `onSuccess`: invalida cache `['propostas']` e navega para `/propostas`
- Botao "Excluir" agora:
  - Dispara `window.confirm` com mensagem de confirmacao
  - Chama `deleteMutation.mutate()` se confirmado
  - Desabilitado durante `deleteMutation.isPending`

### 2.5 Dedup Tema (B-07)

- **Removido:** `app/frontend/src/app/theme.ts` (barrel re-export obsoleto)
- **Preservado:** `app/frontend/src/app/theme/theme.ts` (implementacao real)
- Nenhum import de producao apontava para o barrel removido

---

## Gates Validados

```bash
cd app/frontend
npm run test      # No test files found, exiting with code 0 ✅
npm run build     # 1241 modules, 0 erros ✅
npx tsc --noEmit  # 0 erros ✅
```

## Itens Fechados

| Item | Origem | Arquivo(s) |
|---|---|---|
| C-01 (parcial) | Checkpoint kimi | package.json, vitest.config.ts, test/ |
| M-07 | Amazon Q | ExportMenu.tsx |
| M-08 (frontend) | Amazon Q | servicos.ts, ExpandableTreeRow.tsx |
| Gemini #4 | Gemini | ProposalDetailPage.tsx |
| B-07 | Amazon Q | theme.ts (removido) |

**Total: 5 itens fechados.**
