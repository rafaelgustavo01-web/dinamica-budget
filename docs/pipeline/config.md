# Pipeline Config

> Dynamic configuration for the Role-Inbox Broadcast protocol.
> Any agent reads this file at the start of every cycle.

## Polling
- interval_minutes: 3
- jitter_seconds: 30

## Pipeline State
- status: RUNNING
- started_at: 2026-04-23T10:46:50Z
- stopped_at: null

## WIP
- max_active_sprints: 4
- max_rework_per_sprint: 3

## Roles Active
- research: KIMI
- po: KIMI
- sm: KIMI
- supervisor: KIMI
- worker_codex: CODEX
- worker_gemini: GEMINI
- qa: OPENCODE
- git_controller: OPENCODE
- assistant: OPENCODE
- log_creator: OPENCODE

## Escalation Rules
- auto_escalate_to_git_controller: false
- worker_blocked_by_git: true
- stale_pending_threshold_hours: 24

## Paths
- backlog: docs/BACKLOG.md
- plans: docs/superpowers/plans/
- briefings: docs/briefings/
- walkthroughs_done: docs/walkthrough/done/
- walkthroughs_reviewed: docs/walkthrough/reviewed/
- technical_reviews: docs/technical-review-*.md
- technical_feedback: docs/technical-feedback-*.md
- worker_registry: templates/workers.json
