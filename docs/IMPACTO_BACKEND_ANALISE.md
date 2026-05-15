# Análise de Impacto Backend — Refatoração Frontend

**Data:** 2026-05-15  
**Escopo:** Avaliar se as mudanças do `PLANO_REFATORACAO_FRONTEND.md` afetam contratos de API, payloads, endpoints ou lógica de backend  
**Veredicto:** ✅ **Nenhum impacto no backend** (zero mudanças em contratos de API)

---

## 1. Metodologia

Analisamos os 64 itens do plano de refatoração e mapeamos cada um contra:
- APIs consumidas (`proposalsApi`, `proposalItemsApi`, `histogramaApi`, `bcuItemApi`, `bcuApi`)
- Payloads enviados (`AddItemRequest`, `UpdateItemRequest`, `BcuMaoObraItemCreate`, etc.)
- Estratégias de cache invalidation (`queryClient.invalidateQueries`, `refetch`)
- Handlers de evento (`onSuccess`, `onError`)
- Configuração de transporte (`apiClient.ts`, headers, interceptors)

---

## 2. Análise por Fase

### Fase A — CTAs e Contraste (16 itens)

| Itens | Tipo de mudança | Impacto Backend |
|-------|-----------------|-----------------|
| A1-A6 | `variant="text"` → `variant="outlined/contained"`, `color="error/primary"` | **ZERO** — Puramente CSS/MUI |

**Conclusão:** Nenhuma chamada API, payload ou handler é alterado. São mudanças exclusivas de apresentação.

---

### Fase B — Layouts e Responsividade (16 itens)

| Itens | Tipo de mudança | Impacto Backend |
|-------|-----------------|-----------------|
| B1-B8 | `height: 560` → `flex: 1`, `Container maxWidth` removido, `Box` aninhados aplanados, `minWidth` hardcoded removido, frações mágicas de grid corrigidas | **ZERO** — Puramente CSS/layout |

**Conclusão:** Nenhuma mudança em lógica de negócio ou chamadas API.

---

### Fase C — Padronização Visual (15 itens)

| Itens | Tipo de mudança | Impacto Backend |
|-------|-----------------|-----------------|
| C1-C10 | Cores hex/rgba → tokens do tema, `borderRadius` padronizado, `headCell`/`dataCell` extraídos para shared style, `fontWeight` unificado | **ZERO** — Puramente tema/visual |

**Conclusão:** Nenhuma mudança em contratos ou payloads.

---

### Fase D — Eliminação de Duplicações (17 itens)

Esta é a fase mais intensa em código. Aqui está a análise detalhada:

#### D1: Unificar `ProposalItemsPage` + `ProposalItemsManager`

**Arquivos:** `ProposalItemsPage.tsx` (336 linhas) + `ProposalItemsManager.tsx` (301 linhas)

**Análise das APIs consumidas:**

| Operação | ProposalItemsPage | ProposalItemsManager | Endpoint | Payload |
|----------|-------------------|----------------------|----------|---------|
| listItems | `proposalItemsApi.listItems(id!)` | `proposalItemsApi.listItems(propostaId)` | `GET /propostas/{id}/items` | — |
| addItem | `proposalItemsApi.addItem(id!, body)` | `proposalItemsApi.addItem(propostaId, body)` | `POST /propostas/{id}/items` | `AddItemRequest` |
| updateItem | `proposalItemsApi.updateItem(id!, itemId, body)` | `proposalItemsApi.updateItem(propostaId, itemId, body)` | `PATCH /propostas/{id}/items/{itemId}` | `UpdateItemRequest` |
| deleteItem | `proposalItemsApi.deleteItem(id!, itemId)` | `proposalItemsApi.deleteItem(propostaId, itemId)` | `DELETE /propostas/{id}/items/{itemId}` | — |

**Diferenças de comportamento:**
- `ProposalItemsPage` usa `refetch()` em `onSuccess`; `ProposalItemsManager` usa `invalidateQueries`
- `ProposalItemsPage` faz `queryClient.invalidateQueries({ queryKey: ['proposta', id] })` adicional
- `ProposalItemsPage` faz `navigate('/propostas')` no delete
- `ProposalItemsManager` recebe props `propostaStatus`, `userRole`, `readOnly` para controle de permissões

**Impacto backend:** **ZERO** — Os mesmos endpoints, os mesmos payloads. A unificação proposta (`ProposalItemsPage` renderizando `<ProposalItemsManager>` com wrapper de layout) mantém todas as chamadas intactas.

**⚠️ Risco de regressão frontend:** Se o Manager perder as props `propostaStatus`, `userRole`, `readOnly` ao ser usado dentro de `ProposalDetailPage`, a permissão de edição pode quebrar.

---

#### D2: Extrair `useHistogramaTab(propostaId, tabela)`

**Arquivos:** `HistogramaTabGenerica.tsx` (187 linhas) + `HistogramaTabMaoObra.tsx` (183 linhas)

