# Pipeline Config

> Dynamic configuration for the Role-Inbox Broadcast protocol.
> Any agent reads this file at the start of every cycle.

## Polling
- interval_minutes: 3
- jitter_seconds: 30

## Pipeline State
- status: RUNNING
- started_at: 2026-04-22T20:46:25Z
- stopped_at: null

## WIP
- max_active_sprints: 2
- max_rework_per_sprint: 3

## Roles Active
- po: true
- supervisor: true
- sm: true
- worker: true
- qa: true
- git_controller: true
- research: true
- log_creator: false

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
