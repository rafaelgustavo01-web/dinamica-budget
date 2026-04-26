# Technical Review — Sprint F2-06

**Data:** 2026-04-26
**Sprint:** F2-06 — UX Complementar (Edição de PQ, Filtros, Duplicação)
**Worker:** claude-sonnet-4-6
**Status:** TESTED

---

## Resumo das Mudanças

### Backend — 3 endpoints atômicos

| Endpoint | Descrição |
|---|---|
| `PATCH /propostas/{id}/pq/itens/{item_id}` | Edição parcial de PqItem (descricao/qtd/unidade/observacao) |
| `POST /propostas/{id}/duplicar` | Clona proposta em RASCUNHO; PqItens resetados para PENDENTE; CPU não clonada |
| `GET /propostas/` (filtros) | Aceita `status`, `data_inicial`, `data_final`, `q` (busca ILIKE em codigo/titulo) |

### Frontend — 3 componentes novos + 3 páginas tocadas

| Componente/Página | Mudança |
|---|---|
| `PqItensEditableTable.tsx` | Tabela inline editável com botões editar/salvar/cancelar por linha |
| `ProposalFiltersBar.tsx` | Barra com Select de status, DatePicker de período, TextField debounced (300ms) |
| `DuplicarPropostaDialog.tsx` | Modal de confirmação com navegação para nova proposta |
| `ProposalImportPage.tsx` | Renderiza `PqItensEditableTable` após upload bem-sucedido |
| `ProposalsListPage.tsx` | Integra `ProposalFiltersBar`; filtros passados ao `proposalsApi.list` |
| `ProposalsTable.tsx` | Coluna de ações com botão "Duplicar" por linha |

### API Client
- `proposalsApi.ts`: adicionados `updatePqItem`, `duplicarProposta`, parâmetros de filtro em `list`

---

## Decisões Técnicas

- Duplicação **não** clona `PropostaItem` (CPU) nem composições — usuário regera via match → CPU.
- Filtros são combináveis (status AND período AND busca), não excludentes.
- Debounce de 300ms implementado via `useEffect + setTimeout` sem dependência nova.
- Edição client-side valida `qtd >= 0` e `descricao não vazia` antes do submit.
- Encoding: strings literais em testes sem caracteres especiais para evitar mojibake.

---

## Checklist de Validação

- [x] `PATCH /pq/itens/{id}` persiste descricao/qtd/unidade
- [x] `POST /duplicar` cria proposta em RASCUNHO com PqItens PENDENTE
- [x] `GET /propostas/` aceita e combina todos os filtros
- [x] `PqItensEditableTable` com edição inline funcional
- [x] `ProposalFiltersBar` com debounce de 300ms
- [x] `DuplicarPropostaDialog` navega para nova proposta ao confirmar
- [x] 143+ pytest PASS, 0 FAIL
- [x] 0 erros tsc

---

## Riscos e Observações

- Bug de debounce identificado e corrigido pelo QA durante revisão (estado de busca não era limpo ao trocar de cliente).
- Filtros de data dependem do timezone do servidor — recomenda-se padronizar para UTC em sprints futuras.
