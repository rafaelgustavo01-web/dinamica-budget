# PROJECT MAP

## 1. Purpose

This file is the canonical structural map of the repository.

It makes two boundaries explicit:

- solution artifacts live under `app/`
- project, governance, agent, and engineering support artifacts live outside `app/`

The canonical shared skill source remains:

- `.agents/skills/`

Duplicate `skills` folders in local tooling workspaces were intentionally removed.

---

## 2. Root Layout

### 2.1 Solution Root

- `app/`
  Canonical root of the product solution.

Everything inside `app/` is part of the application/runtime surface:

- backend code
- frontend code
- database migrations
- ML model cache area used by the solution
- runtime env/config files
- deployment entrypoints
- solution-facing READMEs

### 2.2 Repository Operating Contract

These stay at repository root because they govern agents and repo operation, not product runtime:

- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `OBJECTIVE.md`
- `STACK_PROFILE.md`
- `PERSONA_PROFILE.md`
- `ORCHESTRATION.md`

### 2.3 Project and Engineering Surface

- `docs/`
  Project documentation workspace.
- `.agents/`
  Canonical repository-owned agent assets and skills.
- `_agentic_foundation/`
  Bootstrap templates and reusable agentic foundation material.
- `scripts/`
  Root engineering/ops helpers that act on the solution under `app/`.
- `configs/`
  Support configuration assets.
- `templates/`
  Reusable templates and worker metadata.
- `dinamica-design-system/`
  Design support/reference material.

### 2.4 Workspace / Generated / Local Tooling

- `logs/`
- `resultado/`
- `query`
- `.venv/`
- `.pytest_cache/`
- `.amazonq/`
- `.claude/`
- `.codex/`
- `.kilo/`
- `.kimi/`
- `.kiro/`
- `.opencode/`
- `.playwright-cli/`

These are not the canonical product source.

### 2.5 Loose Root Support Artifacts

- `Composições TCPO - PINI.xlsx`
- `Converter em Data Center.xlsx`
- `PC.xlsx`
- `der.sql`
- `.gitignore`
- `.gitignore.backup`
- `ETAPA`

These are auxiliary repo artifacts, not part of the application runtime tree.

---

## 3. Solution Map: `app/`

## 3.1 Solution Root Files

- [README.md](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/README.md)
  Main backend/product documentation from the solution root perspective.
- [README_FRONT.MD](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/README_FRONT.MD)
  Frontend architecture and integration documentation.
- [requirements.txt](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/requirements.txt)
  Python dependencies for the backend/runtime.
- [alembic.ini](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/alembic.ini)
  Alembic config for the moved solution root.
- [pytest.ini](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/pytest.ini)
  Test discovery/config for the backend under `backend/tests`.
- [deploy-dinamica.bat](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/deploy-dinamica.bat)
  Main Windows deployment entrypoint for the application.
- [deploy.bat](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/deploy.bat)
  Additional deploy helper.
- [fix-deploy.ps1](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/fix-deploy.ps1)
  Deployment repair helper.
- [remove-dinamica.bat](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/remove-dinamica.bat)
  Removal/uninstall helper.
- `app/.env`
  Local environment file for the moved solution root.
- `app/.env.example`
  Environment template.
- `app/package-lock.json`
  Root lockfile for solution-level Node tooling.

## 3.2 Backend: `app/backend/`

### Entry and App Composition

- [main.py](/C:/Users/rafae/documents/workspace/github/dinamica-budget/app/backend/main.py)
  FastAPI entrypoint and SPA serving glue.
- `backend/__init__.py`
  Python package marker.

### API Layer

- `app/backend/api/v1/router.py`
  Main API router composition.
- `app/backend/api/v1/endpoints/auth.py`
- `app/backend/api/v1/endpoints/busca.py`
- `app/backend/api/v1/endpoints/servicos.py`
- `app/backend/api/v1/endpoints/homologacao.py`
- `app/backend/api/v1/endpoints/usuarios.py`
- `app/backend/api/v1/endpoints/clientes.py`
- `app/backend/api/v1/endpoints/admin.py`
- `app/backend/api/v1/endpoints/composicoes.py`
- `app/backend/api/v1/endpoints/versoes.py`
- `app/backend/api/v1/endpoints/health.py`
- `app/backend/api/v1/endpoints/propostas.py`
- `app/backend/api/v1/endpoints/pq_importacao.py`
- `app/backend/api/v1/endpoints/cpu_geracao.py`
- `app/backend/api/v1/endpoints/pc_tabelas.py`
- `app/backend/api/v1/endpoints/extracao.py`

### Core Runtime

- `app/backend/core/config.py`
- `app/backend/core/database.py`
- `app/backend/core/security.py`
- `app/backend/core/dependencies.py`
- `app/backend/core/logging.py`
- `app/backend/core/exceptions.py`
- `app/backend/core/audit_hooks.py`
- `app/backend/core/rate_limit.py`

### Domain Models

- `app/backend/models/`
  SQLAlchemy entities, enums, and domain records for users, clients, catalog, compositions, proposals, PQ import, PC tables, history, associations, and audit logs.

