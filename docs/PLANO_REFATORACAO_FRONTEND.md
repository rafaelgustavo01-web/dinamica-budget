# Plano de Refatoração Frontend — Dinâmica Budget

**Autor:** Kimi (UI/UX Audit Agent)  
**Data:** 2026-05-15  
**Baseado em:** Varredura completa de 64 problemas em 32 arquivos  
**Escopo:** CTAs, layouts, padrões visuais, simplificação de código

---

## 1. Objetivo

Corrigir os problemas de contraste de CTAs, desorganização de layouts, elementos fora do padrão do tema e eliminar duplicações de código no frontend, priorizando impacto visual e manutenibilidade.

---

## 2. Fases de Execução

### Fase A — CTAs e Contraste (Impacto Visual Imediato)

**Meta:** Nenhum botão de ação primária/secundária/destrutiva pode ficar sem `variant`.

| # | Arquivo | Problema | Ação |
|---|---------|----------|------|
| A1 | `MatchItemRow.tsx:118-160` | 4 botões (`Confirmar`, `Substituir`, `Rejeitar`, `Remover`) sem variant em tabela densa | Adicionar `variant="outlined"` aos de ação, `variant="outlined" color="error"` ao destrutivo |
| A2 | `BcuPage.tsx` (6 abas) | Botões "Novo" flutuando como texto em todas as abas BCU | Adicionar `variant="outlined" size="small"` aos 6 botões |
| A3 | `BcuGestaoPage.tsx:331-348` | "Ativar" e "Remover" como texto na tabela de versões | Adicionar `variant="outlined"` e `variant="outlined" color="error"` |
| A4 | `ProposalShareDialog.tsx:124-132` | "Remover" ACL como texto + error | `variant="outlined" color="error"` |
| A5 | `ProposalDetailPage.tsx:142-258` | ~10 botões misturados sem hierarquia visual | Agrupar em ButtonGroup por intenção: primário (`contained`), secundário (`outlined`), terciário (menu "Mais ações") |
| A6 | `ProposalCpuPage.tsx:168-176` | "Recalcular BDI" competindo visualmente com "Voltar" | Promover "Recalcular BDI" para `variant="contained"` quando for ação principal; manter "Voltar" como `outlined` |

**Critério de aceite:** Todos os botões de ação em tabelas e dialogs devem ter `variant` explícito. Nenhum botão destrutivo pode ser `text`.

---

### Fase B — Layouts e Responsividade

**Meta:** Eliminar magic numbers de dimensão e garantir consistência com o tema.

| # | Arquivo | Problema | Ação |
|---|---------|----------|------|
| B1 | `ProposalDetailPage.tsx:142-258` | Action bar "sopa de botões" com `flexWrap` | Extrair `ProposalActionsBar` component; agrupar ações; colapsar em menu em `md` e abaixo |
| B2 | `MatchReviewPage.tsx:258-325` | `TableContainer` com `height: 560` hardcoded | Substituir por `flex: 1` com `maxHeight` responsivo |
| B3 | `CpuTable.tsx:184-220` | `minWidth: 1180` e `minWidth: 720` hardcoded | Remover ou vincular a `theme.breakpoints.values` |
| B4 | `ProposalItemsPage.tsx:186` | `Container maxWidth="lg"` quebrando contrato do AppShell | Remover `Container`; usar `Stack` ou `Box` direto |
| B5 | `BcuPage.tsx` (6 abas) | `overflowX: 'auto'` e `minWidth: 1200` apenas em `MaoObraTab` | Mover comportamento de overflow para o `Paper` pai em `BcuPage`; aplicar a todas as abas |
| B6 | `CompositionsPage.tsx:202-250` | `maxHeight: 560` hardcoded | Usar unidade responsiva (`vh`) ou constante compartilhada |
| B7 | `LoginPage.tsx:62` | `gridTemplateColumns` com frações mágicas (`1.05fr 0.95fr`) | Simplificar para `1fr 1fr` ou `repeat(2, 1fr)` |
| B8 | `AppShell.tsx:13-59` | 4 níveis de `Box` aninhados para layout flex padrão | Achatar para 2 níveis: root flex + `main` wrapper |

**Critério de aceite:** Nenhum `minWidth`, `maxHeight`, `height` ou grid fraction hardcoded sem vinculação ao tema ou viewport.

---

