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

### [PENDING] 2026-04-26T11:45:00Z — Sprint F2-02 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-F2-02.md
- Feedback: @docs/technical-feedback-2026-04-26-f2-02-v2.md
- Notes: F2-02 aceita. Explosão recursiva com árvore real (sem achatamento) implementada. Suporta BaseTcpo e ItemProprio. 118 testes unitários OK. Alimentar ROADMAP com padrões de navegação em árvore N níveis para UI.

### [PENDING] 2026-04-26T00:30:00Z — Sprint F2-04 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-F2-04.md
- Feedback: @docs/technical-feedback-2026-04-25-f2-04-v1.md
- Notes: F2-04 aceita. CPU detalhada e BDI dinâmico implementados. Breakdown de custos por categoria (MAT/MO/EQUIP) funcional. Próximo: Alimentar ROADMAP com padrões de exportação de dados detalhados para F2-05.

### [PENDING] 2026-04-22T22:45Z — Sprint S-02 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/S-02/walkthrough/reviewed/walkthrough-S-02.md
- Feedback: @docs/technical-feedback-2026-04-22-v3.md
- Notes: S-02 aceita. Arquitetura em camadas (Service Layer) consolidada. Removido SQL de endpoints. AuthService unificou perfis (wildcard ADMIN). VersaoService gerencia clonagem de composições. Módulo de Orçamentos (S-09+) agora tem base sólida. Alimentar ROADMAP com padrões de serviço e checklists de refatoração para S-03 (Transações).

### [PENDING] 2026-04-22T22:00Z — Sprint S-01 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Briefing: @docs/sprints/S-01/briefing/sprint-S-01-briefing.md
- Walkthrough: @docs/sprints/S-01/walkthrough/reviewed/walkthrough-S-01.md
- Feedback: @docs/technical-feedback-2026-04-22-v1.md
- Notes: S-01 aceita pelo QA. Modelo on-premise de autorização validado (leitura aberta, escrita protegida por perfil). Identificar melhorias de RBAC, testes e observabilidade para alimentar S-04, S-06 e S-08.

### [PENDING] 2026-04-22T23:00Z — Sprint S-05 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Briefing: @docs/sprints/S-05/briefing/sprint-S-05-briefing.md
- Walkthrough: @docs/sprints/S-05/walkthrough/reviewed/walkthrough-S-05.md
- Feedback: @docs/technical-feedback-2026-04-22-v2.md
- Notes: S-05 aceita pelo QA. Benchmarks de busca e modelo produzidos. Riscos residuais: (1) load time 63s do modelo — documentar no runbook S-06; (2) benchmark executado em banco vazio — re-executar após ETL TCPO; (3) decisão de troca de modelo pendente até corpus ≥1000 itens. Alimentar S-06 (runbook), S-09 (módulo orçamentos depende de S-05 DONE).

