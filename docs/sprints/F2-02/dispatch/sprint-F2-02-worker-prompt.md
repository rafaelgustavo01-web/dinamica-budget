# Worker Handoff Prompt — Sprint F2-02

> Delivered by: Scrum Master (Claude Sonnet 4.6)
> Date: 2026-04-25

```
Kimi K2.5, voce e o worker de execucao da sprint F2-02 no projeto Dinamica Budget.

Leia o briefing primeiro:
@docs/sprints/F2-02/briefing/sprint-F2-02-briefing.md

Execute o plano aprovado:
@docs/sprints/F2-02/plans/2026-04-25-explosao-recursiva.md

Arquivos de contexto:
@docs/shared/governance/BACKLOG.md
@docs/shared/governance/JOB-DESCRIPTION.md
@app/backend/models/proposta.py
@app/backend/services/cpu_explosao_service.py
@app/backend/api/v1/endpoints/cpu_geracao.py

Worker assignment:
- Worker ID: kimi-k2.5
- Provider: Kimi CLI
- Mode: BUILD

Regras:
- Execute somente o escopo aprovado da sprint F2-02 (Tasks 1 a 5).
- Use somente o branch main. Nao crie feature branches.
- Gere ou atualize: docs/sprints/F2-02/technical-review/technical-review-2026-04-25-f2-02.md
- Salve o walkthrough em: docs/sprints/F2-02/walkthrough/done/walkthrough-F2-02.md
- Atualize docs/shared/governance/BACKLOG.md de TODO para TESTED ao concluir.
- Nao marque a sprint como DONE.
- Suite de regressao deve terminar com 93+ PASS e 0 FAIL antes de marcar TESTED.
- Migration 019 deve ter down_revision = "018".
- Self-reference SQLAlchemy: use foreign_keys e remote_side explicitos.
- Nao quebrar a logica de explosao de nivel 0 existente.
```