### Fase C — Padronização Visual (Tema e Cores)

**Meta:** Toda cor, raio e tipografia deve vir do tema. Eliminar hex/rgba hardcoded.

| # | Arquivo | Problema | Ação |
|---|---------|----------|------|
| C1 | `theme.ts:228` | `containedSecondary` hover com `#C48A1A` | Substituir por `tokens.secondary.dark` |
| C2 | `theme.ts:118` | `--db-primary-soft` com `rgba(...)` | Usar `alpha(tokens.primary.main, 0.12)` |
| C3 | `theme.ts:217,304,313,481` | `borderRadius` inconsistente (6, 4, 12, 8) | Criar escala `radii` (sm:4, md:8, lg:12) e aplicar uniformemente |
| C4 | `Sidebar.tsx` | Dezenas de `rgba(255,255,255,0.xx)` | Usar `alpha(theme.palette.common.white, x)` ou tokens dedicados `sidebar.text.primary` |
| C5 | `ProposalItemsPage.tsx:225` | Table head com `backgroundColor: '#f5f5f5'` | Substituir por `theme.palette.action.hover` ou `tokens.neutral[100]` |
| C6 | `ProposalItemsManager.tsx:178` | Mesmo `#f5f5f5` em outro arquivo | Mesmo tratamento |
| C7 | `HistogramaTabGenerica.tsx`, `HistogramaTabMaoObra.tsx`, `RecursosExtrasTab.tsx`, `BcuPage.tsx`, `BcuGestaoPage.tsx` | `headCell` / `dataCell` / `numCell` com font sizes hardcoded (`0.72rem`, `0.8rem`, `0.85rem`) | Extrair para `shared/styles/tableCells.ts` ou adicionar variantes `tableHead` / `tableBody` ao tema |
| C8 | `ServicoPickerDialog.tsx:91` | `style={{ color: 'gray', fontSize: '0.8rem' }}` | Usar `Typography variant="caption" color="text.secondary"` |
| C9 | `ProposalDetailPage.tsx:372` | `cursor: 'pointer'` em `Paper` | Usar `CardActionArea` ou `ButtonBase` |
| C10 | `DataTable.tsx:71-73` | `fontWeight: 700` manual vs `fontWeight: 600` do tema | Remover override manual; deixar tema padronizar |

**Critério de aceite:** `grep -r "rgba\|#\{3,6\}" --include="*.tsx" --include="*.ts"` deve retornar apenas valores intencionalmente temáticos ou casos justificados.

---

### Fase D — Eliminação de Duplicações (Simplificação)

**Meta:** Reduzir linhas duplicadas, extrair hooks e componentes genéricos.

| # | Arquivo | Problema | Ação |
|---|---------|----------|------|
| D1 | `ProposalItemsPage.tsx` + `ProposalItemsManager.tsx` | Duplicação de CRUD, diálogo, estado, tabela | Unificar: `ProposalItemsPage` deve renderizar `<ProposalItemsManager>` com wrapper de layout (status + voltar), ou extrair hook `useProposalItemsCrud` |
| D2 | `HistogramaTabGenerica.tsx` + `HistogramaTabMaoObra.tsx` | ~80% lógica duplicada (editing, handleBlur, handleChange, divergeMap, mutations) | Extrair `useHistogramaTab(propostaId, tabela)` hook; tabs consomem o hook |
| D3 | `BcuPage.tsx` | 6 abas (`MaoObraTab`…`MobilizacaoTab`) com 60+ linhas cada, duplicando loading, erro, empty, table, CRUD | Criar `BcuDataTab<T>` genérico aceitando `columns`, `data`, `onEdit`, `onDelete`, `isLoading`; cada aba vira wrapper de ~10 linhas |
| D4 | `BcuPage.tsx:609-673` | `criar/atualizar/deletar Mutation` com `switch` de 6 cases | Substituir por lookup object: `const API_MAP = { MO: { create: ..., update: ..., delete: ... }, ... }` |
| D5 | `ProposalDetailPage.tsx:60-104` | 6 mutações com `onSuccess` boilerplate idêntico | Criar `useProposalMutations(propostaId)` hook com invalidação padrão |
| D6 | `MatchReviewPage.tsx:161-169` | Stats (`confirmados`, `rejeitados`, etc.) recomputados a cada render via `filter` | Wrappar em `useMemo(() => ..., [itens])` |
| D7 | `AdminPage.tsx` + `UploadTcpoPage.tsx` | `AdminPage` duplica upload TCPO e BCU já presentes em `UploadTcpoPage` | Extrair `TcpoUploadSection` e `BcuUploadSection` como shared components; ambas as páginas consomem |
| D8 | `router.tsx:16-105` | Lazy routes com `.then((module) => ({ default: module.PageName }))` boilerplate | Simplificar para `lazy(() => import('../features/admin/AdminPage'))` (default export) |

