# Worker Handoff Prompt — Sprint S-10

> Delivered by: Scrum Master / Supervisor (Kimi Code CLI)
> Date: 2026-04-23

```
Codex 5.3, you are the execution worker for sprint S-10 in project Dinamica Budget.

Read the briefing first:
@docs/sprints/S-10/briefing/sprint-S-10-briefing.md

Execute the approved plan:
@docs/sprints/S-06/plans/2026-04-23-importacao-pq-match-inteligente.md

Context files:
@docs/BACKLOG.md
@docs/JOB-DESCRIPTION.md

Worker assignment:
- Worker ID: codex-5.3
- Provider: OpenAI
- Mode: BUILD

Rules:
- Execute only the approved sprint scope (Tasks 1 through 8).
- Keep the sprint in the backlog state machine.
- Generate or update `docs/sprints/S-10/technical-review/technical-review-2026-04-23-s10.md`.
- Save the walkthrough to `docs/sprints/S-10/walkthrough/done/walkthrough-S-10.md`.
- Update `docs/BACKLOG.md` from `TODO` to `TESTED` when the sprint is complete.
- Do not mark the sprint `DONE`.
- This project uses ONLY the main branch. Do not create feature branches.
- Any DB change must be a safe, backward-compatible Alembic migration.
- Reuse existing `busca_service` (S-05) for matching logic.
```


