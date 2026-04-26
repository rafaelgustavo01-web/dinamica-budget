# Technical Review — Sprint F2-08

**Data:** 2026-04-26
**Sprint:** F2-08 — RBAC por Proposta (desacoplar de cliente)
**Worker:** kimi-k2.5
**Status:** TESTED

---

## Resumo da Implementação

Desacoplada autorização de Propostas do `cliente_id`. Autorização operacional agora é dada por papel na proposta (OWNER/EDITOR/APROVADOR), com VIEWER como default implícito.

## Arquivos Alterados/Criados

| Arquivo | Ação |
|---|---|
| `app/backend/models/enums.py` | Adicionado `PropostaPapel` |
| `app/backend/models/proposta.py` | Adicionado `PropostaAcl` model + relationship |
| `app/alembic/versions/021_proposta_acl.py` | Migration com enum, tabela e backfill OWNER |
| `app/backend/repositories/proposta_acl_repository.py` | CRUD + bulk loader + count_owners |
| `app/backend/services/proposta_acl_service.py` | Regras + last-owner guard |
| `app/backend/core/dependencies.py` | Adicionado `require_proposta_role` |
| `app/backend/core/exceptions.py` | Adicionado `UnprocessableEntityError` |
| `app/backend/services/proposta_service.py` | `criar_proposta` concede OWNER automaticamente |
| `app/backend/api/v1/endpoints/propostas.py` | Refatorado para RBAC por proposta |
| `app/backend/api/v1/endpoints/pq_importacao.py` | Refatorado |
| `app/backend/api/v1/endpoints/cpu_geracao.py` | Refatorado |
| `app/backend/api/v1/endpoints/proposta_export.py` | Refatorado |
| `app/backend/api/v1/endpoints/proposta_recursos.py` | Refatorado |
| `app/backend/api/v1/endpoints/proposta_acl.py` | Criado — CRUD de ACL |
| `app/backend/api/v1/router.py` | Registrado `proposta_acl` |
| `app/backend/schemas/proposta.py` | `meu_papel`, `PropostaAclResponse`, `PropostaAclCreate` |
| `app/backend/tests/unit/test_proposta_acl_service.py` | 5 testes |
| `app/backend/tests/unit/test_proposta_acl_dependency.py` | 7 testes |
| `app/backend/tests/unit/test_proposta_acl_endpoints.py` | 5 testes |
| `app/backend/tests/unit/test_propostas_rbac_refactor.py` | 8 testes |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Tipos + métodos ACL |
| `app/frontend/src/features/proposals/components/ProposalShareDialog.tsx` | Modal compartilhamento |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | UI condicional |
| `app/frontend/src/features/proposals/pages/ProposalsListPage.tsx` | Filtro opcional + coluna meu_papel |

## Testes

- 158 pytest unitários PASS, 0 FAIL
- `npx tsc --noEmit` sem erros

## Decisões Técnicas

- VIEWER não é armazenado — é o default implícito
- ADMIN global bypassa via `is_admin`
- Backfill na migration: criador vira OWNER
- Last-OWNER guard: não pode revogar último OWNER
- Bulk loader em GET /propostas evita N+1