**Critério de aceite:** Nenhum par de arquivos deve conter >50% de JSX/lógica idêntica sem compartilhar hook/componente.

---

### Fase E — Microajustes e Consistência

**Meta:** Limpar code smell restante (baixa prioridade, pode ser feito incrementalmente).

| # | Arquivo | Problema | Ação |
|---|---------|----------|------|
| E1 | `SmartImportStagingPage.tsx:251-257` | Ternário inline para `bgcolor` de linha | Extrair `getRowBgColor(rowClass)` helper |
| E2 | `FeedbackProvider.tsx:55` | `minWidth: 320` e `boxShadow: 6` hardcoded | Usar tema/breakpoints |
| E3 | `SmartImportUploadPage.tsx:25-26` | `propostaId` em `useState` sem nunca mudar | Usar const direta de `searchParams` |
| E4 | `AuthProvider.tsx:78-82,129-141` | `refreshUser()` e `login()` duplicam chamada `getMe` + `syncSelectedClient` | Extrair `bootstrapUser(me)` |
| E5 | `CompositionsPage.tsx` / `ServicesPage.tsx` | `ComposicaoItemRow` / `ComposicaoRow` inline, quase idênticos a `ExpandableTreeRow` | Usar `ExpandableTreeRow` existente ou extrair `ServiceCompositionTree` |
| E6 | `ProtectedRoute.tsx:15-28` | `FullScreenLoader` inline | Mover para `shared/components/FullScreenLoader.tsx` |
| E7 | `DashboardPage.tsx:12-40` | `MetricCard` inline no page | Mover para `shared/components/MetricCard.tsx` |
| E8 | `ContractNotice.tsx:40-65` | `<div>` cru em vez de `<Box>` | Substituir por `Box` |

---

## 3. Sequência de Commits Recomendada

1. `fix(ui): add explicit button variants across tables and dialogs` (Fase A)
2. `refactor(layout): flatten Box nesting and remove hardcoded dimensions` (Fase B)
3. `refactor(theme): replace hardcoded colors and radii with theme tokens` (Fase C)
4. `refactor(proposals): unify ProposalItemsPage and ProposalItemsManager` (D1)
5. `refactor(bcu): extract generic BcuDataTab and API lookup map` (D2, D3, D4)
6. `refactor(proposals): extract useHistogramaTab hook and useProposalMutations` (D5, D6)
7. `refactor(admin): share upload sections between AdminPage and UploadTcpoPage` (D7)
8. `chore(router): simplify lazy route imports` (D8)
9. `chore(ui): micro cleanups — bgColor helpers, inline loaders, Box migration` (Fase E)

---

## 4. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Quebrar estilos visuais em telas pequenas | Testar `md` e `sm` após mudanças de layout |
| Perder funcionalidade ao unificar BCU tabs | Manter snapshots dos props de cada aba antes do refactor |
| Conflito com outro dev editando mesmos arquivos | Fazer commits pequenos e frequentes (recomendado acima) |
| Mudança de cor no Sidebar afetar legibilidade | Validar contraste WCAG 2.1 após aplicar `alpha()` |

---

## 5. Métricas de Sucesso

- [ ] Zero botões de ação sem `variant` em páginas de produção
- [ ] Zero `minWidth`/`maxHeight`/`height` hardcoded sem tema
- [ ] Zero duplicação de `headCell`/`dataCell` (único source: `shared/styles/tableCells.ts`)
- [ ] `ProposalItemsPage.tsx` reduzido para <30 linhas (delegando ao Manager)
- [ ] `BcuPage.tsx` reduzido em >200 linhas após extrair `BcuDataTab`
- [ ] Build (`npm run build`) passando sem warnings novos
- [ ] Health check do backend permanece `status: ok`

---

*Plano gerado com base em auditoria de 64 problemas em 32 arquivos do frontend.*
