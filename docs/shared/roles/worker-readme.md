# Worker - Role Instructions

## Purpose
Execute approved sprints. Produce walkthrough and technical review. Hand off to QA via inbox.

## Entry Gate
Your inbox has `[PENDING]` with `Action: BUILD` or `Action: REWORK`.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read the approved plan and briefing.
4. Execute with `/gsd-do`.
5. Generate/update technical review.
6. Write `docs/walkthrough/done/walkthrough-[id].md`.
7. Update BACKLOG row to `TESTED`.
8. Mark own inbox item as `[DONE]`.
9. **Write to QA inbox:** append to `docs/roles/qa-readme.md`:
   ```markdown
   ### [PENDING] [ISO-TIMESTAMP] — Sprint [ID]
   - From: worker ([worker-id])
   - Action: REVIEW
   - Walkthrough: @docs/walkthrough/done/walkthrough-[id].md
   - Technical Review: @docs/technical-review-YYYY-MM-DD.md
   - Tests: [results]
   ```

## Rules
- Execute only approved sprint scope.
- Do not mark sprint `DONE`.
- If blocked, mark inbox item as `[BLOCKED]` with reason.

## INBOX

### [DONE] 2026-04-29T18:31:00Z — Sprint F3-02
- From: PO / Scrum Master
- Action: BUILD_UIUX_FIXES
- Assigned Worker: claude-code
- Briefing: @docs/sprints/F3-02/briefing/sprint-F3-02-briefing.md
- Plan: @docs/sprints/F3-02/plans/2026-04-29-f3-02-demo-readiness.md
- Input Audit: @docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md
- Technical Review: @docs/sprints/F3-02/technical-review/technical-review-2026-04-29-f3-02.md
- Walkthrough: @docs/sprints/F3-02/walkthrough/done/walkthrough-F3-02.md
- Notes: Correções P1 aplicadas para apresentação; build e testes frontend verdes.


### [DONE] 2026-04-29T18:16:41Z — Sprint F3-01
- From: PO / Scrum Master
- Action: AUDIT_UIUX
- Assigned Worker: codex
- Briefing: @docs/sprints/F3-01/briefing/sprint-F3-01-briefing.md
- Plan: @docs/sprints/F3-01/plans/2026-04-29-f3-01-demo-readiness.md
- Technical Review: @docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md
- Walkthrough: @docs/sprints/F3-01/walkthrough/done/walkthrough-F3-01.md
- Tests: Gates bloqueados no ambiente (`tsc`/`eslint`/`vitest` ausentes; `npm ci` com `EAI_AGAIN`; `pytest` ausente).
- Notes: Auditoria UI/UX concluída sem alterar produção. Resultado: 0 P0, 7 P1, 4 P2; recomendações priorizadas para F3-02.


### [DONE] 2026-04-23T14:45:00Z — Sprint S-10
- From: supervisor
- Action: BUILD
- Assigned Worker: codex-5.3
- Briefing: @docs/sprints/S-10/briefing/sprint-S-10-briefing.md
- Plan: @docs/sprints/S-06/plans/2026-04-23-importacao-pq-match-inteligente.md
- Notes: Entregue em TESTED. Upload `.csv`/`.xlsx`, persistência de PQ e match inteligente implementados. 89 testes unitários PASS e handoff QA aberto.

### [DONE] 2026-04-23T14:45:00Z — Sprint S-07
- From: supervisor
- Action: BUILD
- Assigned Worker: gemini-3.1
- Briefing: @docs/sprints/S-07/briefing/sprint-S-07-briefing.md
- Plan: @docs/sprints/S-12/plans/2026-04-23-ux-governanca-permissoes.md
- Notes: Entregue em TESTED. Telas de usuários, perfil e dashboard atualizadas. Build OK. Handoff para OpenCode (QA).

### [DONE] 2026-04-23T14:50:00Z — Sprint S-11
- From: supervisor
- Action: BUILD
- Assigned Worker: codex-5.3
- Briefing: @docs/sprints/S-11/briefing/sprint-S-11-briefing.md
- Plan: @docs/sprints/S-10/plans/2026-04-23-geracao-cpu-composicao-precos.md
- Notes: Entregue em TESTED. CPU gerada com explosão reutilizando `servico_catalog_service`, lookup PcTabelas adaptado ao schema atual, 91 testes unitários PASS e handoff QA aberto.

