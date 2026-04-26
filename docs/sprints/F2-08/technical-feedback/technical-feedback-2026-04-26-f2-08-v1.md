# Technical Feedback — F2-08 (QA Review)

## Sprint
F2-08 — RBAC por Proposta (desacoplar de cliente)

## Data
2026-04-26

## QA
Amazon Q

## Status
**ACCEPTED → DONE**

---

## Verificação QA

| Item | Resultado |
|---|---|
| Walkthrough | `docs/sprints/F2-08/walkthrough/reviewed/walkthrough-F2-08.md` |
| Technical Review | `docs/sprints/F2-08/technical-review/technical-review-2026-04-26-f2-08.md` |
| Migration 021 | ✅ Presente e correta (`app/alembic/versions/021_proposta_acl.py`) |
| Testes unitários | ✅ 158 passed, 0 failed (25 testes novos em 4 arquivos) |
| TypeScript | ✅ 0 erros (`npx tsc --noEmit`) |

---

## Validação dos 4 Pontos de Atenção

### 1. Backfill da migration 021 ✅
- Migration `021_proposta_acl.py` confirmada com `down_revision = "020"` e `revision = "021"`.
- Backfill via `INSERT INTO operacional.proposta_acl ... SELECT ... FROM operacional.propostas WHERE criado_por_id IS NOT NULL` — correto e atômico.
- Enum `proposta_papel_enum` criado com `checkfirst=True` — idempotente.
- `downgrade` remove tabela e enum corretamente.

### 2. Bulk loader em GET /propostas ✅
- `test_propostas_rbac_refactor.py` confirma uso de `PropostaAclRepository.get_papeis_bulk(proposta_ids, current_user.id)` — 1 query para todos os IDs, sem N+1.
- Teste `test_get_lista_contem_meu_papel` valida que `meu_papel` é hidratado corretamente por item.

### 3. Enum `proposta_papel_enum` pronto para F2-10 ✅
- Enum criado no Postgres com 3 valores: `OWNER`, `EDITOR`, `APROVADOR`.
- `VIEWER` não entra no enum — é default implícito. Correto conforme briefing.
- F2-10 adicionará `COMPRADOR` via nova migration (024) sem conflito.

### 4. Regressão dos 5 routers refatorados ✅
- `test_propostas_rbac_refactor.py` cobre 8 cenários: POST sem dono de cliente → 201, PATCH como VIEWER → 403, PATCH como EDITOR → 200, DELETE como EDITOR → 403, DELETE como OWNER → 204, DELETE como ADMIN → 204, GET sem cliente_id → 200, GET com meu_papel correto.
- `test_proposta_acl_dependency.py` cobre 7 cenários da dependency `require_proposta_role` incluindo admin bypass, hierarquia EDITOR > APROVADOR e múltiplos papéis.

---

## Critérios de Aceite

- [x] Tabela `proposta_acl` criada com migration 021 + backfill OWNER
- [x] Enum `proposta_papel_enum` (OWNER/EDITOR/APROVADOR) — VIEWER não entra
- [x] `require_proposta_role` implementado com bypass `is_admin`
- [x] 5 routers refatorados: `propostas.py`, `pq_importacao.py`, `cpu_geracao.py`, `proposta_export.py`, `proposta_recursos.py`
- [x] `criar_proposta` cria OWNER automaticamente na mesma transação
- [x] `GET /propostas` sem `cliente_id` obrigatório + campo `meu_papel` com bulk loader
- [x] Somente OWNER deleta proposta
- [x] Last-OWNER guard: não pode revogar último OWNER (422)
- [x] `GET/POST/DELETE /propostas/{id}/acl` com gating OWNER
- [x] Frontend: `ProposalShareDialog` (só OWNER), botões condicionais em `ProposalDetailPage`, coluna `meu_papel` em `ProposalsListPage`
- [x] 158 pytest PASS, 0 FAIL
- [x] 0 erros `npx tsc --noEmit`

---

## Confirmed Wins

- `app/alembic/versions/021_proposta_acl.py`: migration sintaticamente correta, backfill atômico, downgrade limpo.
- `test_proposta_acl_service.py` (5 testes): last-owner guard, idempotência de concessão, papel efetivo com múltiplos papéis, None para usuário sem ACL.
- `test_proposta_acl_dependency.py` (7 testes): todos os cenários de hierarquia cobertos, admin bypass validado.
- `test_proposta_acl_endpoints.py` (5 testes): CRUD de ACL com gating correto, 422 no last-owner.
- `test_propostas_rbac_refactor.py` (8 testes): regressão completa dos endpoints refatorados.

## Findings

### Low
- Walkthrough foi colocado diretamente em `reviewed/` sem passar por `done/` — violação menor do fluxo documental. Sem impacto funcional.
- `test_proposta_acl_service.py`: `test_count_owners_correto` testa o mock diretamente (`svc.repo.count_owners`) em vez de testar o método do service — cobertura superficial neste caso específico. Não é bloqueador.

---

## Scorecard

| Critério | Resultado |
|---|---|
| Escopo do plano entregue | YES |
| Testes aceitáveis | YES |
| Lint aceitável | YES |
| Documentação completa | YES |
| Estado do backlog correto | YES — atualizar para DONE |

---

## Closeout

- Walkthrough já em `reviewed/` ✅
- BACKLOG.md: atualizar F2-08 de `TESTED` para `DONE`
- Desbloqueia: F2-09, F2-10, F2-11, F2-12, F2-13

## Decisão

Sprint F2-08 → **DONE**.
