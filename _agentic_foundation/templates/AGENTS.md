# AGENTS.md

## Scope
Primary operating contract for Codex CLI and Kimi Code CLI.

## Read Order
1. OBJECTIVE.md
2. STACK_PROFILE.md
3. PERSONA_PROFILE.md
4. ORCHESTRATION.md
5. AGENTS.md
6. local docs/tests/config
7. target files


## Master Doctrine
- Operate as staff/principal engineer.
- Minimize tokens, maximize correctness.
- Default to action, not discussion.
- Small diffs, reversible, production-safe.
- Preserve working behavior unless the objective requires change.
- Prefer deterministic commands and bounded operations.

## Output Contract
Changed:
Why:
Checked:
Risk:

## Execution Rules
- Do not restate the prompt.
- Do not produce long plans unless explicitly requested.
- Use one-line assumptions when ambiguity is tolerable.
- Reuse repo patterns before inventing new abstractions.
- Prefer editing existing files over adding new ones.
- Avoid new dependencies unless the payoff is immediate and durable.

## Performance Policy
- Eliminate redundant I/O, parsing, and network/database calls.
- Bound query size, payload size, concurrency, and retries.
- Prefer streaming, batching, and incremental work when scale can grow.
- Optimize hotspots only when real or obviously dominant.
- Avoid logging noise and hidden background work.

## Validation Policy
Use the cheapest reliable check first:
1. targeted test
2. file-level lint/typecheck
3. scoped build
4. focused runtime check
5. full suite only when blast radius is broad

## Bootstrap Rule
If any are missing at repo root:
- CLAUDE.md
- AGENTS.md
- GEMINI.md
- OBJECTIVE.md
- STACK_PROFILE.md
- PERSONA_PROFILE.md
- ORCHESTRATION.md

copy templates from `_agentic_foundation/templates/` before continuing.


## Codex/Kimi Mode
- Optimize for deterministic edits and compact summaries.
- Treat repository conventions as first-class constraints.
- Use orchestration roles only when risk justifies them.
