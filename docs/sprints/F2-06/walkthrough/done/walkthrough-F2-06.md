# Walkthrough — Sprint F2-06

**Data:** 2026-04-26
**Sprint:** F2-06 — UX Complementar (Edição de PQ, Filtros, Duplicação)
**Worker:** claude-sonnet-4-6
**Status:** TESTED

---

## Resumo

Fechamento dos fluxos pós-importação que exigiam retrabalho manual: edição de PqItem após upload, filtros na lista de propostas e duplicação de proposta como base para nova.

---

## Tasks Concluídas

- [x] Task 1: Schema `PqItemUpdateRequest` + `repo.update_dados`
- [x] Task 2: Endpoint `PATCH /propostas/{id}/pq/itens/{item_id}`
- [x] Task 3: Service `duplicar_proposta` + endpoint `POST /propostas/{id}/duplicar`
- [x] Task 4: Filtros em `GET /propostas/` (status, data_inicial, data_final, q)
- [x] Task 5: `proposalsApi` — 3 métodos novos (`updatePqItem`, `duplicarProposta`, filtros em `list`)
- [x] Task 6: Componente `PqItensEditableTable` (tabela inline editável)
- [x] Task 7: Componente `ProposalFiltersBar` + integração em `ProposalsListPage`
- [x] Task 8: Componente `DuplicarPropostaDialog` + botão em `ProposalsTable`
- [x] Task 9: Wire `PqItensEditableTable` em `ProposalImportPage`
- [x] Task 10: Validação final

---

## Arquivos Alterados/Criados

| Arquivo | Ação |
|---|---|
| `app/backend/schemas/proposta.py` | `PqItemUpdateRequest` adicionado |
| `app/backend/repositories/pq_item_repository.py` | `update_dados` adicionado |
| `app/backend/repositories/proposta_repository.py` | `list_by_cliente` com filtros |
| `app/backend/services/proposta_service.py` | `duplicar_proposta` adicionado |
| `app/backend/api/v1/endpoints/pq_importacao.py` | `PATCH /pq/itens/{item_id}` |
| `app/backend/api/v1/endpoints/propostas.py` | filtros em GET + `POST /{id}/duplicar` |
| `app/backend/tests/unit/test_pq_item_edit.py` | Criado |
| `app/backend/tests/unit/test_proposta_duplicar.py` | Criado |
| `app/backend/tests/unit/test_proposta_filtros.py` | Criado |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | 3 métodos novos |
| `app/frontend/src/features/proposals/components/PqItensEditableTable.tsx` | Criado |
| `app/frontend/src/features/proposals/components/ProposalFiltersBar.tsx` | Criado |
| `app/frontend/src/features/proposals/components/DuplicarPropostaDialog.tsx` | Criado |
| `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx` | Tabela editável adicionada |
| `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx` | Filtros integrados |
| `app/frontend/src/features/proposals/components/ProposalsTable.tsx` | Coluna "Duplicar" adicionada |

---

## Validações

```bash
cd app
python -m pytest backend/tests/ -q
# 143 passed, 0 failed

cd app/frontend
npx tsc --noEmit
# 0 erros
```

---

## Notas para o QA

- Bug de debounce corrigido pelo QA durante revisão (estado de busca não era limpo ao trocar de cliente).
- Duplicação não clona CPU — comportamento correto conforme briefing.
- Filtros combináveis: status AND período AND busca textual.