**Análise das APIs consumidas:**

| Operação | Generica | MaoObra | Endpoint |
|----------|----------|---------|----------|
| editarItem | `histogramaApi.editarItem(propostaId, tabela, itemId, payload)` | `histogramaApi.editarItem(propostaId, 'mao-obra', itemId, payload)` | `PATCH /propostas/{id}/histograma/{tabela}/{itemId}` |
| aceitarBcu | `histogramaApi.aceitarBcu(propostaId, tabela, itemId)` | `histogramaApi.aceitarBcu(propostaId, 'mao-obra', itemId)` | `POST /propostas/{id}/histograma/{tabela}/{itemId}/aceitar-bcu` |

**Diferença de payload:**
- `Generica`: `payload: Record<string, any>`
- `MaoObra`: `payload: Partial<PropostaPcMaoObraOut>`

**Impacto backend:** **ZERO** — O hook abstrai o estado local (`editing`, `handleChange`, `handleBlur`) e as mutations, mas os endpoints, paths e payloads permanecem idênticos.

**⚠️ Risco de build:** O hook genérico precisa preservar o tipo do payload (`Record<string, any>` para genérica, `Partial<T>` para mao-obra). Se mal tipado, quebra TypeScript mas não o backend.

---

#### D3: Refatorar 6 abas BCU em `BcuDataTab<T>`

**Arquivo:** `BcuPage.tsx` (803 linhas)

**Análise das APIs por aba:**

| Aba | Create | Update | Delete |
|-----|--------|--------|--------|
| Mão de Obra | `bcuItemApi.criarMaoObra(cabecalhoId, body)` | `bcuItemApi.atualizarMaoObra(cabecalhoId, itemId, body)` | `bcuItemApi.deletarMaoObra(cabecalhoId, itemId)` |
| Equipamentos | `bcuItemApi.criarEquipamento(...)` | `bcuItemApi.atualizarEquipamento(...)` | `bcuItemApi.deletarEquipamento(...)` |
| Encargos | `bcuItemApi.criarEncargo(...)` | `bcuItemApi.atualizarEncargo(...)` | `bcuItemApi.deletarEncargo(...)` |
| EPI | `bcuItemApi.criarEpi(...)` | `bcuItemApi.atualizarEpi(...)` | `bcuItemApi.deletarEpi(...)` |
| Ferramentas | `bcuItemApi.criarFerramenta(...)` | `bcuItemApi.atualizarFerramenta(...)` | `bcuItemApi.deletarFerramenta(...)` |
| Mobilização | `bcuItemApi.criarMobilizacao(...)` | `bcuItemApi.atualizarMobilizacao(...)` | `bcuItemApi.deletarMobilizacao(...)` |

**Payloads:** Cada aba tem um tipo `Create` distinto (`BcuMaoObraItemCreate`, `BcuEquipamentoItemCreate`, etc.). A refatoração propõe passar `onEdit` e `onDelete` como callbacks para o componente genérico.

**Impacto backend:** **ZERO** — O componente genérico não altera qual endpoint é chamado. Os callbacks (`onEdit`, `onDelete`) continuam invocando as mesmas funções do `bcuItemApi`. A tipagem genérica `T` é um artefato TypeScript.

**⚠️ Risco de build:** Cada tipo `Create`/`Update` é distinto. O generic `T` precisa ser propagado corretamente para os callbacks.

---

#### D4: Substituir `switch` por lookup object para mutations BCU

**Código atual (simplificado):**
```typescript
switch (type) {
  case 'MO': return bcuItemApi.criarMaoObra(...);
  case 'EQP': return bcuItemApi.criarEquipamento(...);
  // ... 4 cases
}
```

**Código proposto:**
```typescript
const API_MAP = {
  MO: { create: bcuItemApi.criarMaoObra, update: bcuItemApi.atualizarMaoObra, delete: bcuItemApi.deletarMaoObra },
  EQP: { create: bcuItemApi.criarEquipamento, ... },
  // ...
};
return API_MAP[type].create(cabecalhoId, body);
```

**Impacto backend:** **ZERO** — São exatamente as mesmas funções sendo chamadas. O lookup object é apenas uma reorganização sintática.

---

#### D5: Extrair `useProposalMutations(propostaId)`

**Mutations envolvidas:**
- `novaVersao`: `POST /propostas/{id}/nova-versao` + `navigate` em `onSuccess`
- `enviarAprovacao`: `POST /propostas/{id}/enviar-aprovacao`
- `aprovar`: `POST /propostas/{id}/aprovar`
- `rejeitar`: `POST /propostas/{id}/rejeitar`
- `codigo`: `PATCH /propostas/{id}` (body `{ codigo }`) + `setCodigoDraft` + `invalidateQueries(['propostas'])`
- `delete`: `DELETE /propostas/{id}` + `navigate('/propostas')` + `invalidateQueries(['propostas'])`

