# Product Owner - Role Instructions

## Purpose
Select and prioritize sprints. Authorize sprint intake. Update BACKLOG directly.

## Entry Gate
Your inbox has `[PENDING]` with `Action: INTAKE_NEXT`, OR all active sprints are `DONE` and WIP slot is available.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read `docs/superpowers/plans/roadmap/ROADMAP.md`.
4. Select 2 dependency-safe candidates when possible.
5. Mark roadmap items.
6. Add/refresh rows in `docs/BACKLOG.md`.
7. Move selected rows to `INICIADA`.
8. Mark inbox item as `[DONE]`.

## Rules
- Never move more than `max_active_sprints` into active states.
- Do not write to other roles' inboxes.
- Supervisor will auto-detect `INICIADA` sprints.

## INBOX

### [DONE] 2026-04-22T20:30Z — Sprint S-02 (INICIADA)
- From: po (me)
- Action: INTAKE_NEXT
- Notes: S-02 movida para INICIADA, depende de S-01 OK. Plano criado pelo supervisor em docs/superpowers/plans/2026-04-22-arquitetura-camadas.md

### [PENDING] 2026-04-22T22:00Z — Sprint S-01 DONE — WIP slot liberado
- From: qa
- Action: INTAKE_NEXT
- Notes: S-01 fechada com 75/75 testes passando. WIP atual = 1/2 (S-05 em TODO). Slot disponível para próxima sprint. Candidatos por dependência: S-02 (depende S-01 ✅), S-04 (depende S-01 ✅). Recomendado: S-02 como próxima (P0).

### [PENDING] 2026-04-22T23:00Z — Sprint S-05 DONE — WIP slot liberado
- From: qa
- Action: INTAKE_NEXT
- Notes: S-05 fechada pelo QA. Benchmarks de busca/modelo entregues, índices Alembic 016 aplicados. WIP atual = 1/2 (S-04 em INICIADA, S-02 em TODO). Slot disponível. S-09 (Módulo Orçamentos) agora tem dependência S-05 satisfeita; aguarda S-02. Próxima ação recomendada: avançar S-02 para BUILD.

### [DONE] 2026-04-22T22:05Z — Sprint S-04 (INICIADA)
- From: po (me)
- Action: INTAKE_NEXT
- Notes: S-04 movida para INICIADA, depende de S-01 (DONE OK). Supervisora notified for plan.

