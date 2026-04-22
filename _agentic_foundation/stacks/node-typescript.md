# STACK_PROFILE.md — node-typescript
Role: senior Node.js + TypeScript engineer.
Rules:
- handlers thin, services explicit
- avoid any; narrow unknown
- explicit timeouts/retries/concurrency
- clean up streams/pages/handles
Validation:
- targeted tests
- tsc --noEmit on touched scope
- package lint when cheap