### [DONE] 2026-04-23T14:50:00Z — Sprint S-12
- From: supervisor
- Action: BUILD
- Assigned Worker: gemini-3.1
- Briefing: @docs/sprints/S-12/briefing/sprint-S-12-briefing.md
- Plan: @docs/sprints/S-11/plans/2026-04-23-ux-frontend-modulo-orcamentos.md
- Notes: Entregue em TESTED. Telas de listagem, criação e importação funcionais. Tela de CPU entregue como placeholder aguardando S-11. Build OK. Handoff para OpenCode (QA).

### [DONE] 2026-04-23T10:25:00Z — Sprint S-09
- From: supervisor
- Action: BUILD
- Assigned Worker: codex-5.3
- Briefing: @docs/sprints/S-09/briefing/sprint-S-09-briefing.md
- Plan: @docs/sprints/S-04/plans/2026-04-23-entidades-propostas-crud.md
- Notes: Entregue em TESTED. Migration 017 aplicada com sucesso, 85 testes unitários PASS, handoff para QA aberto.

### [DONE] 2026-04-23T09:15:00Z — Sprint S-03
- From: supervisor
- Action: BUILD
- Assigned Worker: codex-5.3
- Briefing: @docs/sprints/S-03/briefing/sprint-S-03-briefing.md
- Plan: @docs/sprints/S-09/plans/2026-04-23-revisao-transacional.md
- Notes: Entregue em TESTED -> Aprovada pelo QA (DONE ✅). Estratégia transacional documentada, 6 testes transacionais adicionados, 80/80 testes unitários PASS.

### [DONE] 2026-04-23T11:30:00Z — Sprint S-04
- From: supervisor
- Action: BUILD
- Assigned Worker: kimi-k2.5 & gemini-3.1
- Briefing: @docs/sprints/S-04/briefing/sprint-S-04-briefing.md
- Plan: @docs/sprints/S-03/plans/2026-04-22-seguranca-rbac.md
- Notes: Implementação consolidada. 3 endpoints protegidos, 85 testes PASS, checklist OWASP FINAL gerado. S-04 movida para TESTED e handoff realizado para o QA (OpenCode).

### [DONE] 2026-04-22T20:30Z — Sprint S-02
- From: supervisor
- Action: BUILD
- Briefing: @docs/sprints/S-02/briefing/sprint-S-02-briefing.md
- Plan: @docs/sprints/S-02/plans/2026-04-22-arquitetura-camadas.md
- Notes: Entregue em TESTED. 6 tasks completadas, 74/74 testes unitarios PASS. Walkthrough e technical review gerados.

### [DONE] 2026-04-22T18:00Z -- Sprint S-05
- From: supervisor
- Action: BUILD
- Briefing: @docs/sprints/S-05/briefing/sprint-S-05-briefing.md
- Plan: @docs/superpowers/plans/2026-04-22-optimize-search-and-operational-cost.md
- Notes: Entregue em TESTED. Handoff para QA realizado em 2026-04-22T21:45Z (SM normalizacao).

### [DONE] 2026-04-23T15:20:00Z — Sprint S-06
- From: supervisor
- Action: BUILD
- Assigned Worker: gemini-3.1
- Briefing: @docs/sprints/S-06/briefing/sprint-S-06-briefing.md
- Plan: @docs/sprints/S-07/plans/2026-04-23-runbook-observabilidade-onpremise.md
- Notes: Entregue em TESTED. Endpoint /health, script PowerShell e Runbook operacional concluídos. Handoff para OpenCode (QA).

### [DONE] 2026-04-25T17:30:00Z — Sprint F2-02
- From: QA (gemini-cli)
- Action: REWORK
- Briefing: @docs/briefings/sprint-f2-02-rework-v1.md
- Feedback: @docs/technical-feedback-2026-04-25-f2-02-v1.md
- Notes: A implementação atual duplica itens devido ao uso de explosão recursiva (DFS) do catálogo em cada nível. Metadados (tipo, custo) e suporte a Itens Próprios ausentes nas sub-explosões. Ver detalhes no feedback.
- Status: **ARCHIVED → DONE** (Orchestrator sync 2026-04-29; sprint already closed/aligned in BACKLOG).

