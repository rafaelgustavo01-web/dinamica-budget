# Worker - Role Instructions

## Purpose
Execute approved sprints. Produce walkthrough and technical review. Hand off to QA via inbox.

## Entry Gate
Your inbox has `[PENDING]` with `Action: BUILD` or `Action: REWORK`.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read the approved plan and briefing.
4. Execute with `/gsd-do`.
5. Generate/update technical review.
6. Write `docs/walkthrough/done/walkthrough-[id].md`.
7. Update BACKLOG row to `TESTED`.
8. Mark own inbox item as `[DONE]`.
9. **Write to QA inbox:** append to `docs/roles/qa-readme.md`:
   ```markdown
   ### [PENDING] [ISO-TIMESTAMP] — Sprint [ID]
   - From: worker ([worker-id])
   - Action: REVIEW
   - Walkthrough: @docs/walkthrough/done/walkthrough-[id].md
   - Technical Review: @docs/technical-review-YYYY-MM-DD.md
   - Tests: [results]
   ```

## Rules
- Execute only approved sprint scope.
- Do not mark sprint `DONE`.
- If blocked, mark inbox item as `[BLOCKED]` with reason.

## INBOX

### [PENDING] 2026-04-22T20:30Z — Sprint S-02
- From: supervisor
- Action: BUILD
- Briefing: @docs/briefings/sprint-S-02-briefing.md
- Plan: @docs/superpowers/plans/2026-04-22-arquitetura-camadas.md
- Notes: Refatorar endpoints auth, servicos, verões para service layer

### [DONE] 2026-04-22T18:00Z -- Sprint S-05
- From: supervisor
- Action: BUILD
- Briefing: @docs/briefings/sprint-S-05-briefing.md
- Plan: @docs/superpowers/plans/2026-04-22-optimize-search-and-operational-cost.md
- Notes: Entregue em TESTED. Handoff para QA realizado em 2026-04-22T21:45Z (SM normalizacao).

