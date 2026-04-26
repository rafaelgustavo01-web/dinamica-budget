# Sprint F2-08 — Briefing

**Sprint:** F2-08
**Titulo:** RBAC por Proposta (desacoplar de cliente)
**Worker:** kimi-k2.5
**Status:** BACKLOG → INICIADA
**Data:** 2026-04-26
**Prioridade:** P0 (gap de seguranca ativo)

---

## Origem

Revisao critica do "plano gpt" (`docs/plano gpt.md`, secao 10) confirmou que o RBAC atual de Propostas esta conceitualmente errado:

- Hoje, todo endpoint de proposta gateia por `require_cliente_access(proposta.cliente_id, ...)`.
- Isso significa: usuario sem vinculo ao cliente da proposta nao enxerga nem mexe na proposta.
- Regra correta de negocio (confirmada pelo PO em 2026-04-26): qualquer usuario autenticado pode ver/criar propostas para qualquer cliente. Autorizacao operacional (editar, aprovar, deletar) e dada por papel **na proposta**, nao por vinculo ao cliente.

## Objetivo

Substituir gating por cliente por gating por papel-na-proposta:

1. **Nova tabela** `operacional.proposta_acl(id, proposta_id, usuario_id, papel, created_by, ...)` com 3 papeis: `OWNER`, `EDITOR`, `APROVADOR`.
2. **VIEWER e default implicito** de qualquer usuario autenticado — NAO mora na tabela.
3. **ADMIN global** (`users.is_admin = true`) bypassa qualquer checagem.
4. **Migration 021** com backfill: criador de cada proposta existente vira `OWNER`.
5. **Substituir** `require_cliente_access` por novo `require_proposta_role(proposta_id, papel_minimo)` em 5 routers.
6. **`GET /propostas`** deixa de exigir `cliente_id` e retorna todas as propostas com campo `meu_papel`.
7. **CRUD de ACL** (`GET/POST/DELETE /propostas/{id}/acl`) — somente OWNER pode gerenciar.
8. **Frontend**: modal "Compartilhar proposta" + esconder botoes de edit/delete conforme papel.

## Hierarquia de Papeis

```
ADMIN global (is_admin=true)  >  OWNER  >  EDITOR  >  APROVADOR  >  VIEWER (implicito)
```

| Papel | Pode | Onde mora |
|---|---|---|
| ADMIN | tudo (bypass) | `users.is_admin` |
| OWNER | tudo + delete + gerenciar ACL | `proposta_acl` |
| EDITOR | criar/editar/importar/gerar CPU | `proposta_acl` |
| APROVADOR | aprovar/rejeitar (escopo F2-09) + ver | `proposta_acl` |
| VIEWER | apenas ler | implicito (default) |

## Criterios de Aceite

- Tabela `proposta_acl` criada (migration 021) com `UniqueConstraint(proposta_id, usuario_id, papel)`
- Enum `proposta_papel_enum` (OWNER/EDITOR/APROVADOR) — VIEWER NAO entra
- Backfill: toda proposta com `criado_por_id` recebe linha OWNER
- `require_proposta_role(proposta_id, papel_minimo)` implementado com bypass `is_admin`
- 5 routers refatorados: `propostas.py`, `pq_importacao.py`, `cpu_geracao.py`, `proposta_export.py`, `proposta_recursos.py`
- `criar_proposta` cria automaticamente OWNER para o criador (mesma transacao)
- `GET /propostas` sem `cliente_id` obrigatorio + campo `meu_papel` na resposta (bulk loader, sem N+1)
- Somente OWNER deleta proposta
- Last-OWNER guard: nao pode revogar o ultimo OWNER (422)
- `GET/POST/DELETE /propostas/{id}/acl` com gating OWNER
- Frontend: `ProposalShareDialog` (so OWNER), botoes condicionais em `ProposalDetailPage`, coluna `meu_papel` em `ProposalsListPage`
- 145+ pytest PASS, 0 FAIL (preserva regressao das sprints anteriores)
- 0 erros `npx tsc --noEmit`

## Plano

Arquivo: `docs/sprints/F2-08/plans/2026-04-26-rbac-por-proposta.md`

