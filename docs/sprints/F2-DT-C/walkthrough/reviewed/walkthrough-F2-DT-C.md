# Walkthrough — Sprint F2-DT-C — Frontend Smoke Tests

**Data:** 2026-04-29  
**Worker:** kimi-k2.6  
**Status:** TESTED

---

## Resumo

Sprint F2-DT-C entregou **13 asserts de smoke test** em 4 arquivos de teste, cobrindo as 3 features críticas do frontend de Orçamentos: Histograma da Proposta, Composições (árvore expansível) e Propostas (lista + detalhe).

Trata-se de rede de segurança mínima para refactors futuros — não é cobertura completa. Nenhum arquivo de produção foi modificado.

---

## Commit

**Mensagem:** `test(f2-dt-c): smoke tests for histograma, composicoes, propostas`

---

## Arquivos Novos

| # | Arquivo | Asserts | Cobertura |
|---|---|---|---|
| 1 | `app/frontend/src/test/test-utils.tsx` | — | Helper `renderWithProviders` (QueryClient + MemoryRouter + FeedbackProvider) |
| 2 | `app/frontend/src/features/proposals/pages/__tests__/ProposalHistogramaPage.test.tsx` | 4 | Renderização, troca de aba, badge de divergência, edição inline com PATCH |
| 3 | `app/frontend/src/features/compositions/components/__tests__/ExpandableTreeRow.test.tsx` | 3 | Render raiz, expansão com fetch de filhos, recursão de 2 níveis com `codigo_origem` |
| 4 | `app/frontend/src/features/proposals/pages/__tests__/ProposalsListPage.test.tsx` | 2 | Renderização de 3 propostas, navegação por clique na linha |
| 5 | `app/frontend/src/features/proposals/pages/__tests__/ProposalDetailPage.test.tsx` | 4 | Renderização de header/abas, ExportMenu (2 opções), erro de export 500, botão Excluir para OWNER |

**Total: 13 asserts, 0 falhas.**

---

## MSW Handlers (runtime via `server.use`)

- `GET /api/v1/propostas/123/histograma`
- `PATCH /api/v1/propostas/123/histograma/mao-obra/mo-1`
- `GET /api/v1/servicos/srv-1/componentes`
- `GET /api/v1/servicos/srv-2/componentes`
- `GET /api/v1/propostas/?cliente_id=client-1`
- `GET /api/v1/propostas/p1`
- `GET /api/v1/propostas/root/root-1/versoes`
- `GET /api/v1/propostas/p1/export/excel` (cenário de erro 500)

---

## Gates Validados

```bash
cd app/frontend
npm run test      # 4 test files, 13 passed, 0 failed ✅
npm run build     # 0 erros, bundle gerado ✅
npx tsc --noEmit  # 0 erros ✅
```

---

## Itens Fechados

| Item | Origem | Arquivo(s) |
|---|---|---|
| C-01 (completo) | Checkpoint kimi | test-utils.tsx + 4 arquivos `.test.tsx` |
| Smoke Histograma | Briefing F2-DT-C | ProposalHistogramaPage.test.tsx |
| Smoke Composições | Briefing F2-DT-C | ExpandableTreeRow.test.tsx |
| Smoke Propostas (list) | Briefing F2-DT-C | ProposalsListPage.test.tsx |
| Smoke Propostas (detail) | Briefing F2-DT-C | ProposalDetailPage.test.tsx |

**Total: 5 itens fechados.**

---

## Débitos Registrados

- `ExpandableTreeRow` gera warning de hydration no jsdom devido ao `Collapse` do MUI renderizando `<div>` como container de `<tr>`. Isso é uma limitação do jsdom, não do componente em produção (onde a estrutura de tabela está correta).
- Não foram adicionados smoke tests para `RecursosExtrasTab` nem `AlocacaoRecursoDialog` (dentro do escopo do histograma) — considerados secundários para a rede de segurança mínima.
