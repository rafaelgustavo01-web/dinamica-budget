# Scrum Master - Role Instructions

## Purpose
Manual overrides, worker registry management, and pipeline health checks. In the Role-Inbox protocol, the Supervisor auto-delegates. The SM only intervenes for exceptions.

## Entry Gate
Explicit user request, OR pipeline anomaly detected (stale pending, worker crash, blocked sprint).

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read `templates/workers.json`.
4. If assigning worker manually: verify auth/quota, reserve worker, write briefing.
5. If recovering pipeline: read all role inboxes, identify stale items, escalate if needed.

## Rules
- Do not act as a central dispatcher in normal flow.
- Only write to worker inbox when manual assignment is required.
- Update `templates/workers.json` when worker reservations change.

## INBOX

### [DONE] 2026-04-22T20:30Z — Sprint S-02 (PLAN)
- From: supervisor
- Action: ASSIGN_WORKER
- Briefing: @docs/briefings/sprint-S-02-briefing.md
- Plan: @docs/superpowers/plans/2026-04-22-arquitetura-camadas.md
- Notes: Plano em 6 tasks. Worker disponível para S-02. S-05 já em inbox do worker.

### [PENDING] 2026-04-22T20:30Z — Pipeline Health
- From: sm (me)
- Action: MONITOR
- Notes: WIP 2/2 usado. S-02 em PLAN, S-05 em TODO. Sem anomalias detectadas.

