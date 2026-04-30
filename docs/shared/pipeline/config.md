# Pipeline Config

> Dynamic configuration for the Role-Inbox Broadcast protocol.
> Any agent reads this file at the start of every cycle.

## Polling
- interval_minutes: 3
- jitter_seconds: 30

## Pipeline State
- status: STOPPED
- started_at: 2026-04-23T10:46:50Z
- stopped_at: 2026-04-23T14:51:49Z

## WIP
- max_active_sprints: 4
- max_rework_per_sprint: 3

## Roles Active
- research: GEMINI
- po: KIMI
- sm: KIMI
- supervisor: KIMI
- worker_codex: CODEX
- worker_frontend: CLAUDE
- worker_backend_codex: CODEX
- worker_backend_kimi: KIMI
- qa: GEMINI
- git_controller: OPENCODE
- assistant: OPENCODE
- log_creator: OPENCODE

## Escalation Rules
- auto_escalate_to_git_controller: false
- worker_blocked_by_git: true
- stale_pending_threshold_hours: 24

## Paths
- backlog: docs/shared/governance/BACKLOG.md
- plans: docs/sprints/[ID]/plans/; docs/shared/superpowers/plans/
- briefings: docs/sprints/[ID]/briefing/
- walkthroughs_done: docs/sprints/[ID]/walkthrough/done/
- walkthroughs_reviewed: docs/sprints/[ID]/walkthrough/reviewed/
- technical_reviews: docs/sprints/[ID]/technical-review/
- technical_feedback: docs/sprints/[ID]/technical-feedback/
- worker_registry: templates/workers.json


## Operating Policy — 2026-04-29
- WIP assumido: 4 sprints ativas no máximo (`max_active_sprints: 4`).
- Quando QA mover uma sprint de `TESTED` para `DONE`, o Scrum Master/gedAI deve abrir/despachar novo ciclo respeitando dependências e WIP disponível.
- QA principal para validação de sprints em `TESTED`: Gemini.
- Fluxo documental obrigatório por sprint:
  - Briefing: `docs/sprints/[ID]/briefing/`
  - Plan: `docs/sprints/[ID]/plans/`
  - Technical Review: `docs/sprints/[ID]/technical-review/`
  - Technical Feedback: `docs/sprints/[ID]/technical-feedback/`
  - Walkthrough: `docs/sprints/[ID]/walkthrough/done/` e/ou `docs/sprints/[ID]/walkthrough/reviewed/`
- Agents podem editar, escrever, rodar gates e commitar/pushar na `main`, mas continuam proibidos de force-push, reset hard destrutivo, segredos e produção sem aprovação.


## Agent Routing Policy — 2026-04-29
- gedAI remains the orchestrator/scrum master and decides dispatch based on sprint scope, WIP and model availability.
- Backend, database, migrations, services, APIs, integrations and heavy refactors: prefer **Kimi** and **Codex**.
- Frontend, UI/UX, React/TypeScript, MUI, layout, visual polish and demo flows: prefer **Claude Code**.
- Research, feature discovery, product references, roadmap mining and new-feature ideation: prefer **Gemini**.
- QA can use Gemini when available, but must not block the pipeline indefinitely on Gemini capacity; if Gemini returns capacity/rate errors, retry later or use Codex/Kimi as fallback reviewer with the same QA contract.
- Use conscious token rotation:
  - simple, bounded tasks: lower-cost/lighter models such as Codex 5.3-class or Claude Sonnet-class;
  - full operational work, architecture review, broad refactors or high-risk changes: stronger models such as Codex 5.5-class, Claude Opus-class or Kimi.
- Prefer more delegated, smaller tasks over one oversized prompt; each delegated task must preserve the documentation flow and commit/push discipline.
- Mandatory sprint artifacts remain: Briefing, Plan, Technical Review, Technical Feedback and Walkthrough.
