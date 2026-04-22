# ORCHESTRATION.md

## Active Multi-Agent Flow
Default pipeline:
1. Planner
2. Executor
3. Auditor
4. Synthesizer

Use fewer agents when the task is small.
Use the full chain when:
- the blast radius is medium/high
- infra or security is involved
- data migration or refactor risk exists
- the change crosses boundaries

## Role Contract

### Planner
- compress problem into an execution brief
- identify scope, constraints, likely files, validation path
- do not overdesign
- output <= 12 lines

### Executor
- perform the smallest correct change
- reuse existing patterns
- keep diffs small
- validate narrowly first

### Auditor
- inspect for regressions, edge cases, security/performance debt
- look for mismatch between objective and implementation
- propose only material corrections

### Synthesizer
- produce the final compact delivery note
- no internal chain-of-thought
- standard output:
  - Changed
  - Why
  - Checked
  - Risk

## Escalation Rules
Escalate to full chain if any are true:
- multiple services/packages touched
- schema/API contract changed
- auth/payment/file handling involved
- concurrency/background jobs involved
- unknown performance impact

## Token Budgeting
- planner <= 12 lines
- auditor <= 10 lines
- final <= 8 lines unless explicitly asked for detail
