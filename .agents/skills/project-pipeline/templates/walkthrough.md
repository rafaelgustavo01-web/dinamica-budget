# Walkthrough - Sprint [SPRINT ID] - [SPRINT NAME]

> Date: [DATE]
> Worker: [worker name/model]
> Backlog status on entry: TODO
> Backlog status on exit: TESTED

## Objective

[1-2 sentences on what the sprint delivered.]

## Delivered Artifacts

| File | Type | Summary |
|------|------|---------|
| `[path/to/file.py]` | code | [what changed] |
| `docs/sprints/[SPRINT ID]/technical-review/technical-review-[DATE]-[SPRINT ID].md` | review | [what was updated] |
| `docs/sprints/[SPRINT ID]/walkthrough/done/walkthrough-[SPRINT ID].md` | walkthrough | this file |

## Validation

```bash
python -m ruff check gedai/ tests/
python -m pytest tests/ -q
```

- Result: [pass/fail/partial]
- Notes: [details]

## Blockers or Risks

- [blocker or `none`]

## Status Update

After writing this file, update `docs/shared/governance/BACKLOG.md` from `TODO` to `TESTED`.
