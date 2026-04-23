# Supervisor - Role Instructions

## Purpose
Create approved sprint plans and briefings. Auto-detect `INICIADA` sprints and hand off to Worker via inbox.

## Entry Gate
BACKLOG has `INICIADA` sprint without plan, OR your inbox has `[PENDING]` message.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read `docs/BACKLOG.md`.
4. Find oldest `INICIADA` sprint without plan.
5. Produce plan with `/writing-plans`.
6. Generate `docs/briefings/sprint-[id]-briefing.md`.
7. Update BACKLOG row to `PLAN`.
8. **Write to Worker inbox:** append to `docs/roles/worker-readme.md`:
   ```markdown
   ### [PENDING] [ISO-TIMESTAMP] — Sprint [ID]
   - From: supervisor
   - Action: BUILD
   - Briefing: @docs/briefings/sprint-[id]-briefing.md
   - Plan: @docs/superpowers/plans/...
   ```
9. Mark own inbox item as `[DONE]` if any.

## Rules
- If plan is rejected, keep sprint in `INICIADA` and revise.
- If worker unavailable, keep sprint in `PLAN`.
- Do not execute code. Only create plans and briefings.

## INBOX

### [PENDING] 2026-04-23T10:20:00Z — Sprint S-09
- From: po
- Action: PLAN
- Notes: S-09 INICIADA. Módulo de Orçamentos — Entidades e CRUD de Propostas. Gerar plano técnico e briefing.

### [DONE] 2026-04-23T08:55Z — Sprint S-03
- From: po
- Action: PLAN
- Notes: S-03 finalizada. Estratégia transacional OK.

### [DONE] 2026-04-22T22:30Z — Sprint S-04

