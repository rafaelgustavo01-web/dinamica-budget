# Agent Memory Sync Briefing - [DATE]

> Audience: Product Owner, Supervisor, Scrum Master, Workers, QA, Research AI, Log Creator
> Purpose: refresh permanent memory after a pipeline contract update

## Read First

- `docs/JOB-DESCRIPTION.md`
- `docs/BACKLOG.md`
- `docs/superpowers/plans/roadmap/ROADMAP.md`
- `.claude/skills/project-pipeline/SKILL.md`

## Memory Updates Required

1. Replace the legacy Supervisor -> DEV MASTER mental model with the multi-role pipeline.
2. Store the canonical state machine: `BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`.
3. Store the WIP cap of 2 active sprints.
4. Store the single-flight status update rule.
5. Store the scheduler defaults: every role `ACTIVE` except Log Creator `DISABLED`, interval 10 minutes, native automation first, Claude MCP scheduling fallback.
6. Store the active sprint queue and selected roadmap IDs.

## Expected Acknowledgement

Reply with:
- role understood
- state machine understood
- scheduler default understood
- current active sprints understood
- any blocker or `none`
