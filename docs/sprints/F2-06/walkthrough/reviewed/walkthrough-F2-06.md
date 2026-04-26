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
- [x] Task 5: `proposalsApi` — 3 métodos novos
- [x] Task 6: Componente `PqItensEditableTable`
- [x] Task 7: Componente `ProposalFiltersBar` + integração em `ProposalsListPage`
- [x] Task 8: Componente `DuplicarPropostaDialog` + botão em `ProposalsTable`
- [x] Task 9: Wire `PqItensEditableTable` em `ProposalImportPage`
- [x] Task 10: Validação final

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

## Notas

- Bug de debounce corrigido pelo QA durante revisão.
- Duplicação não clona CPU — comportamento correto conforme briefing.
- Filtros combináveis: status AND período AND busca textual.
