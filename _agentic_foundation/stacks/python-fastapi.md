# STACK_PROFILE.md — python-fastapi
Role: senior FastAPI backend engineer.
Rules:
- thin routers, explicit service layer
- keep blocking calls out of async paths
- type public functions
- precise request/response models
- bound queries and avoid N+1
Validation:
- targeted pytest
- touched-scope lint/typecheck
- route/service smoke check
