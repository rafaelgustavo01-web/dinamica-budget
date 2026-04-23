---
name: project-pipeline
description: Use when managing a multi-role sprint pipeline with inbox-based handoff, backlog transitions, briefing dispatch, worker assignment, QA handoff, or Git recovery in this repository.
---

# Project Pipeline

Use this skill to coordinate the repo's operational sprint flow. It is for orchestration, not direct feature implementation.

## Core Protocol: Role-Inbox Broadcast

Communication between roles happens exclusively through **inbox sections inside role files** and **briefings**. There is no central dispatcher.

### Read Order (every agent cycle)

1. `docs/pipeline/config.md` — polling interval, WIP cap, active roles
2. `docs/roles/[MY-ROLE]-readme.md` — my instructions + ## INBOX
3. `docs/BACKLOG.md` — current sprint statuses
4. `docs/JOB-DESCRIPTION.md` — team contract
5. `docs/superpowers/plans/roadmap/ROADMAP.md` — candidate features

### Handoff Rules

- When a role finishes, it **appends** a message to the ## INBOX of the next role.
- Messages have 3 states: `[PENDING]`, `[DONE]`, `[BLOCKED]`.
- Never delete messages. Only change state.
- Briefings are the vehicle of communication between roles.
- Rework from QA is a **new briefing file**: `docs/briefings/sprint-[ID]-rework-v[N].md`.

### Inbox Message Template

```markdown
### [PENDING] 2026-04-22T14:00Z — Sprint S-XX
- From: [role]
- Action: [PLAN | BUILD | REVIEW | REWORK | MINE_ROADMAP | INTAKE_NEXT | GIT_RECOVER]
- Briefing: @docs/briefings/sprint-S-XX-briefing.md
- Plan: @docs/superpowers/plans/...
- Notes: [context]
```

## Canonical Status Flow

`BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`

## Role Boundaries

- **Product Owner**: selects sprints, moves BACKLOG → INICIADA. Updates BACKLOG directly.
- **Supervisor**: auto-detects INICIATED sprints in BACKLOG, creates plan + briefing, writes inbox to Worker.
- **Scrum Master**: assigns workers, updates workers.json, writes briefing if needed.
- **Worker**: executes approved work from inbox, produces walkthrough/review artifacts, writes inbox to QA.
- **QA**: accepts to DONE or rejects with rework briefing, writes inbox to Research + PO.
- **Git Controller**: resolves repository incidents. Only receives inbox messages for real emergencies (corrupted history, broken main, impossible merges).
- **Research AI**: mines DONE sprints into roadmap.

## Artifact Paths

- Config: `docs/pipeline/config.md`
- Backlog: `docs/BACKLOG.md`
- Plans: `docs/superpowers/plans/`
- Briefings: `docs/briefings/` (original + rework versions)
- Worker prompts: `docs/dispatch/pending/`
- Walkthroughs: `docs/walkthrough/done/`
- Reviewed walkthroughs: `docs/walkthrough/reviewed/`
- Technical reviews: `docs/technical-review-YYYY-MM-DD.md`
- Technical feedback: `docs/technical-feedback-YYYY-MM-DD-vN.md`
- Worker registry: `templates/workers.json`
- Role inboxes: `docs/roles/*.md` (## INBOX section)

## Git Controller Rules

- Inspect `git status`, branch state, and stash state before making changes.
- Preserve work before destructive operations by using a safety tag or stash.
- Prefer `main` as the integration branch unless the user explicitly asks otherwise.
- Do not force-push or reset without explicit confirmation.
- **Anti-pattern prevention**: No role may write to `git-controller.md` inbox for trivial merges, `.gitignore` fixes, or routine commits. Git Controller is for emergencies only.

## Repo Hygiene Rules

- Generated artifacts must stay out of Git.
- Keep folder names stable and predictable.
- Remove duplicate or accidental nested paths when a canonical path already exists.
- Update `PROJECT MAP.md` after structural changes.

## Pipeline Control CLI

A PowerShell controller manages the Windows Task Scheduler tasks for all active roles.

Script: `scripts/pipeline-control.ps1`

### Commands

- **`start`** — Reads active roles from `docs/pipeline/config.md`, creates one Task Scheduler task per role running `scripts/pipeline-agent.ps1` at the configured interval, and sets `status: RUNNING`.
- **`stop`** — Deletes all `Dinamica-Pipeline-*` tasks and sets `status: STOPPED`.
- **`time_set -Interval <minutes>`** — Updates `interval_minutes` in config. If pipeline is RUNNING, stops and recreates all tasks with the new interval.

### Agent Polling Script

Script: `scripts/pipeline-agent.ps1`

Each role's Task Scheduler task invokes this script with `-Role <name>`. It:
1. Reads `docs/pipeline/config.md` and exits silently if `status: STOPPED`.
2. Reads the role's `docs/roles/[role]-readme.md` and extracts the `## INBOX` section.
3. Parses `[PENDING]`, `[DONE]`, and `[BLOCKED]` messages.
4. For `worker`, resolves the assigned agent from briefing metadata or `templates/workers.json`, builds the CLI wake-up command, and outputs `CLI_TARGET` and `CLI_COMMAND`.
5. Supports `-DispatchMode emit|dry-run|run` so operators can inspect or execute the wake-up command.
6. Executes the worker CLI from the project root so the agent always starts inside the repository workspace.

Current built-in worker CLI mappings:
- `codex-*` / provider `OpenAI` -> `codex "<prompt>"`
- `gemini-*` / provider `Google` -> `gemini "<prompt>"`
- `kimi-*` / provider `Kimi CLI` -> `kimi-cli run "<prompt>"`
- `opencode-*` / provider `OpenCode` -> `opencode --no-interactive "<prompt>"`

## Completion Checklist

- Backlog status matches actual artifact state.
- Walkthrough and technical review paths are canonical.
- Skills have valid frontmatter and repo-correct references.
- Git history is clean enough for `main` to remain the single valid branch.
- Role inboxes have no stale `[PENDING]` messages older than config threshold.
