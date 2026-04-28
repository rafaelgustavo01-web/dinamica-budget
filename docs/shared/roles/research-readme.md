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

### [PENDING] 2026-04-27T12:00:00Z — Sprint F2-09 (DONE)
- From: qa (Amazon Q)
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/F2-09/walkthrough/reviewed/walkthrough-F2-09.md
- Feedback: @docs/sprints/F2-09/technical-feedback/technical-feedback-2026-04-27-f2-09-v1.md
- Notes: F2-09 aceita. Milestone 6 (Proposta Completa) fechado. Versionamento com proposta_root_id como agrupador logico, nova_versao clona metadados (PQ/CPU comecam limpos), workflow de aprovacao opcional por flag requer_aprovacao. ACL herdada por root_id. 5 endpoints novos com ordem de rota correta. ApprovalQueuePage + ProposalHistoryPanel entregues. Alimentar ROADMAP com padroes de versionamento de entidades (root_id + numero_versao + is_versao_atual) e workflow de aprovacao multi-papel para reutilizacao em F2-10+.

### [PENDING] 2026-04-26T23:11:00Z — Sprint F2-08 (DONE)
- From: qa (Gemini 3.1 Pro)
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/F2-08/walkthrough/reviewed/walkthrough-F2-08.md
- Feedback: @docs/sprints/F2-08/technical-feedback/technical-feedback-2026-04-26-f2-08-v1.md
- Notes: F2-08 aceita. RBAC por Proposta. Migration 021, tabela `proposta_acl`, `require_proposta_role` implementados. Aprovado com sucesso.

### [PENDING] 2026-04-26T19:00:00Z — Sprint F2-07 (DONE)
- From: qa (Amazon Q)
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/F2-07/walkthrough/reviewed/walkthrough-F2-07-rework-v1.md
- Feedback: @docs/sprints/F2-07/technical-feedback/technical-feedback-2026-04-26-f2-07-v2.md
- Notes: F2-07 aceita apos rework v1. Motor de busca 4 camadas formalizado em MOTOR_BUSCA_4_CAMADAS.md. PropostaResumoRecurso populado em gerar-cpu. Endpoint GET /recursos + ProposalResourcesPage com Accordion por TipoRecurso. 143 PASS, 0 tsc errors. Alimentar ROADMAP com padroes de agregacao por tipo de recurso e documentacao de motores de busca em cascata.

### [PENDING] 2026-04-26T14:00:00Z — Sprint F2-06 (DONE)
- From: qa (Amazon Q)
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/F2-06/walkthrough/reviewed/walkthrough-F2-06.md
- Feedback: @docs/sprints/F2-06/technical-feedback/technical-feedback-2026-04-26-f2-06-v1.md
- Notes: F2-06 aceita. Edicao inline de PqItem, filtros combinados em GET /propostas e duplicacao de proposta com reset de match. 143 PASS, 0 tsc errors. Alimentar ROADMAP com padroes de edicao inline e filtros combinados.

### [PENDING] 2026-04-26T13:00:00Z — Sprint F2-03 (DONE)
- From: qa (Amazon Q)
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/F2-03/walkthrough/reviewed/walkthrough-F2-03.md
- Feedback: @docs/sprints/F2-03/technical-feedback/technical-feedback-2026-04-26-f2-03-v1.md
- Notes: F2-03 aceita. Tela de Revisao de Match completa com 2 endpoints backend e 3 componentes frontend. 6 PASS, 0 tsc errors. Alimentar ROADMAP com padroes de revisao manual de match.

### [PENDING] 2026-04-26T18:00:00Z — Sprint F2-05 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/F2-05/walkthrough/reviewed/walkthrough-F2-05.md
- Feedback: @docs/sprints/F2-05/technical-feedback/technical-feedback-2026-04-26-f2-05-v1.md
- Notes: F2-05 aceita. Exportacao Excel (4 abas: Capa/Quadro-Resumo/CPU/Composicoes) e PDF (folha de rosto) implementados com StreamingResponse. ExportMenu reutilizavel em ProposalDetailPage e ProposalCpuPage. 130 testes OK. Alimentar ROADMAP com padroes de exportacao de documentos formais.

### [PENDING] 2026-04-26T11:45:00Z — Sprint F2-02 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-F2-02.md
- Feedback: @docs/technical-feedback-2026-04-26-f2-02-v2.md
- Notes: F2-02 aceita. Explosao recursiva com arvore real (sem achatamento) implementada. Suporta BaseTcpo e ItemProprio. 118 testes unitarios OK. Alimentar ROADMAP com padroes de navegacao em arvore N niveis para UI.

### [PENDING] 2026-04-26T00:30:00Z — Sprint F2-04 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-F2-04.md
- Feedback: @docs/technical-feedback-2026-04-25-f2-04-v1.md
- Notes: F2-04 aceita. CPU detalhada e BDI dinamico implementados. Breakdown de custos por categoria (MAT/MO/EQUIP) funcional.

### [PENDING] 2026-04-22T22:45Z — Sprint S-02 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Walkthrough: @docs/sprints/S-02/walkthrough/reviewed/walkthrough-S-02.md
- Feedback: @docs/technical-feedback-2026-04-22-v3.md
- Notes: S-02 aceita. Arquitetura em camadas consolidada. AuthService unificou perfis. VersaoService gerencia clonagem de composicoes.

### [PENDING] 2026-04-22T22:00Z — Sprint S-01 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Briefing: @docs/sprints/S-01/briefing/sprint-S-01-briefing.md
- Walkthrough: @docs/sprints/S-01/walkthrough/reviewed/walkthrough-S-01.md
- Feedback: @docs/technical-feedback-2026-04-22-v1.md
- Notes: S-01 aceita pelo QA. Modelo on-premise de autorizacao validado.

### [PENDING] 2026-04-22T23:00Z — Sprint S-05 (DONE)
- From: qa
- Action: MINE_ROADMAP
- Briefing: @docs/sprints/S-05/briefing/sprint-S-05-briefing.md
- Walkthrough: @docs/sprints/S-05/walkthrough/reviewed/walkthrough-S-05.md
- Feedback: @docs/technical-feedback-2026-04-22-v2.md
- Notes: S-05 aceita pelo QA. Benchmarks de busca e modelo produzidos.
