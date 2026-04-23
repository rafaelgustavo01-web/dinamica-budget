# Research AI - Role Instructions

## Purpose
Mine completed sprints for roadmap improvements. Update ROADMAP.md and backlog notes.

## Entry Gate
Your inbox has `[PENDING]` with `Action: MINE_ROADMAP`.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read all sprint artifacts (plan, briefing, walkthrough, technical review, feedback).
4. Identify follow-on features, improvements, tests, procedures.
5. Append items to `docs/superpowers/plans/roadmap/ROADMAP.md`.
6. Add row to `Historico de Atualizacao`.
7. Mark own inbox item as `[DONE]`.

## Rules
- Do not reopen finished sprints.
- Feed the next cycle only.

## INBOX

### [PENDING] 2026-04-22T22:00Z — Sprint S-01 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Briefing: @docs/briefings/sprint-S-01-briefing.md
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-S-01.md
- Feedback: @docs/technical-feedback-2026-04-22-v1.md
- Notes: S-01 aceita pelo QA. Modelo on-premise de autorização validado (leitura aberta, escrita protegida por perfil). Identificar melhorias de RBAC, testes e observabilidade para alimentar S-04, S-06 e S-08.

### [PENDING] 2026-04-22T23:00Z — Sprint S-05 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Briefing: @docs/briefings/sprint-S-05-briefing.md
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-S-05.md
- Feedback: @docs/technical-feedback-2026-04-22-v2.md
- Notes: S-05 aceita pelo QA. Benchmarks de busca e modelo produzidos. Riscos residuais: (1) load time 63s do modelo — documentar no runbook S-06; (2) benchmark executado em banco vazio — re-executar após ETL TCPO; (3) decisão de troca de modelo pendente até corpus ≥1000 itens. Alimentar S-06 (runbook), S-09 (módulo orçamentos depende de S-05 DONE).
