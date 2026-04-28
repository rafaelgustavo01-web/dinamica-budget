# Plano de Implementacao: Frontend Smoke Tests (Sprint F2-DT-C)

**Data:** 2026-04-27
**Autor:** Supervisor (PO + Arquiteto)
**Branch:** `main` (regra global — sem feature branches)
**Worker:** kimi-k2.6 (Solo)
**Mode:** BUILD
**Status:** PLAN — bloqueada em DT-A E DT-B em DONE

## 1. Contexto

Sprint F2-DT-B entregou o scaffold Vitest + RTL + MSW. Sprint F2-DT-A
entregou o contrato `codigo_origem`. Esta sprint escreve **1 smoke
test por feature critica** para garantir cobertura minima de regressao
nos componentes mais sensiveis.

Nao e cobertura completa — e rede de seguranca minima ("o componente
renderiza, faz a chamada certa, exibe os dados").

## 2. Pre-requisitos

- F2-DT-A em `DONE` (contrato `codigo_origem` no backend)
- F2-DT-B em `DONE` (scaffold Vitest + MSW disponivel)
- `npm run test` retorna "no tests found" sem erro

## 3. Escopo

Apenas `app/frontend/src/**/*.test.tsx` (arquivos novos). Nao modificar
codigo de producao do frontend nem nada do backend.

## 4. Ordem de Tarefas (1 commit por feature)

### Test 1 — Histograma (3 abas)

**Arquivo novo:**
`app/frontend/src/features/proposals/pages/__tests__/ProposalHistogramaPage.test.tsx`

**O que cobrir:**
- Renderiza pagina sem crash com mock de proposta + mock de histograma
- Troca de aba (MO -> EQP -> ENC) muda conteudo da tabela
- Edicao inline de uma celula dispara mutation com payload correto
- Badge de divergencia aparece quando `valor_atual != valor_snapshot`

**MSW handlers:**
- `GET /api/v1/propostas/:id/histograma` -> mock fixture
- `PATCH /api/v1/propostas/:id/histograma/items/:itemId` -> 200

### Test 2 — Composicoes (tree expansion)

**Arquivo novo:**
`app/frontend/src/features/catalogo/components/__tests__/ExpandableTreeRow.test.tsx`

**O que cobrir:**
- Linha raiz renderiza com codigo_origem visivel
- Click no chevron dispara fetch de filhos
- Filhos renderizam com codigo_origem (nao mais `—`)
- Recursao de 2 niveis funciona

**MSW handlers:**
- `GET /api/v1/composicoes/:id/componentes` -> mock fixture com
  3 filhos (1 servico recursivo + 2 insumos)

### Test 3 — Propostas (list + detail)

**Arquivos novos:**
- `app/frontend/src/features/proposals/pages/__tests__/ProposalsListPage.test.tsx`
- `app/frontend/src/features/proposals/pages/__tests__/ProposalDetailPage.test.tsx`

**O que cobrir (list):**
- Renderiza tabela com mock de 3 propostas
- Filtro por status filtra corretamente
- Click em linha navega para detail

**O que cobrir (detail):**
- Renderiza header da proposta + abas
- ExportMenu abre com 2 opcoes (Excel, PDF)
- Erro de export exibe Alert/Snackbar (testa cenario M-07 de F2-DT-B)
- Botao Excluir: presente OU ausente conforme decisao da F2-DT-B
  (verificar codigo de F2-DT-B antes de assertar)

**MSW handlers:**
- `GET /api/v1/propostas` -> 3 propostas
- `GET /api/v1/propostas/:id` -> 1 proposta
- `GET /api/v1/propostas/:id/export.xlsx` -> erro 500 (testar handling)

### Commit unico

Mensagem: `test(f2-dt-c): smoke tests for histograma, composicoes, propostas`

## 5. Restricoes Criticas

- **Branch `main` apenas.** Sem feature branches.
- **1 commit unico** com todos os testes.
- `npm run test` deve passar (4 arquivos de teste, 12+ asserts).
- `npm run build` continua verde.
- Apenas arquivos novos em `**/__tests__/**` — nao modificar codigo de
  producao.

## 6. Artefatos Obrigatorios Antes de TESTED

- `docs/sprints/F2-DT-C/technical-review/technical-review-YYYY-MM-DD-f2-dt-c.md`
- `docs/sprints/F2-DT-C/walkthrough/done/walkthrough-F2-DT-C.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-DT-C
  `TODO -> TESTED`

## 7. Fora de Escopo

- Cobertura E2E (Playwright/Cypress)
- Testes de unidade de hooks/utils isoladamente (apenas integracao via
  componentes)
- Performance/load testing
- Visual regression
- Modificar codigo de producao para testabilidade — se algo for
  intestavel, registrar no walkthrough como debito.

## 8. Itens Fechados

C-01 kimi (parcial — agora completo: scaffold + smoke tests).