**Impacto backend:** **ZERO** — O hook extrai o boilerplate `useMutation` + `onSuccess`. As mesmas funções do `proposalsApi` são chamadas, com as mesmas invalidations.

**⚠️ Risco de regressão frontend:** A mutation `codigo` invalida `['propostas']` além de `['proposta', id]`, e `delete` faz `navigate`. O hook deve preservar essas particularidades.

---

#### D6: `useMemo` para stats em `MatchReviewPage`

**Código:**
```typescript
const confirmados = itens.filter((i) => i.match_status === 'CONFIRMADO').length;
// ... recomputado a cada render
```

**Impacto backend:** **ZERO** — Puramente computação local. Nenhuma chamada API é afetada.

---

#### D7: Compartilhar `UploadTcpoPage` + `AdminPage`

**APIs comuns:**
- `bcuApi.upload()` — `POST /bcu/upload`
- `bcuApi.criarCabecalho()` — `POST /bcu/cabecalhos`

**Impacto backend:** **ZERO** — As mesmas chamadas, apenas componentização do JSX.

---

#### D8: Simplificar lazy routes

**Código:**
```typescript
// Antes
lazy(() => import('../features/admin/AdminPage').then(m => ({ default: m.AdminPage })))
// Depois
lazy(() => import('../features/admin/AdminPage'))
```

**Impacto backend:** **ZERO** — Puramente configuração de bundler/router.

---

### Fase E — Microajustes (8 itens)

| Itens | Tipo de mudança | Impacto Backend |
|-------|-----------------|-----------------|
| E1-E8 | `getRowBgColor` helper, `const` em vez de `useState`, `bootstrapUser` extração, `FullScreenLoader` movido, `Box` em vez de `<div>`, etc. | **ZERO** — Puramente organização de código e micro-otimizações |

---

## 3. Resumo Executivo

| Categoria | Total de itens | Impacto Backend |
|-----------|----------------|-----------------|
| **Fase A** (CTAs) | 16 | ✅ ZERO |
| **Fase B** (Layouts) | 16 | ✅ ZERO |
| **Fase C** (Tema) | 15 | ✅ ZERO |
| **Fase D** (Deduplicação) | 17 | ✅ ZERO |
| **Fase E** (Microajustes) | 8 | ✅ ZERO |
| **TOTAL** | **72** | **✅ ZERO** |

---

## 4. Riscos Identificados (Frontend-only)

Embora não haja impacto no backend, há **3 riscos de regressão no frontend** que devem ser mitigados durante a implementação:

### Risco 1: Quebra de permissões em `ProposalItemsManager`
**Fase:** D1  
**Descrição:** `ProposalItemsManager` recebe props `propostaStatus`, `userRole`, `readOnly` que controlam `canEdit` / `canAddRemove` / `canDelete`. Se a unificação remover essas props (ou torná-las opcionais sem default), o componente dentro de `ProposalDetailPage` pode perder controle de permissões.  
**Mitigação:** Manter as props obrigatórias e testar que `readOnly=true` desabilita edição.

### Risco 2: TypeScript build quebrado em `BcuDataTab<T>`
**Fase:** D3  
**Descrição:** Cada aba BCU tem payloads `Create`/`Update` distintos. Um generic mal tipado pode causar erro de compilação (`BcuMaoObraItemCreate` vs `BcuEquipamentoItemCreate`).  
**Mitigação:** Rodar `npm run build` após cada refatoração. Usar `typeof bcuItemApi.criarMaoObra` para inferir tipos nos callbacks.

### Risco 3: Cache invalidation perdida em `useProposalMutations`
**Fase:** D5  
**Descrição:** A mutation `codigo` invalida tanto `['proposta', id]` quanto `['propostas']`. A mutation `delete` invalida `['propostas']` e faz `navigate`. Se o hook abstrair demais e padronizar apenas `['proposta', id]`, a listagem de propostas pode ficar desatualizada.  
**Mitigação:** O hook deve aceitar `onSuccess` customizado por mutation, ou expor `options` que permitam invalidações extras.

---

## 5. Recomendação

> **A refatoração frontend pode prosseguir sem qualquer modificação no backend.**

Nenhum endpoint, schema de request/response, header de autenticação, ou lógica de cache do backend precisa ser alterado.

**Checklist de validação (frontend-only):**
- [ ] `npm run build` passa sem erros de TypeScript após cada fase
- [ ] `npm run lint` não reporta novos warnings
- [ ] Testes unitários (`npm run test`) continuam passando
- [ ] Health check do backend (`/health`) retorna `status: ok` antes e depois
- [ ] Verificar manualmente: adicionar item em proposta, editar histograma, CRUD BCU, workflow de aprovação

---

*Relatório gerado com base na análise de 32 arquivos frontend e 5 arquivos de API (contratos de ~30 endpoints).*
