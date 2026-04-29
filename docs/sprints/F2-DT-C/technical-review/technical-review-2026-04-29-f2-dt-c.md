# Technical Review — F2-DT-C Frontend Smoke Tests

**Data:** 2026-04-29  
**Sprint:** F2-DT-C  
**Worker:** kimi-k2.6  
**Branch:** main  
**Suite final:** 13 passed, 0 failed (4 test files)

---

## Commit entregue

| # | Hash | Titulo |
|---|------|--------|
| 1 | `PENDENTE` | `test(f2-dt-c): smoke tests for histograma, composicoes, propostas` |

---

## Arquivos novos

### 1. `app/frontend/src/test/test-utils.tsx`
- Helper `renderWithProviders` que envolve o componente em:
  - `QueryClientProvider` (retry desabilitado, gcTime/staleTime infinito para estabilidade)
  - `MemoryRouter` com suporte a `route`, `initialEntries` e `path` (para `useParams`)
  - `FeedbackProvider` (contexto de snackbar usado por Histograma e ExportMenu)

### 2. `app/frontend/src/features/proposals/pages/__tests__/ProposalHistogramaPage.test.tsx` (4 asserts)
- **Renderização:** mocka `GET /api/v1/propostas/123/histograma` com fixture completa (`mao_obra`, `equipamentos`, divergências, `cpu_desatualizada`); verifica título "Histograma da Proposta", linha "Pedreiro" e chip "CPU Desatualizada".
- **Troca de aba:** clica na aba "Equipamentos" e aguarda renderização da tabela genérica com coluna "Aluguel R$/h" e item "Betoneira".
- **Divergência:** valida que chips "1 divergência(s) com BCU" e "Diverge" aparecem quando `divergencias` contém snapshot vs BCU distintos.
- **Edição inline:** simula `change` + `blur` no primeiro `spinbutton` (salário); intercepta `PATCH /api/v1/propostas/123/histograma/mao-obra/mo-1` e valida payload `{ salario: 4000 }`.

### 3. `app/frontend/src/features/compositions/components/__tests__/ExpandableTreeRow.test.tsx` (3 asserts)
- **Render raiz:** monta linha expansível com `codigo_origem = 'CON-001'` e confirma visibilidade.
- **Expansão + filhos:** clica no chevron, mocka `GET /api/v1/servicos/srv-1/componentes` com 3 filhos (1 serviço recursivo + 2 insumos); valida que "Cimento CP-II" exibe `CIM-001`, "Sub-servico" exibe `SER.001` e "Areia" exibe `—` (null).
- **Recursão 2 níveis:** mocka segundo nível (`GET /api/v1/servicos/srv-2/componentes`) com tubo PVC; expande e valida `TUB-001`.

### 4. `app/frontend/src/features/proposals/pages/__tests__/ProposalsListPage.test.tsx` (2 asserts)
- **Renderização:** mocka `GET /api/v1/propostas/?cliente_id=client-1` com 3 propostas; valida "Obra Alpha", "Obra Beta", "Obra Gamma".
- **Navegação:** usa `LocationCapture` com `useLocation` dentro do mesmo `MemoryRouter`; clica na linha e verifica que pathname mudou para `/propostas/p1`.

### 5. `app/frontend/src/features/proposals/pages/__tests__/ProposalDetailPage.test.tsx` (4 asserts)
- **Renderização:** mocka `GET /api/v1/propostas/p1` e `GET /api/v1/propostas/root/root-1/versoes` (histórico); valida header "Proposta: PROP-2026-001", título "Obra Alpha", seções "Dados da Proposta" e "Totais".
- **ExportMenu:** clica em "Exportar" e valida presença de "Excel (xlsx)" e "PDF (folha de rosto)".
- **Erro de export:** mocka `GET /api/v1/propostas/p1/export/excel` com 500; clica em Excel e valida snackbar "Falha ao exportar Excel. Tente novamente.".
- **Botão Excluir:** mocka `useAuth` com `is_admin: true`; valida que botão "Excluir" está presente (decisão F2-DT-B: botão implementado para OWNER/admin).

---

## Gates Validados

```bash
cd app/frontend
npm run test      # 4 test files, 13 passed, 0 failed ✅
npm run build     # 1241 modules, 0 erros ✅
npx tsc --noEmit  # 0 erros ✅
```

---

## Riscos e Observacoes

- Apenas arquivos novos em `**/__tests__/**` e `src/test/test-utils.tsx`. Zero modificações em código de produção.
- `ExpandableTreeRow` gera warning de hydration no jsdom (`<tr>` dentro de `<div>` do `Collapse`) — isso é comportamento conhecido do MUI + jsdom e não afeta o teste.
- `ProposalHistoryPanel` dispara fetch para `/api/v1/propostas/root/:rootId/versoes`; handler de fallback vazio adicionado para evitar erro MSW em todos os testes de `ProposalDetailPage`.
- O helper `test-utils.tsx` usa `staleTime: Infinity` para evitar re-fetches imprevisíveis durante asserts assíncronos.
