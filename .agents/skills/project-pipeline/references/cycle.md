# Complete Cycle Reference - Multi-Role Sprint Orchestration

## State Machine

| From | To | Owner | Required Evidence |
|------|----|-------|-------------------|
| `BACKLOG` | `INICIADA` | Product Owner | roadmap items selected and backlog row created |
| `INICIADA` | `PLAN` | Supervisor | approved sprint plan + briefing created |
| `PLAN` | `TODO` | Supervisor (auto) | worker assigned via inbox handoff |
| `TODO` | `TESTED` | Worker | technical-review plus walkthrough |
| `TESTED` | `DONE` | QA | technical-feedback plus accepted validation |
| `TESTED` | `TODO` | QA | rework briefing written to worker inbox |

Only one role may perform each transition. Every transition must re-read `docs/BACKLOG.md` immediately before writing.

## Global Queue Rules

- WIP cap: no more than 2 active sprints across `INICIADA`, `PLAN`, `TODO`, and `TESTED`.
- Parallel planning is allowed only for dependency-safe sprints.
- A sprint may not skip a state.
- A sprint may not be marked `DONE` by a worker.
- A worker reservation must be released when the sprint reaches `DONE` or returns to `BACKLOG`.

## Communication Protocol

### How Roles Talk to Each Other

1. **No central dispatcher.** Each role writes directly to the next role's inbox.
2. **Inbox location:** `docs/roles/[role-name]-readme.md` → section `## INBOX`.
3. **Handoff vehicle:** Briefings (`docs/briefings/sprint-[id]-briefing.md`).
4. **Rework vehicle:** New briefing file (`docs/briefings/sprint-[id]-rework-v[N].md`).

### Inbox States

- `[PENDING]`: awaiting action by the owner of this role file.
- `[DONE]`: action completed. Kept for audit trail.
- `[BLOCKED]`: cannot proceed. Escalation required.

## Role Cycles

### Product Owner

Entry gate:
- Inbox has `[PENDING]` message with `Action: INTAKE_NEXT`, OR
- All active sprints are `DONE` and WIP slot is available.

Checklist:
1. Read `docs/pipeline/config.md`.
2. Read `docs/roles/po-readme.md` ## INBOX.
3. Read `docs/superpowers/plans/roadmap/ROADMAP.md`.
4. Select at least 2 candidate features when 2 safe candidates exist.
5. Mark selected roadmap IDs in `ROADMAP.md`.
6. Add or refresh rows in `docs/BACKLOG.md`.
7. Move selected rows to `INICIADA`.
8. **Do NOT write to any inbox.** Supervisor will auto-detect `INICIADA`.

### Supervisor

Entry gate:
- At least one sprint is `INICIADA` in BACKLOG, OR
- Inbox has `[PENDING]` message.

Checklist:
1. Read `docs/shared/pipeline/config.md`.
2. Read `docs/shared/roles/supervisor-readme.md` ## INBOX.
3. Read `docs/shared/governance/BACKLOG.md`.
4. Find oldest `INICIADA` sprint without a plan.
5. Produce a plan and save to `docs/sprints/[id]/plans/`.
6. Generate briefing at `docs/sprints/[id]/briefing/sprint-[id]-briefing.md`.
7. Update backlog row to `PLAN`.
8. **Write inbox to Worker:** append to `docs/shared/roles/worker-readme.md`:
   ```markdown
   ### [PENDING] [ISO-TIMESTAMP] — Sprint [ID]
   - From: supervisor
   - Action: BUILD
   - Briefing: @docs/sprints/[id]/briefing/sprint-[id]-briefing.md
   - Plan: @docs/sprints/[id]/plans/...
   ```

### Worker

Entry gate:
- Inbox has `[PENDING]` message with `Action: BUILD` or `Action: REWORK`.

Checklist:
1. Read `docs/shared/pipeline/config.md`.
2. Read `docs/shared/roles/worker-readme.md` ## INBOX.
3. Read the approved plan in `docs/sprints/[id]/plans/` and briefing in `docs/sprints/[id]/briefing/`.
4. Execute with `/gsd-do`.
5. Generate or update `docs/sprints/[id]/technical-review/technical-review-YYYY-MM-DD-[id].md`.
6. Write `docs/sprints/[id]/walkthrough/done/walkthrough-[id].md`.
7. Update backlog row to `TESTED`.
8. Mark own inbox item as `[DONE]`.
9. **Write inbox to QA:** append to `docs/shared/roles/qa-readme.md`:
   ```markdown
   ### [PENDING] [ISO-TIMESTAMP] — Sprint [ID]
   - From: worker ([worker-id])
   - Action: REVIEW
   - Walkthrough: @docs/sprints/[id]/walkthrough/done/walkthrough-[id].md
   - Technical Review: @docs/sprints/[id]/technical-review/technical-review-YYYY-MM-DD-[id].md
   - Tests: [command + results]
   ```

### QA

Entry gate:
- Inbox has `[PENDING]` message with `Action: REVIEW`.

