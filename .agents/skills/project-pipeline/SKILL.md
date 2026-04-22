---
name: project-pipeline
description: Use when managing a multi-role sprint pipeline with backlog transitions, briefing dispatch, worker assignment, QA handoff, or Git recovery in this repository.
---

# Project Pipeline

Use this skill to coordinate the repo's operational sprint flow. It is for orchestration, not direct feature implementation.

## Read Order

1. `docs/BACKLOG.md`
2. `docs/JOB-DESCRIPTION.md`
3. `docs/superpowers/plans/roadmap/ROADMAP.md`
4. `templates/workers.json`
5. `PROJECT MAP.md`

## Canonical Status Flow

`BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`

## Role Boundaries

- Product Owner: selects and prioritizes sprints.
- Supervisor: creates the approved plan and briefing.
- Scrum Master: assigns workers and moves approved work to `TODO`.
- Worker: executes approved work and produces walkthrough/review artifacts.
- QA: accepts to `DONE` or rejects back to `TODO`.
- Git Controller: resolves repository incidents without losing work.

## Artifact Paths

- Backlog: `docs/BACKLOG.md`
- Plans: `docs/superpowers/plans/`
- Briefings: `docs/briefings/`
- Worker prompts: `docs/dispatch/pending/`
- Walkthroughs: `docs/walkthrough/done/`
- Technical reviews: `docs/technical-review-YYYY-MM-DD.md`
- Worker registry: `templates/workers.json`

## Git Controller Rules

- Inspect `git status`, branch state, and stash state before making changes.
- Preserve work before destructive operations by using a safety tag or stash.
- Prefer `main` as the integration branch unless the user explicitly asks otherwise.
- Do not force-push or reset without explicit confirmation.

## Repo Hygiene Rules

- Generated artifacts must stay out of Git.
- Keep folder names stable and predictable.
- Remove duplicate or accidental nested paths when a canonical path already exists.
- Update `PROJECT MAP.md` after structural changes.

## Completion Checklist

- Backlog status matches actual artifact state.
- Walkthrough and technical review paths are canonical.
- Skills have valid frontmatter and repo-correct references.
- Git history is clean enough for `main` to remain the single valid branch.
