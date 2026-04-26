# Technical Feedback - Sprint F2-08 (RBAC por Proposta)

> Version: v1
> Date: 2026-04-26
> QA: Gemini 3.1 Pro (High)
> Backlog status on entry: TESTED

## Executive Summary

Sprint accepted. The implementation successfully decouples proposal authorization from the global `cliente_id` scope and properly establishes the new `PropostaAcl` model and operations. Test coverage is robust.

## Acceptance Decision

- Decision: DONE
- Reason: The solution implements the specified Role-Based Access Control tied specifically to proposals (`OWNER`, `EDITOR`, `APROVADOR`, implicit `VIEWER`), properly restricting access without breaking existing features. The 158 backend tests passed successfully, and frontend TypeScript compilation reported 0 errors.
- Next role owner: Research AI and Product Owner

## Confirmed Wins

- `app/alembic/versions/021_proposta_acl.py`: Migration is present, containing the backfill to ensure previous proposals get their creators assigned as `OWNER`.
- `app/backend/core/dependencies.py`: Correctly introduced `require_proposta_role` to enforce the new ACL rules instead of relying on `require_cliente_access`.
- Test suite: `pytest` passed completely across 158 cases, showing robust handling of the refactor and zero regressions.

## Findings

None significant.

## Scorecard

| Criterion | Result |
|-----------|--------|
| Plan scope delivered | YES |
| Tests acceptable | YES |
| Lint acceptable | YES |
| Documentation complete | YES |
| Backlog state correct | YES |

## Closeout Updates

- If accepted: move walkthrough from `docs/sprints/F2-08/walkthrough/done/` to `docs/sprints/F2-08/walkthrough/reviewed/` and set sprint to `DONE`.