### [DONE] 2026-04-26T00:20:00Z — Sprint F2-02 (Rework v1)
- From: qa
- Action: REWORK
- Assigned Worker: kimi-k2.5
- Briefing: @docs/briefings/sprint-f2-02-rework-v1.md
- Plan: @docs/sprints/F2-02/plans/2026-04-25-explosao-recursiva.md
- Notes: Rework aplicado. _listar_filhos_diretos substitui explode_composicao DFS. Sub-composicoes com snapshot e metadados completos. Suporte a ItemProprio. 9 testes unitarios de explosao recursiva (3 novos). Regressao: 118 PASS / 0 FAIL. Handoff para QA aberto.

### [DONE] 2026-04-25T23:30:00Z — Sprint F2-04
- From: supervisor
- Action: BUILD
- Assigned Worker: kimi-k2.5
- Briefing: @docs/sprints/F2-04/briefing/sprint-F2-04-briefing.md
- Plan: @docs/sprints/F2-04/plans/2026-04-25-cpu-detalhada.md
- Notes: Entregue em TESTED. Schemas, repository, service, endpoints, frontend API, CpuTable accordion, ProposalCpuPage desbloqueada. Regressao: 115 PASS / 0 FAIL. TypeScript: 0 erros. Handoff para QA aberto.

### [DONE] 2026-04-25T16:10:00Z — Sprint F2-02
- From: supervisor
- Action: BUILD
- Assigned Worker: kimi-k2.5
- Briefing: @docs/sprints/F2-02/briefing/sprint-F2-02-briefing.md
- Plan: @docs/sprints/F2-02/plans/2026-04-25-explosao-recursiva.md
- Notes: Entregue em TESTED. Migration 019, modelo self-ref, service com guard de profundidade, endpoint explodir-sub e 6 testes novos. Regressao completa: 99 PASS / 0 FAIL (corrigidos imports `app.*` em 6 arquivos de teste existentes). Handoff para QA aberto.

### [DONE] 2026-04-23T15:20:00Z — Sprint S-08
- From: supervisor
- Action: BUILD
- Assigned Worker: codex-5.3
- Briefing: @docs/sprints/S-08/briefing/sprint-S-08-briefing.md
- Plan: @docs/sprints/S-08/plans/2026-04-23-auditoria-qualidade-final.md
- Notes: Entregue em TESTED. Quality gate executavel com `0 falhas`, smoke E2E `1 passed`, relatorio de go-live finalizado e handoff para QA aberto.

### [DONE] 2026-04-27T12:00:00Z — Sprint F2-12
- From: PO / Scrum Master
- Action: BUILD
- Assigned Worker: kimi-k2.6
- Briefing: @docs/sprints/F2-12/briefing/sprint-F2-12-briefing.md
- Plan: @docs/sprints/F2-12/plans/2026-04-27-refatoracao-tcpo.md
- Notes: Entregue em TESTED -> Aprovado pelo QA. Testes unitários atualizados com `descricao_indent` e `font.bold`. Lógica robusta de parsing garantida.

### [DONE] 2026-04-29T02:18:00Z — Sprint F2-DT-C
- From: supervisor / self-dispatch (HOLD liberado)
- Action: BUILD
- Assigned Worker: kimi-k2.6
- Briefing: @docs/sprints/F2-DT-C/briefing/sprint-F2-DT-C-briefing.md
- Plan: @docs/sprints/F2-DT-C/plans/2026-04-27-frontend-smoke-tests.md
- Notes: Entregue em TESTED. 4 arquivos de teste (13 asserts), helper test-utils.tsx, technical-review e walkthrough gerados. npm run test passa (13/13), npm run build verde, 0 tsc errors. Handoff para QA aberto.

### [DONE] 2026-04-27T12:15:00Z — Sprint F2-13
- From: PO / Scrum Master
- Action: BUILD
- Assigned Worker: kimi-k2.6
- Briefing: @docs/sprints/F2-13/briefing/sprint-F2-13-briefing.md
- Plan: @docs/sprints/F2-13/plans/2026-04-27-tree-table-composicoes.md
- Notes: Substituição do modelo flat por uma Table Expansível Hierárquica no Frontend do catálogo de bases. Carregamento lazily dos insumos/sub-serviços.
- Status: **ARCHIVED → DONE** (Orchestrator sync 2026-04-29; sprint already closed/aligned in BACKLOG).
