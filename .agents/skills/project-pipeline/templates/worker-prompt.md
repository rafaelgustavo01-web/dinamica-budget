# Worker Handoff Prompt Template

> Deliver one prompt per sprint and one worker per prompt.
> Replace every placeholder before sending.

```
[WORKER_NAME], you are the execution worker for sprint [SPRINT ID] in project [PROJECT_NAME].

Read the briefing first:
@docs/sprints/[SPRINT ID]/briefing/sprint-[SPRINT ID]-briefing.md

Execute the approved plan:
@docs/sprints/[SPRINT ID]/plans/[YYYY-MM-DD]-[name].md

Context files:
@docs/shared/governance/BACKLOG.md
@docs/sprints/[SPRINT ID]/technical-review/technical-review-[DATE]-[SPRINT ID].md
@docs/sprints/[SPRINT ID]/technical-feedback/technical-feedback-[DATE]-[SPRINT ID]-v[N].md

Worker assignment:
- Worker ID: [WORKER_ID]
- Provider: [PROVIDER]
- Mode: [BUILD | Always Proceed | Ignore | Agent]

Rules:
- Execute only the approved sprint scope.
- Keep the sprint in the backlog state machine.
- Generate or update `docs/sprints/[SPRINT ID]/technical-review/technical-review-[DATE]-[SPRINT ID].md`.
- Save the walkthrough to `docs/sprints/[SPRINT ID]/walkthrough/done/walkthrough-[SPRINT ID].md`.
- Update `docs/shared/governance/BACKLOG.md` from `TODO` to `TESTED` when the sprint is complete.
- Do not mark the sprint `DONE`.
```

## Notes for Scrum Master

- Send the prompt only after auth and quota checks pass.
- Reserve the worker before sending the prompt.
- If the worker rejects or fails the gate, keep the sprint in `PLAN`.
