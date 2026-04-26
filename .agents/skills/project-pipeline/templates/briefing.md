# Sprint Briefing - [SPRINT ID] - [SPRINT NAME]

> Date: [DATE]
> Prepared by: [Supervisor name/model]
> Assigned role: Worker
> Assigned worker: [WORKER_ID]
> Execution mode: [BUILD | Always Proceed | Ignore | Agent]
> Plan: `docs/sprints/[SPRINT ID]/plans/YYYY-MM-DD-[name].md`

## Mission

[2-3 paragraphs that explain the current code state, why this sprint exists, and what must change now.]

## Delegation Envelope

- Sprint status on entry: `PLAN`
- Worker status target on exit: `TESTED`
- Assigned worker: [WORKER_ID]
- Provider: [PROVIDER]
- Auth status snapshot: [PASS/FAIL/UNKNOWN]
- Quota status snapshot: [PASS/FAIL/UNKNOWN]
- Execution mode: [MODE]

## Current Code State

### `[path/to/file.py]`
- Line [N]: [relevant method or class]
- Line [N]: [relevant method or class to change]
- Risk note: [what can break if the file is rewritten]

## Required Changes

### Task [ID.1] - [Task name]
- File: `[path/to/file.py]`
- Change: [precise behavior change]
- Constraints: [must preserve existing behavior, tests, interfaces]

### Task [ID.2] - [Task name]
- File: `[path/to/file.py]`
- Change: [precise behavior change]
- Constraints: [what must not change]

## Mandatory Tests

- `[tests/test_file.py]`: add [N] tests
- `[tests/test_existing_file.py]`: preserve existing tests and append [N] tests
- Validation commands:
```bash
python -m ruff check gedai/ tests/
python -m pytest tests/ -q
```

## Required Artifacts Before Status `TESTED`

- `docs/sprints/[SPRINT ID]/technical-review/technical-review-[DATE]-[SPRINT ID].md` updated
- `docs/sprints/[SPRINT ID]/walkthrough/done/walkthrough-[SPRINT ID].md` written
- `docs/shared/governance/BACKLOG.md` updated from `TODO` to `TESTED`

## Critical Warnings

1. Use incremental edits. Do not rewrite full files unless the plan explicitly requires it.
2. Do not change sprint status out of order.
3. Do not mark the sprint `DONE`.
4. If blocked, record the blocker in the walkthrough and leave the status unchanged.
