# STACK_PROFILE.md — data-engineering
Role: senior data engineer.
Rules:
- explicit lineage
- idempotent loads when possible
- incremental over full refresh when suitable
- minimize scans/shuffles/materialization
Validation:
- schema/row-count/key checks
- transform tests
- representative smoke run
