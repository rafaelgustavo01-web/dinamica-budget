# Worker Handoff Prompt — Sprint F2-DT-A

> Delivered by: Scrum Master (PO + Arquiteto)
> Date: 2026-04-27

```
Claude Code (claude-sonnet-4-6), voce e o worker de execucao da sprint
F2-DT-A no projeto Dinamica Budget — Backend Tech Debt Cleanup.

Leia o briefing primeiro:
@docs/sprints/F2-DT-A/briefing/sprint-F2-DT-A-briefing.md

Execute o plano aprovado:
@docs/sprints/F2-DT-A/plans/2026-04-27-backend-tech-debt-cleanup.md

Arquivos de contexto:
@docs/shared/governance/BACKLOG.md
@docs/shared/governance/JOB-DESCRIPTION.md
@docs/analysis/amazonq_analysis.md
@docs/analysis/gemini_analysis.md
@docs/analysis/kimi_analysis.md
@app/backend/api/v1/endpoints/admin.py
@app/backend/services/etl_service.py
@app/backend/services/histograma_service.py
@app/backend/services/servico_catalog_service.py
@app/backend/services/cpu_geracao_service.py
@app/backend/services/proposta_versionamento_service.py
@app/backend/services/proposta_export_service.py
@app/backend/core/dependencies.py
@app/backend/core/config.py
@app/backend/tests/conftest.py
@app/backend/repositories/proposta_pc_repository.py

Worker assignment:
- Worker ID: claude-sonnet-4-6
- Provider: Anthropic (Claude Code)
- Mode: BUILD

Regras:
- Branch `main` apenas. Sem feature branches.
- Execute em 4 commits atomicos sequenciais conforme plan secao 4:
  Commit 1 = pytest infra
  Commit 2 = purga legado
  Commit 3 = N+1 batch + bundle
  Commit 4 = ETL durabilidade (com migration nova)
- Mensagem de commit: `feat(f2-dt-a/N): <descricao>` (N = 1..4).
- Suite de regressao DEVE ficar verde apos cada commit (197+ PASS,
  0 FAIL). Nao prosseguir para o proximo commit sem suite verde.
- Proibido tocar `app/frontend/**`. Sprint F2-DT-B (Kimi) detem ownership
  exclusivo dessa arvore. Conflito git = falha de processo.
- Contrato `codigo_origem` em `ComposicaoComponenteResponse` esta FROZEN
  no plan secao 3.5 — manter assinatura exata; F2-DT-B ja codifica
  frontend contra ele.
- Gerar ou atualizar:
  docs/sprints/F2-DT-A/technical-review/technical-review-2026-04-27-f2-dt-a.md
- Salvar walkthrough em:
  docs/sprints/F2-DT-A/walkthrough/done/walkthrough-F2-DT-A.md
- Atualizar docs/shared/governance/BACKLOG.md de TODO para TESTED ao
  concluir.
- Nao marcar a sprint como DONE.
- Bloqueio: registrar no walkthrough e parar — nao mudar status.

Itens fora de escopo (parking lot — nao tocar):
- A-04 kimi (i18n), M-04 kimi (DataTable), A-01 kimi (god classes)
- B-01..B-04 amazonq (cosmeticos), A-04 gemini (DecimalValue)
- A-05 amazonq (expunge), M-05 amazonq (require_cliente_access)
```
