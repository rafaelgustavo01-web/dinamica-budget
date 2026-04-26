# Worker Prompt — Sprint F2-08

**Para:** Kimi K2.5 (kimi-k2.5)
**Modo:** Agent / BUILD
**Sprint:** F2-08 — RBAC por Proposta (desacoplar de cliente)
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget
**Prioridade:** P0 (gap de seguranca ativo)

---

Voce e o worker da Sprint F2-08. Implemente o plano completo em `docs/sprints/F2-08/plans/2026-04-26-rbac-por-proposta.md` do inicio ao fim sem pausas.

## Por que voce foi escolhido

Esta sprint e majoritariamente backend de seguranca:

- Migration com backfill critico (proposta sem OWNER = proposta orfa)
- Refator de 5 routers preservando contratos
- Nova dependency com hierarquia de papeis e bypass admin
- Bulk loader para evitar N+1 em `GET /propostas`
- Frontend modesto: 1 dialog novo + ajuste de visibilidade de botoes

Sua experiencia com SQLAlchemy async, Alembic, e refator de seguranca em endpoints faz match com o trabalho. Frontend e pequeno o suficiente para nao bloquear o pacote.

## Instrucoes de execucao

1. **OBRIGATORIO antes de codar**: leia em ordem os 11 documentos/arquivos listados na secao "Pre-requisito de leitura" do briefing.
2. Leia o briefing em `docs/sprints/F2-08/briefing/sprint-F2-08-briefing.md`
3. Leia o plano em `docs/sprints/F2-08/plans/2026-04-26-rbac-por-proposta.md`
4. Execute cada task em ordem, commitando apos cada uma
5. Apos cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
6. Apos cada task de frontend: `cd app/frontend && npx tsc --noEmit`
7. Ao concluir TODAS as tasks: crie
   - `docs/sprints/F2-08/technical-review/technical-review-2026-04-26-f2-08.md`
   - `docs/sprints/F2-08/walkthrough/done/walkthrough-F2-08.md`
   - Atualize status do sprint para TESTED em `docs/shared/governance/BACKLOG.md`

## Atencao especial

- **Mudanca de comportamento INTENCIONAL em `GET /propostas`**: deixa de exigir `cliente_id` na query string. Frontend antigo passara a receber TUDO. A coluna `meu_papel` permite ao usuario distinguir o que e dele do que e visivel-mas-nao-editavel.
- **`POST /propostas` deixa de checar acesso ao cliente**: agora qualquer usuario autenticado pode criar proposta para qualquer cliente. Esta e a mudanca de produto pedida pelo PO.
- **Backfill da migration e critico**: deve usar `gen_random_uuid()` para PK. Validar com query manual antes de marcar como done.
- **VIEWER NAO entra no enum Postgres** — apenas OWNER, EDITOR, APROVADOR. Em Python, "VIEWER ou superior" = `PropostaPapel | None`.
- **Last-OWNER guard**: implementar em `PropostaAclService.revogar` — `if papel == OWNER and count_owners == 1: raise UnprocessableEntityError`. Cobrir com teste.
- **`criar_proposta` cria OWNER na mesma transacao**: nao usar `db.commit()` no meio. Use `db.flush()` se precisar do `proposta.id` antes do commit.
- **Bulk loader em `GET /propostas`**: 1 query unica em `proposta_acl` para os `proposta_ids` da pagina. NAO uma query por proposta.
- **Substituicao de `require_cliente_access`**: identifique todas as ocorrencias com Grep antes de comecar — pode haver chamadas que nao estao listadas no plano (ex: novos endpoints de F2-05/06/07).
- **NAO implementar workflow de aprovacao**: APROVADOR existe no enum, mas as acoes `enviar-aprovacao`/`aprovar`/`rejeitar` sao da F2-09. Esta sprint apenas reconhece o papel.
- **Frontend `is_admin` precisa estar disponivel no contexto de auth**: verificar se `useCurrentUser()` ja expoe; se nao, adicionar.
- **Encoding UTF-8 limpo**: docs e codigo sem mojibake. ASCII puro em strings de codigo.
- **Conflito potencial em `proposalsApi.ts`**: ja modificado por F2-05/06/07. Adicionar tipos/metodos novos no FINAL do arquivo, sem reescrever blocos existentes.

## Criterios de conclusao

- Migration 021 sintaticamente correta + backfill validado (count proposta_acl OWNER == count propostas com criado_por_id)
- 145+ PASS, 0 FAIL no pytest (preserva regressao das sprints anteriores)
- 0 erros no `tsc --noEmit`
- Todos os 8 tasks com checkbox marcado
- 5 endpoints de proposta refatorados (`require_cliente_access` removido)
- `criar_proposta` cria OWNER automaticamente
- Last-OWNER guard funcional e testado
- `GET /propostas` retorna `meu_papel` sem N+1
- `ProposalShareDialog` renderiza, lista ACL, permite adicionar/remover
- `ProposalDetailPage` esconde Excluir para nao-OWNER, esconde Editar para VIEWER
- `ProposalsListPage` deixa cliente_id como filtro opcional, mostra coluna meu_papel
- Documentos technical-review e walkthrough criados
- BACKLOG atualizado para TESTED

## Diretorio de trabalho

```
app/backend/models/enums.py
app/backend/models/proposta.py
app/alembic/versions/021_proposta_acl.py
app/backend/repositories/proposta_acl_repository.py
app/backend/services/proposta_acl_service.py
app/backend/services/proposta_service.py
app/backend/core/dependencies.py
app/backend/api/v1/endpoints/propostas.py
app/backend/api/v1/endpoints/pq_importacao.py
app/backend/api/v1/endpoints/cpu_geracao.py
app/backend/api/v1/endpoints/proposta_export.py
app/backend/api/v1/endpoints/proposta_recursos.py
app/backend/api/v1/endpoints/proposta_acl.py
app/backend/api/v1/router.py
app/backend/schemas/proposta.py
app/backend/tests/unit/test_proposta_acl_service.py
app/backend/tests/unit/test_proposta_acl_dependency.py
app/backend/tests/unit/test_proposta_acl_endpoints.py
app/backend/tests/unit/test_propostas_rbac_refactor.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/components/ProposalShareDialog.tsx
app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
app/frontend/src/features/proposals/pages/ProposalsListPage.tsx
```

## Commits esperados (sequencia minima)

1. `feat(f2-08): add PropostaAcl model and migration 021 with backfill`
2. `feat(f2-08): add proposta_acl repository and service with last-owner guard`
3. `feat(f2-08): add require_proposta_role dependency with admin bypass`
4. `refactor(f2-08): replace require_cliente_access with require_proposta_role across proposta endpoints`
5. `feat(f2-08): add proposta_acl CRUD endpoints (OWNER-gated)`
6. `feat(f2-08): add proposta ACL API client and ProposalShareDialog`
7. `feat(f2-08): conditional UI actions based on proposta_acl role`
8. `docs(f2-08): add technical-review and walkthrough, handoff to QA`
