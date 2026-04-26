# Worker Handoff Prompt — Sprint F2-01

> Delivered by: Scrum Master (Claude Sonnet 4.6)
> Date: 2026-04-25

```
Codex 5.3, voce e o worker de execucao da sprint F2-01 no projeto Dinamica Budget.

Leia o briefing primeiro:
@docs/sprints/F2-01/briefing/sprint-F2-01-briefing.md

Execute o plano aprovado:
@docs/sprints/F2-01/plans/2026-04-25-pq-layout-cliente.md

Arquivos de contexto:
@docs/shared/governance/BACKLOG.md
@docs/shared/governance/JOB-DESCRIPTION.md
@app/backend/models/proposta.py
@app/backend/services/pq_import_service.py
@app/backend/api/v1/router.py

Worker assignment:
- Worker ID: claude-sonnet-4-6
- Provider: Anthropic (Claude Code)
- Mode: BUILD

Regras:
- Execute somente o escopo aprovado da sprint F2-01 (Tasks 1 a 7).
- Use somente o branch main. Nao crie feature branches.
- Gere ou atualize: docs/sprints/F2-01/technical-review/technical-review-2026-04-25-f2-01.md
- Salve o walkthrough em: docs/sprints/F2-01/walkthrough/done/walkthrough-F2-01.md
- Atualize docs/shared/governance/BACKLOG.md de TODO para TESTED ao concluir.
- Nao marque a sprint como DONE.
- Suite de regressao deve terminar com 93+ PASS e 0 FAIL antes de marcar TESTED.
- Migration 018 deve ter down_revision = "017".
- Reutilize padroes de repository existentes (ex: proposta_repository.py como referencia).
```
