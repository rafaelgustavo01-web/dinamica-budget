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

### [DONE] 2026-04-23T15:20:00Z — Sprint S-08
- From: supervisor
- Action: BUILD
- Assigned Worker: codex-5.3
- Briefing: @docs/sprints/S-08/briefing/sprint-S-08-briefing.md
- Plan: @docs/sprints/S-08/plans/2026-04-23-auditoria-qualidade-final.md
- Notes: Entregue em TESTED. Quality gate executavel com `0 falhas`, smoke E2E `1 passed`, relatorio de go-live finalizado e handoff para QA aberto.


