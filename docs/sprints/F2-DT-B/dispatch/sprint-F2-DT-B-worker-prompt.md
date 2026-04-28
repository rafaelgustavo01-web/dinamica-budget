# Worker Handoff Prompt — Sprint F2-DT-B

> Delivered by: Scrum Master (PO + Arquiteto)
> Date: 2026-04-27

```
Kimi (kimi-k2.6), voce e o worker de execucao da sprint F2-DT-B no
projeto Dinamica Budget — Frontend Tech Debt Cleanup.

Leia o briefing primeiro:
@docs/sprints/F2-DT-B/briefing/sprint-F2-DT-B-briefing.md

Execute o plano aprovado:
@docs/sprints/F2-DT-B/plans/2026-04-27-frontend-tech-debt-cleanup.md

Arquivos de contexto:
@docs/shared/governance/BACKLOG.md
@docs/shared/governance/JOB-DESCRIPTION.md
@docs/analysis/amazonq_analysis.md
@docs/analysis/gemini_analysis.md
@docs/analysis/kimi_analysis.md
@app/frontend/package.json
@app/frontend/vite.config.ts
@app/frontend/src/features/proposals/components/ExportMenu.tsx
@app/frontend/src/features/proposals/components/ExpandableTreeRow.tsx
@app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
@app/frontend/src/shared/services/api/composicoesApi.ts

Worker assignment:
- Worker ID: kimi-k2.6
- Provider: Moonshot
- Mode: BUILD

Regras:
- Branch `main` apenas. Sem feature branches.
- Execute em 2 commits atomicos sequenciais conforme plan secao 4:
  Commit 1 = vitest scaffold (Vitest + RTL + MSW + package.json scripts)
  Commit 2 = polimento UI (ExportMenu erro, codigo_origem em filhos,
             botao delete, dedup tema)
- Mensagem de commit: `feat(f2-dt-b/N): <descricao>` (N = 1..2).
- `npm run build` e `tsc --noEmit` devem ficar verdes apos cada commit.
- Apos Commit 1, `npm run test` deve retornar "no tests found" sem
  erro de configuracao.
- Proibido tocar `app/backend/**`, `app/alembic/**`, `scripts/**`.
  Sprint F2-DT-A (Claude) detem ownership exclusivo. Conflito git =
  falha de processo.
- Contrato `codigo_origem` em `ComposicaoComponenteResponse` esta
  FROZEN no plan secao 3 — F2-DT-A entrega backend; voce declara o
  campo no TS.
- Para o botao Excluir (Task 2.4): VERIFIQUE PRIMEIRO se `DELETE
  /propostas/{id}` existe no backend (grep no router). Se nao existir,
  ESCONDA o botao (renderizar `null`). Nao implementar endpoint
  backend.
- NAO escrever testes smoke reais — isso e a sprint F2-DT-C (Solo,
  futura).
- Gerar ou atualizar:
  docs/sprints/F2-DT-B/technical-review/technical-review-2026-04-27-f2-dt-b.md
- Salvar walkthrough em:
  docs/sprints/F2-DT-B/walkthrough/done/walkthrough-F2-DT-B.md
- Atualizar docs/shared/governance/BACKLOG.md de TODO para TESTED ao
  concluir.
- Nao marcar a sprint como DONE.
- Bloqueio: registrar no walkthrough e parar — nao mudar status.

Itens fora de escopo (parking lot — nao tocar):
- A-04 kimi (i18n)
- M-01 kimi (componentes grandes)
- A-03 kimi (refactor Histograma compartilhado)
- A-02 kimi (DecimalValue drift)
```
