# F4 Migration Consolidation Matrix — 2026-05-09

## Baseline

- Main head at consolidation start: `a5945b9`
- Current Alembic head on `main`: `026_item_codigo_autogerado.py` (`revision = "026"`, `down_revision = "025"`).
- Parallel worker migrations found: five files all claiming `revision = "027"` and `down_revision = "026"`.

## Collision inventory

| Worker | File | Action |
|---|---|---|
| F4-01 Gemini | `027_smart_import_job_table.py` | Keep as first new revision: `027` -> `026` |
| F4-02 Codex | `027_pq_client_profiles.py` | Merge concepts into canonical PQ profile revision |
| F4-02 Kimi | `027_pq_client_profile_learning.py` | Preferred base for canonical PQ profile revision because it includes explicit audit trail and tested hardening |
| F4-04 Claude | `027_cliente_campos_pc.py` | Do not use as-is: missing `schema="operacional"`; keep frontend field intent for final contract review |
| F4-04 Codex | `027_cliente_campos_folha_pc.py` | Preferred base for Cliente/Folha PC migration because schema-qualified and broader PC data model |

## Proposed linear chain

1. `027_smart_import_job_table.py` — from F4-01, `down_revision = "026"`.
2. `028_pq_client_profile_learning.py` — canonical F4-02 migration, `down_revision = "027"`.
3. `029_cliente_campos_folha_pc.py` — canonical F4-04 migration, `down_revision = "028"`.

## Guardrails before merge to main

- No migration from worker worktrees may be copied with `revision = "027"` unchanged except the first one.
- F4-04 Claude migration must not be used as-is because it omits `schema="operacional"` and would target the wrong table/search path.
- F4-02 needs final code-contract choice before merge: Kimi and Codex diverge in column naming (`aliases_json` vs `aliases_colunas`, `is_aprovado` vs approval metadata). Canonical migration should match selected merged backend code, not merely union every worker idea.
- Cliente/Folha PC needs final front/back contract reconciliation: Claude frontend currently uses `telefone`, `email_comercial`, `endereco_cidade`; Codex backend uses `contato_telefone`, `contato_email`, `endereco_municipio` plus fuller address fields.

## Status

This matrix is a staging artifact. The Alembic chain is not yet merged into `main` until code contracts are reconciled and upgrade/downgrade are validated.
