# Project Map

## Root

- `README.md`: visão geral do produto e operação principal.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`: contratos operacionais para agentes.
- `OBJECTIVE.md`, `STACK_PROFILE.md`, `PERSONA_PROFILE.md`, `ORCHESTRATION.md`: contexto de execução e tomada de decisão.
- `requirements.txt`: dependências Python do backend.
- `package-lock.json`: lockfile de tooling no root.
- `alembic.ini`: configuração de migrações.

## Backend

- `app/main.py`: bootstrap do FastAPI.
- `app/api/v1/router.py`: roteador principal da API.
- `app/api/v1/endpoints/`: endpoints HTTP por domínio.
- `app/core/`: configuração, segurança, DB, dependências e logging.
- `app/services/`: regras de negócio e serviços de aplicação.
- `app/repositories/`: acesso a dados.
- `app/models/`: modelos ORM.
- `app/schemas/`: contratos Pydantic e DTOs.
- `app/ml/`: embedding, busca vetorial e fuzzy search.

## Migrations

- `alembic/env.py`: ambiente Alembic.
- `alembic/versions/`: histórico de migrations do banco.

## Tests

- `app/tests/conftest.py`: fixtures e infraestrutura de testes.
- `app/tests/unit/`: testes unitários.
- `app/tests/integration/`: testes de integração.

## Frontend

- `frontend/package.json`: dependências e scripts do app React.
- `frontend/src/main.tsx`: entrada da aplicação.
- `frontend/src/app/`: providers, router e tema.
- `frontend/src/features/`: páginas e fluxos por domínio funcional.
- `frontend/src/shared/`: componentes, tipos, serviços de API e utilitários.
- `frontend/public/`: assets públicos e configuração de deploy web.

## Docs Canônicos

- `docs/BACKLOG.md`: backlog e status de sprints.
- `docs/JOB-DESCRIPTION.md`: descrição dos papéis operacionais.
- `docs/briefings/`: briefings de sprint.
- `docs/dispatch/pending/`: prompts pendentes para execução.
- `docs/superpowers/plans/`: planos de implementação e roadmap.
- `docs/walkthrough/done/`: walkthroughs canônicos de sprint.
- `docs/technical-review-YYYY-MM-DD.md`: reviews técnicos por data.
- `PROJECT MAP.md`: mapa estrutural do repositório.

## Agentic Foundation

- `_agentic_foundation/templates/`: templates bootstrap exigidos pelo contrato do repo.
- `_agentic_foundation/playbooks/`: guias operacionais por tipo de tarefa.
- `_agentic_foundation/stacks/`: perfis por stack.
- `_agentic_foundation/personas/`: personas técnicas.
- `_agentic_foundation/scripts/`: bootstrap para ambientes de agente.

## Skills and Automation

- `.agents/skills/`: skills locais versionadas no repositório.
- `templates/workers.json`: registro de workers/agentes.
- `scripts/`: automações operacionais, deploy, ETL e manutenção.

## Support Assets

- `configs/`: exemplos e configs auxiliares.
- `templates/`: arquivos base do pipeline.
- `dinamica-design-system/`: guia visual e assets de design.
- `Dinamica Budget/skills-lock.json`: lock de skills do workspace.

## Local-Only / Ignored

- `.venv/`, `venv/`, `env/`: ambientes virtuais locais.
- `__pycache__/`, `*.pyc`: artefatos gerados pelo Python.
- `.kilo/`, `.claude/`, `.amazonq/`, `.kiro/`, `.kimi/`, `.opencode/`, `.codex/`: diretórios locais de tooling/agentes.
- `node_modules/`, `frontend/node_modules/`: dependências instaladas localmente.