### Schemas

- `app/backend/schemas/`
  Pydantic contracts for API requests/responses and domain DTOs.

### Services

- `app/backend/services/`
  Business logic for auth, search, homologation, catalog, embeddings, proposals, PQ import/match, CPU generation, ETL, and PC tables.

### Repositories

- `app/backend/repositories/`
  Data access layer for domain entities and supporting tables.

### ML

- `app/backend/ml/embedder.py`
- `app/backend/ml/vector_search.py`
- `app/backend/ml/fuzzy_search.py`

### Tests

- `app/backend/tests/unit/`
- `app/backend/tests/integration/`
- `app/backend/tests/e2e/`
- `app/backend/tests/conftest.py`

## 3.3 Frontend: `app/frontend/`

### Root

- `app/frontend/package.json`
- `app/frontend/vite.config.ts`
- `app/frontend/tsconfig.json`
- `app/frontend/index.html`
- `app/frontend/.env.example`

### Source

- `app/frontend/src/main.tsx`
- `app/frontend/src/app/`
  App bootstrap, providers, router, theme.
- `app/frontend/src/features/`
  Feature modules for auth, dashboard, search, services, homologation, compositions, associations, reports, profile, users, clients, admin, permissions.
- `app/frontend/src/shared/`
  Shared components, API clients, contracts, and utilities.
- `app/frontend/src/styles/`
  Global styles.
- `app/frontend/public/`
  Public assets.

### Generated

- `app/frontend/dist/`
  Build output.
- `app/frontend/node_modules/`
  Installed dependencies.

## 3.4 Database and Migrations: `app/alembic/`

- `app/alembic/env.py`
  Alembic environment using the moved backend package.
- `app/alembic/versions/`
  Migration history.

## 3.5 Model Cache: `app/ml_models/`

- `app/ml_models/`
  Local model cache/storage used by the application in on-prem deployments.

---

## 4. Project Documentation Workspace: `docs/`

Root layout:

- `docs/sprints/`
  Canonical sprint-by-sprint workspace.
- `docs/shared/`
  Canonical shared/project-wide workspace.

## 4.1 Sprint Tree

- `docs/sprints/S-01/` ... `docs/sprints/S-12/`
- `docs/sprints/S-XX/briefing/`
- `docs/sprints/S-XX/plans/`
- `docs/sprints/S-XX/technical-review/`
- `docs/sprints/S-XX/technical-feedback/`
- `docs/sprints/S-XX/walkthrough/done/`
- `docs/sprints/S-XX/walkthrough/reviewed/`
- `docs/sprints/S-XX/dispatch/`
- `docs/sprints/S-XX/security/`

## 4.2 Shared Tree

- `docs/shared/analysis/`
- `docs/shared/governance/`
- `docs/shared/manuals/`
- `docs/shared/operations/`
- `docs/shared/research/`
- `docs/shared/security/`
- `docs/shared/dispatch/`
- `docs/shared/pipeline/`
- `docs/shared/roles/`
- `docs/shared/superpowers/`
- `docs/shared/walkthrough/`

---

## 5. Agent and Automation Map

## 5.1 Canonical Agent Assets: `.agents/`

- `.agents/skills/`
  Canonical shared skill source.
- `.agents/skills/Superpowers/`
- `.agents/skills/context7-mcp/`
- `.agents/skills/project-pipeline/`
- `.agents/skills/semantic-memory/`

## 5.2 Agentic Bootstrap: `_agentic_foundation/`

- `_agentic_foundation/templates/`
- `_agentic_foundation/playbooks/`
- `_agentic_foundation/stacks/`
- `_agentic_foundation/personas/`
- `_agentic_foundation/scripts/`

## 5.3 Root Automation: `scripts/`

These scripts are not product source; they operate on the moved solution in `app/`.

Representative examples:

- [audit-quality-gate.ps1](/C:/Users/rafae/documents/workspace/github/dinamica-budget/scripts/audit-quality-gate.ps1)
- [benchmark_search.py](/C:/Users/rafae/documents/workspace/github/dinamica-budget/scripts/benchmark_search.py)
- [benchmark_embeddings.py](/C:/Users/rafae/documents/workspace/github/dinamica-budget/scripts/benchmark_embeddings.py)
- [test_model_ptbr.py](/C:/Users/rafae/documents/workspace/github/dinamica-budget/scripts/test_model_ptbr.py)
- [deploy-pc-tabelas.ps1](/C:/Users/rafae/documents/workspace/github/dinamica-budget/scripts/deploy-pc-tabelas.ps1)
- [fix-auth-login-admin.ps1](/C:/Users/rafae/documents/workspace/github/dinamica-budget/scripts/fix-auth-login-admin.ps1)

---

## 6. Canonical Ownership Summary

- Product solution root: `app/`
- Product backend: `app/backend/`
- Product frontend: `app/frontend/`
- Database evolution: `app/alembic/`
- Model cache/runtime assets: `app/ml_models/`
- Project docs: `docs/`
- Canonical skills: `.agents/skills/`
- Root engineering automation: `scripts/`
- Repo structural map: `PROJECT MAP.md`
