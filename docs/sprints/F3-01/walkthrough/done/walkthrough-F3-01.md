# Walkthrough — F3-01 Demo Readiness Audit

Data: 2026-04-29  
Worker: codex  
Tipo: auditoria UI/UX sem alteração de produção.

## Escopo executado

- Li briefing e plano da sprint `F3-01`.
- Rodei os gates disponíveis de frontend/build/test e smoke existente.
- Auditei estaticamente as rotas principais: Dashboard, Propostas, Criar Proposta, Importar PQ, Revisão de Match, CPU, Histograma, Composições, Exportação, Histórico/Aprovação e RBAC visual.
- Gerei o relatório técnico em `docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md`.
- Não alterei código de produção.

## Gates

- `npm run build`: bloqueado por dependências ausentes (`tsc: not found`).
- `npm run lint`: bloqueado por dependências ausentes (`eslint: not found`).
- `npm run test`: bloqueado por dependências ausentes (`vitest: not found`).
- `npm ci --cache /tmp/npm-cache --prefer-offline`: bloqueado por rede/registry (`EAI_AGAIN` em `registry.npmjs.org`).
- `pytest app/backend/tests/e2e/test_smoke_proposta.py -q`: bloqueado (`pytest: command not found`).
- `python3 -m pytest backend/tests/e2e/test_smoke_proposta.py -q`: bloqueado (`No module named pytest`).

## Resultado

- P0: 0 achados confirmados.
- P1: 7 achados para F3-02.
- P2: 4 polimentos recomendados.
- Recomendação: corrigir os P1 antes da apresentação desta semana.

## Arquivos alterados

- `docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md`
- `docs/sprints/F3-01/walkthrough/done/walkthrough-F3-01.md`
- `docs/shared/governance/BACKLOG.md`
- `docs/shared/roles/worker-readme.md`
- `docs/shared/roles/qa-readme.md`

## Observações

- A execução deixou uma tentativa parcial de `node_modules` durante `npm ci`; ela foi removida antes do commit.
- O arquivo `.codex` já estava não versionado antes da sprint e não foi incluído.
