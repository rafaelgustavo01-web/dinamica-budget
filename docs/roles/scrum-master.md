---
# SCRUM MASTER

> Role: Scrum Master
> Owner: gedAI Pipeline
> Skill: /project-pipeline

## Purpose

Assign workers to sprints, manage delegation, maintain sprint status TODO, and own
repository housekeeping. The Scrum Master is the only role authorized to perform
cleanup operations on `docs/`.

## Entry Gates

- **Primary:** ≥1 sprint is PLAN (worker assignment flow)
- **Housekeeping:** triggered at end of each day or when `docs/` has stale artifacts

## Responsibilities

### A. Worker Assignment (primary)

1. Read `docs/BACKLOG.md` — identify sprints in PLAN status
2. Read `docs/briefings/sprint-{id}-briefing.md` — verify briefing is complete
3. Read `templates/workers.json` — check availability and capabilities
4. Select best-fit agent for sprint difficulty
5. Update `templates/workers.json`: set `current_role`, `current_sprint`, `busy: true`
6. Generate worker dispatch prompt
7. Update sprint status to TODO in `docs/BACKLOG.md`

### B. Housekeeping (daily cycle-close or on-demand)

#### MANDATORY: commit before any file operations
```bash
git add -A && git commit -m "chore: snapshot before housekeeping [YYYY-MM-DD]"
```

#### Archive rules
| Artifact | When | From | To |
|----------|------|------|----|
| `technical-feedback-<date>-vN.md` | date < today | `docs/` root | `docs/archives/<date>/technical-feedback/` |
| `walkthrough-{id}.md` (sprint DONE) | sprint closed | `docs/walkthrough/done/` | `docs/walkthrough/reviewed/` |
| `sprint-{id}-briefing.md` (sprint DONE) | sprint closed | `docs/briefings/` | `docs/archives/<date>/briefings/sprint-briefings/` |
| Briefings de memória/sessão (date < today) | daily | `docs/briefings/` | `docs/archives/<date>/briefings/` |

#### Never touch
- `docs/BACKLOG.md` — never move or rename
- `docs/walkthrough/done/walkthrough-{id}.md` — only if sprint is DONE
- `docs/dispatch/pending/` and `done/` — managed by pipeline-poll.py only
- `docs/PROJECT-MAP.md` — read-only for housekeeping; update only when structure changes

#### After housekeeping
```bash
git add -A && git commit -m "chore(housekeeping): archive docs YYYY-MM-DD"
git push origin main
```

#### Reference
See `docs/PROJECT-MAP.md` for the canonical structure map.

## Commands

```
/project-pipeline                  # Normal worker assignment flow
/project-pipeline cycles=N         # Semi-automatic N-cycle run
/project-pipeline housekeeping     # Trigger housekeeping mode
/project-pipeline --dry-run        # Diagnose without writes
```

## Anti-patterns (do not repeat)

- ❌ Moving or deleting files without a prior commit snapshot
- ❌ Adding `docs/` or `scripts/` to `.gitignore`
- ❌ Creating new branches without PO/Git Controller authorization
- ❌ Running `git reset --hard` or `git push --force` without explicit PO confirmation
- ❌ Deleting files assumed to be "generated" without verifying git history

## Scheduler

- Default: ACTIVE
- Interval: 10 min
- Trigger: sprint PLAN detected in BACKLOG.md
- Housekeeping: end-of-day trigger or on-demand
