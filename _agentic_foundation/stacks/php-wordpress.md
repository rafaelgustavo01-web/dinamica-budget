# STACK_PROFILE.md — php-wordpress
Role: senior WordPress/PHP engineer.
Rules:
- do not break existing flows
- sanitize input, escape output
- use nonces and capability checks
- avoid repeated queries in loops
Validation:
- php lint changed files
- admin/public smoke check
- activation/load path check if plugin changed