8 tasks:
1. Backend — enum + model + migration 021 com backfill
2. Backend — repository + service de ACL (last-owner guard)
3. Backend — `require_proposta_role` dependency (com testes)
4. Backend — refator dos 5 endpoints + `criar_proposta` cria OWNER + `meu_papel` em PropostaResponse (bulk loader)
5. Backend — endpoints CRUD de ACL (gating OWNER)
6. Frontend — proposalsApi + `ProposalShareDialog`
7. Frontend — esconder acoes condicionais em DetailPage e ListPage
8. Validacao final + technical-review + walkthrough + BACKLOG TESTED

## Pre-requisito de leitura (CRITICO)

Antes de codar, leia em ordem:

1. `docs/shared/superpowers/plans/roadmap/ROADMAP.md` — Milestone 6, Fase 6.6
2. `docs/plano gpt.md` — Secao 10 (origem) + RESPEITAR a correcao no ROADMAP (PO descartou ACL como gating de leitura)
3. `app/backend/core/dependencies.py` — `require_cliente_access`, `require_cliente_perfil`
4. `app/backend/api/v1/endpoints/propostas.py` — onde `require_cliente_access` e chamado
5. `app/backend/api/v1/endpoints/pq_importacao.py`
6. `app/backend/api/v1/endpoints/cpu_geracao.py`
7. `app/backend/api/v1/endpoints/proposta_export.py`
8. `app/backend/api/v1/endpoints/proposta_recursos.py`
9. `app/backend/models/usuario.py` — `is_admin`
10. `app/backend/models/proposta.py` — `Proposta.criado_por_id`
11. `app/alembic/versions/020_add_proposta_resumo_recursos_table.py` — padrao de migration mais recente

**Antes de codar, mentalmente responda:**
- VIEWER mora em `proposta_acl`? **Resposta:** NAO — implicito.
- O que faz `is_admin = true`? **Resposta:** bypass total.
- ACL e por `proposta_id` ou `proposta_root_id`? **Resposta:** `proposta_id` nesta sprint. F2-09 migra para root.
- Quem pode revogar o ultimo OWNER? **Resposta:** ninguem (422).

## Contexto tecnico

- Schema Postgres: `operacional`
- Migration mais recente: `020_add_proposta_resumo_recursos_table.py`
- Repo pattern: `BaseRepository[Model]` em `app/backend/repositories/base_repository.py`
- Logging: `from backend.core.logging import get_logger` (structlog)
- Frontend: padrao MUI Dialog + Autocomplete + TanStack Query v5
- Endpoint de listagem de usuarios: verificar se existe; senao, criar consulta minima `GET /users?ativos=true` (escopo desta sprint se necessario)

## Dependencias

- F2-03 DONE (usado para PqImportacao endpoints)
- F2-04 DONE (CPU)
- F2-07 DONE (proposta_recursos endpoint a ser refatorado)

## Atencao especial (kimi)

- **Refator de endpoints DEVE preservar contratos de resposta** — apenas o gating muda. Status codes 200/201/204 mantidos. 403 substitui 403 anterior (mesma natureza).
- **Backfill na migration e CRITICO** — propostas existentes precisam de OWNER, senao usuarios perdem acesso ao deploy. Validar com `SELECT count(*) FROM proposta_acl WHERE papel = 'OWNER'` = `SELECT count(*) FROM propostas WHERE criado_por_id IS NOT NULL`.
- **VIEWER nao entra no enum Postgres** — so OWNER, EDITOR, APROVADOR. Codigo Python pode usar `PropostaPapel | None` para representar "VIEWER ou superior".
- **Bulk loader em `GET /propostas`** — evite N+1. Faca 1 query em `proposta_acl` para `(proposta_ids, current_user.id)` e mapeie em dict.
- **Last-OWNER guard** no service: `if papel == OWNER and count_owners(proposta_id) == 1: raise UnprocessableEntityError("Proposta nao pode ficar sem OWNER")`. Sem isso, alguem pode tornar a proposta orfa.
- **`criar_proposta`**: a concessao de OWNER deve estar na MESMA sessao SQLAlchemy do insert da proposta. NAO commit no meio.
- **Encoding UTF-8 limpo**, sem mojibake. ASCII puro em strings de codigo.
- **NAO implementar workflow de aprovacao agora** — APROVADOR existe no enum mas o fluxo `enviar-aprovacao`/`aprovar`/`rejeitar` e da F2-09. Apenas garantir que o papel e validavel.
