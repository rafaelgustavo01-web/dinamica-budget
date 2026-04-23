# Worker Handoff Prompt — Sprint S-11

> Delivered by: Scrum Master / Supervisor (Kimi Code CLI)
> Date: 2026-04-23

```
Codex 5.3, you are the execution worker for sprint S-11 in project Dinamica Budget.

Read the briefing first:
@docs/briefings/sprint-S-11-briefing.md

Execute the approved plan:
@docs/superpowers/plans/2026-04-23-geracao-cpu-composicao-precos.md

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
- Generate or update `docs/technical-review-2026-04-23-s11.md`.
- Save the walkthrough to `docs/walkthrough/done/walkthrough-S-11.md`.
- Update `docs/BACKLOG.md` from `PLAN` to `TESTED` when the sprint is complete.
- Do not mark the sprint `DONE`.
- This project uses ONLY the main branch. Do not create feature branches.
- Any DB change must be a safe, backward-compatible Alembic migration.
- Reuse existing composition explosion logic (S-02) and PcTabelas models.
```
