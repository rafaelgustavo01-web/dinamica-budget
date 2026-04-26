# [PROJECT_NAME] - Sprint Backlog

> Live queue. Update at every status transition.
> Last updated: [DATE-TIME]

## Status Machine

`BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`

## Queue Rules

- Only one role may update sprint status at a time.
- Re-read this file before every status write.
- Keep at most 2 active sprints across `INICIADA`, `PLAN`, `TODO`, and `TESTED`.
- Only parallelize dependency-safe sprints.
- `DONE` may only be written by QA.

## Active Sprint Queue

| Sprint | Status | Role Owner | Assigned Worker | Dependencies | Roadmap IDs | Plan | Briefing | Walkthrough | Feedback |
|--------|--------|------------|-----------------|--------------|-------------|------|----------|-------------|----------|
| [Sprint ID] - [Sprint Name] | [BACKLOG/INICIADA/PLAN/TODO/TESTED/DONE] | [Role] | [Worker or -] | [Dependencies or none] | [1.1, 2.2] | [path or Pending] | [path or Pending] | [path or Pending] | [path or Pending] |

## Completed Sprint Archive

| Sprint | Status | Closed On | Notes |
|--------|--------|-----------|-------|
| [Sprint ID] | DONE | [DATE] | [Short closeout note] |

## Roadmap Intake Notes

- Selected roadmap items must be marked in `docs/superpowers/plans/roadmap/ROADMAP.md`.
- Use `Roadmap IDs` to connect the backlog row to roadmap entries.
- When QA closes a sprint, move follow-on ideas to the roadmap or backlog instead of reopening the closed row.
