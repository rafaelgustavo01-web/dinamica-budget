# Technical Review — Sprint F2-03
**Data:** 2026-04-26
**Sprint:** F2-03 — Tela de Revisão de Match
**Worker:** claude-sonnet-4-6

---

## Status de Entrega

Todos os 7 tasks concluídos com sucesso.

- **Backend:** 124 passed, 0 failed (pytest)
- **Frontend:** 0 erros (tsc --noEmit)

---

## Arquivos Modificados/Criados

| Arquivo | Ação |
|---|---|
| `app/backend/schemas/proposta.py` | Adicionados `PqItemResponse`, `PqMatchConfirmarRequest` |
| `app/backend/api/v1/endpoints/pq_importacao.py` | Adicionados `GET /itens` e `PATCH /itens/{id}/match` |
| `app/backend/tests/unit/test_pq_match_review.py` | Criado (6 testes) |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Tipos + `listPqItens`, `confirmarMatch` |
| `app/frontend/src/features/proposals/pages/MatchReviewPage.tsx` | Criado |
| `app/frontend/src/features/proposals/components/MatchItemRow.tsx` | Criado |
| `app/frontend/src/features/proposals/components/ServicoPickerDialog.tsx` | Criado |
| `app/frontend/src/features/proposals/routes.tsx` | Rota `/propostas/:id/match-review` adicionada |
| `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx` | Botão "Revisar e Confirmar Match" após match |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Botão "Revisar Match" na barra de ações |

---

## Decisões Técnicas

- **`model_validator(mode='after')`** em vez de `field_validator` para `PqMatchConfirmarRequest.substituir_requer_servico` — Pydantic v2 não chama `field_validator` para campos com valor default não fornecido; `model_validator` é chamado após todos os campos serem validados.
- **`TipoServicoMatch` mapeado no frontend** via `origem_match === 'PROPRIA_CLIENTE'` → `ITEM_PROPRIO`, demais → `BASE_TCPO`.
- **`status_match` query param** opcional em `GET /itens` permite filtrar por status sem paginar no primeiro release.
- A ação `substituir` exige `servico_match_tipo` além de `servico_match_id` — validado tanto no schema Pydantic quanto no endpoint.

---

## Critérios de Aceite — Verificação

| Critério | Status |
|---|---|
| GET /propostas/{id}/pq/itens retorna lista de PqItems | ✅ |
| PATCH /propostas/{id}/pq/itens/{item_id}/match aceita confirmar/substituir/rejeitar | ✅ |
| Página /propostas/:id/match-review com tabela e barra de progresso | ✅ |
| Botões de ação por linha: confirmar (verde), substituir (diálogo), rejeitar (vermelho) | ✅ |
| Botão "Revisar Match" em ProposalDetailPage | ✅ |
| Botão "Revisar e Confirmar Match" em ProposalImportPage após match | ✅ |
| npx tsc --noEmit sem erros | ✅ (0 erros) |
| python -m pytest backend/tests/ com 110+ PASS, 0 FAIL | ✅ (124 PASS, 0 FAIL) |

---

## Riscos / Observações

- Itens com `match_status` diferente de `SUGERIDO` ou `PENDENTE` não exibem botões de ação (comportamento correto — evita re-processamento acidental).
- Campo `quantidade` editável no PATCH mas não exposto na UI desta sprint — previsto para F2-06.
- 11 erros pré-existentes em testes de integração (requerem infraestrutura de banco) — não relacionados a esta sprint.
