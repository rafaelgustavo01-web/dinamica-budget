# Walkthrough — S-08 Auditoria de Qualidade Final

## Status

`TESTED`

## What Changed

- Added executable audit gate script in `scripts/audit-quality-gate.ps1`.
- Added smoke E2E for the proposal flow in `app/backend/tests/e2e/test_smoke_proposta.py`.
- Finalized the go-live audit report in `docs/auditoria-go-live-2026-04-23.md`.
- Fixed API router startup for the audited flow by removing the invalid `health.router` include in `app/api/v1/router.py`.

## Acceptance Criteria

- Audit script executa 5 checks e retorna quantidade de falhas: done.
- Endpoints de escrita seguem protegidos: done via regressao dedicada no quality gate.
- Frontend compila para producao: done.
- Smoke E2E do fluxo principal de orcamentos passa: done.
- Relatorio de go-live documenta cobertura e riscos residuais: done.

## Verification

- `pytest app/backend/tests/e2e/test_smoke_proposta.py -q` -> `1 passed`
- `powershell -ExecutionPolicy Bypass -File scripts\audit-quality-gate.ps1 -ProjectRoot .` -> `0 falhas`

## Notes For QA

- Focus review on the executable gate, the smoke flow (`criar proposta -> importar PQ -> match -> gerar CPU`), and the router fix found during the audit.
- The smoke test uses the real FastAPI app with controlled overrides to keep the release gate deterministic despite instability in the local PostgreSQL test database.