Checklist:
1. Read `docs/shared/pipeline/config.md`.
2. Read `docs/shared/roles/qa-readme.md` ## INBOX.
3. Read walkthrough in `docs/sprints/[id]/walkthrough/done/` and technical-review in `docs/sprints/[id]/technical-review/`.
4. Run targeted verification first.
5. Expand to broader verification only if the blast radius requires it.
6. Write `docs/sprints/[id]/technical-feedback/technical-feedback-YYYY-MM-DD-[id]-v[N].md`.
7. Mark own inbox item as `[DONE]`.
8. **If ACCEPTED:**
   - Update backlog row to `DONE`.
   - Move walkthrough from `docs/sprints/[id]/walkthrough/done/` to `docs/sprints/[id]/walkthrough/reviewed/`.
   - **Write inbox to Research:** append to `docs/shared/roles/research-readme.md`
   - **Write inbox to PO:** append to `docs/shared/roles/po-readme.md`
9. **If REJECTED:**
   - Create rework briefing at `docs/sprints/[id]/briefing/sprint-[id]-rework-v[N].md`.
   - Update backlog row to `TODO`.
   - **Write inbox to Worker:** append to `docs/shared/roles/worker-readme.md`:
     ```markdown
     ### [PENDING] [ISO-TIMESTAMP] — Sprint [ID] REWORK v[N]
     - From: qa
     - Action: REWORK
     - Rework Briefing: @docs/sprints/[id]/briefing/sprint-[id]-rework-v[N].md
     - Original Briefing: @docs/sprints/[id]/briefing/sprint-[id]-briefing.md
     - Technical Feedback: @docs/sprints/[id]/technical-feedback/technical-feedback-YYYY-MM-DD-[id]-v[N].md
     ```

### Research AI

Entry gate:
- Inbox has `[PENDING]` message with `Action: MINE_ROADMAP`.

Checklist:
1. Read `docs/pipeline/config.md`.
2. Read `docs/roles/research-readme.md` ## INBOX.
3. Read all sprint artifacts.
4. Identify follow-on features, improvements, tests, and procedures.
5. Append those items to `docs/superpowers/plans/roadmap/ROADMAP.md`.
6. Add a row to `Historico de Atualizacao` with summary, owner, and timestamp.
7. Mark own inbox item as `[DONE]`.

### Git Controller

Entry gate:
- Inbox has `[PENDING]` message with `Action: GIT_RECOVER`, OR
- Explicit manual activation by user.

Checklist:
1. Read `docs/pipeline/config.md`.
2. Read `docs/roles/git-controller.md` ## INBOX.
3. Inspect `git status`, branch state, and stash state.
4. Preserve work before destructive operations.
5. Resolve incident.
6. Mark own inbox item as `[DONE]`.
7. If unblocking a Worker, optionally write to `docs/roles/worker-readme.md`.

**Rule:** No other role may write to Git Controller inbox for routine tasks (merge, commit, .gitignore). Only emergencies: corrupted history, broken main, impossible merges.

## Scheduler Semantics

Default interval:
- Read from `docs/pipeline/config.md` → `interval_minutes`.
- If not specified, fallback to 10 minutes.

Default role states:
- Product Owner: `ACTIVE`
- Supervisor: `ACTIVE`
- Scrum Master: `ACTIVE` (for manual overrides only)
- Workers: `ACTIVE`
- QA: `ACTIVE`
- Research AI: `ACTIVE`
- Git Controller: `ACTIVE`
- Log Creator: `DISABLED`

Preferred backend order:
1. Native client automation (Task Scheduler, cron).
2. Claude MCP scheduling fallback.

Role trigger conditions:
- **Product Owner:** inbox has `INTAKE_NEXT` or all active sprints are `DONE`.
- **Supervisor:** BACKLOG has `INICIADA` sprint without plan, or inbox has message.
- **Worker:** inbox has `BUILD` or `REWORK`.
- **QA:** inbox has `REVIEW`.
- **Research AI:** inbox has `MINE_ROADMAP`.
- **Git Controller:** inbox has `GIT_RECOVER`.

Generic scheduler prompt:
```
Read docs/pipeline/config.md for interval.
Read docs/roles/[MY-ROLE]-readme.md and check ## INBOX for [PENDING] messages.
Read docs/BACKLOG.md for context.
If a [PENDING] message matches my role, execute the action and hand off to the next role via inbox.
If no [PENDING] message, exit with no write.
Reschedule this same check after interval_minutes.
```

## Failure Handling

- Approval rejected: Supervisor keeps sprint in `INICIADA`, revises plan, and re-writes worker inbox.
- Worker unavailable: Supervisor keeps sprint in `PLAN` and does not assign fallback silently.
- QA rejection: QA creates rework briefing first, then writes to Worker inbox. Backlog stays `TODO`.
- Missing artifact: do not advance state. Write `[BLOCKED]` in own inbox with reason.
- WIP cap reached: Product Owner must not move additional items into `INICIADA`.
- Agent crash: `[PENDING]` message remains. Next scheduler cycle retries.
