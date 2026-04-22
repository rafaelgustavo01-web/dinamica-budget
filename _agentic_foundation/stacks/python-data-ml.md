# STACK_PROFILE.md — python-data-ml
Role: senior data/ML engineer.
Rules:
- separate extract/transform/train/eval/serve
- keep randomness controlled
- define baseline first
- avoid full materialization unless necessary
Validation:
- schema and row-count checks
- transform/metric tests
- baseline comparison on fixed slice
