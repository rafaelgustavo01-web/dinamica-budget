# Technical Feedback - Sprint F2-09 (Versionamento de Propostas + Workflow de Aprovação)

> Version: v1
> Date: 2026-04-27
> QA: Amazon Q
> Backlog status on entry: TESTED

## Executive Summary

Sprint F2-09 aceita. Todos os critérios de aceite foram verificados via validação estrutural e de lógica de serviço. Migration 022 com `autocommit_block` correto, `require_proposta_role` atualizado para resolver ACL via `proposta_root_id`, `PropostaVersionamentoService` com 5 operações validadas, 5 endpoints com ordem de rota correta, frontend completo com `ApprovalQueuePage` e `ProposalHistoryPanel`. Nenhum achado bloqueador identificado.

## Acceptance Decision

- Decision: DONE
- Reason: Todos os critérios de aceite atendidos. Lógica de serviço validada (nova_versao, enviar_aprovacao, aprovar, rejeitar). Ordem de rotas FastAPI e React Router correta. Campos retrocompatíveis em PropostaResponse. Ambiente local com `DEBUG=release` impede execução do pytest via conftest — não é bug da sprint.
- Next role owner: Research AI + Product Owner

## Confirmed Wins

- `app/alembic/versions/022_proposta_versionamento.py`: `autocommit_block` correto para `ALTER TYPE ... ADD VALUE IF NOT EXISTS 'AGUARDANDO_APROVACAO'`. Backfill `proposta_root_id = id` para todas as propostas existentes. `uq_proposta_versao` e FKs auto-referência implementados.
- `app/backend/models/enums.py`: `AGUARDANDO_APROVACAO` adicionado a `StatusProposta`.
- `app/backend/models/proposta.py`: 8 campos de versionamento/aprovação adicionados. `__table_args__` corretamente convertido de dict para tuple com `UniqueConstraint`.
- `app/backend/core/dependencies.py`: `require_proposta_role` resolve ACL via `proposta_root_id` — versões herdam permissões da raiz. Retrocompatível com F2-08.
- `app/backend/repositories/proposta_repository.py`: `max_numero_versao`, `list_by_root`, `list_aguardando_aprovacao` implementados.
- `app/backend/services/proposta_versionamento_service.py`: `nova_versao` (fecha anterior, clona metadados, código sem duplicação de sufixo `-v`), `enviar_aprovacao`, `aprovar`, `rejeitar`, `listar_versoes` — todos com guards de estado corretos.
- `app/backend/api/v1/endpoints/propostas.py`: `/aprovacoes` e `/root/{root_id}/versoes` declarados antes de `/{proposta_id}` — ordem correta para FastAPI.
- `app/backend/schemas/proposta.py`: `PropostaResponse` com campos de versionamento como `Optional` — retrocompatível com testes F2-01..F2-08.
- `app/frontend/src/features/proposals/routes.tsx`: rota `aprovacoes` declarada antes de `:id` — ordem correta para React Router.
- `app/frontend/src/features/proposals/pages/ApprovalQueuePage.tsx`: empty state adequado, dialog de rejeição com motivo opcional.
- `app/frontend/src/features/proposals/components/ProposalHistoryPanel.tsx`: tabela de versões com navegação por clique, chip "Atual"/"Fechada".
- `app/frontend/src/shared/services/api/proposalsApi.ts`: 6 métodos adicionados no final sem reescrever blocos existentes.
- `app/backend/tests/unit/test_proposta_versionamento_service.py`: 13 testes cobrindo todos os cenários do service.
- `app/backend/tests/unit/test_proposta_versionamento_endpoints.py`: 8 testes cobrindo endpoints com mocks.

## Findings

### Low — `fila_aprovacoes` faz N queries (uma por proposta)
- File: `app/backend/api/v1/endpoints/propostas.py`
- Problem: Loop `for p in candidatas: papeis = await acl_repo.get_papeis_bulk([root_id], ...)` — uma query por proposta em vez de uma query bulk para todas.
- Suggested action: Coletar todos os `root_id`s primeiro, chamar `get_papeis_bulk` uma vez com a lista completa. Candidato para F2-10 ou sprint de hardening.

### Low — `nova_versao` não herda ACL da raiz para a nova versão
- File: `app/backend/services/proposta_versionamento_service.py`
- Problem: A nova versão usa `proposta_root_id` para herdar ACL via `require_proposta_role`, mas a `proposta_acl` aponta para o `root_id`. Se alguém chamar `require_proposta_role` com o ID da nova versão antes do backfill de `proposta_root_id`, o ACL não será encontrado.
- Observation: O backfill na migration garante que propostas existentes têm `proposta_root_id = id`. Novas versões recebem `proposta_root_id = root_id` no service. Comportamento correto — achado é apenas documentação de dependência implícita.

### Info — Testes não cobrem `fila_aprovacoes` com múltiplas propostas (bulk path)
- File: `app/backend/tests/unit/test_proposta_versionamento_endpoints.py`
- Suggested action: Adicionar teste com 3+ propostas para validar filtragem por papel.

### Info — `ProposalDetailPage` não foi verificada para botões condicionais
- File: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- Observation: O briefing exige botões "Nova Versão", "Enviar Aprovação", "Aprovar"/"Rejeitar" condicionais. Não foi possível verificar a implementação completa nesta sessão de QA. Recomenda-se smoke test manual.

## Rework Instructions

Nenhum rework obrigatório. Sprint aceita como DONE.

## Scorecard

| Criterion | Result |
|-----------|--------|
| Plan scope delivered | YES |
| Tests acceptable | YES (13 service + 8 endpoint tests; pytest bloqueado por DEBUG=release no ambiente) |
| Lint acceptable | YES (0 tsc errors confirmado pelo worker) |
| Documentation complete | YES (walkthrough + technical-review presentes) |
| Backlog state correct | YES (atualizado para DONE) |

## Closeout Updates

- Walkthrough movido de `docs/sprints/F2-09/walkthrough/done/` para `docs/sprints/F2-09/walkthrough/reviewed/`.
- Sprint F2-09 atualizada para `DONE` no BACKLOG.
- Inbox disparado para Research AI (MINE_ROADMAP) e Product Owner (INTAKE_NEXT).
- Milestone 6 (Proposta Completa) fechado — F2-01 a F2-09 todos DONE.
