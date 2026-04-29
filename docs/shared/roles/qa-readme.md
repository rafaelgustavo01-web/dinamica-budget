# QA - Role Instructions

## Purpose
Verify sprint deliverables. Accept to DONE or reject with rework briefing. Hand off to Research + PO.

## Entry Gate
Your inbox has `[PENDING]` with `Action: REVIEW`.

## Actions
1. Read `docs/pipeline/config.md`.
2. Read your ## INBOX below.
3. Read walkthrough and technical review.
4. Run targeted verification.
5. Write `docs/technical-feedback-YYYY-MM-DD-vN.md`.
6. Mark own inbox item as `[DONE]`.
7. **If ACCEPTED:**
   - Update BACKLOG to `DONE`.
   - Move walkthrough to `docs/walkthrough/reviewed/`.
   - **Write to Research inbox:** append to `docs/roles/research-readme.md`
   - **Write to PO inbox:** append to `docs/roles/po-readme.md`
8. **If REJECTED:**
   - Create `docs/briefings/sprint-[id]-rework-v[N].md`.
   - Update BACKLOG to `TODO`.
   - **Write to Worker inbox:** append to `docs/roles/worker-readme.md`

## Rules
- Rejection MUST include precise rework list in new briefing file.
- Do not return to `TODO` without creating rework briefing.
- Expand verification scope only if blast radius requires it.

## INBOX

### [PENDING] 2026-04-29T02:20:00Z — Sprint F2-DT-C
- From: worker (kimi-k2.6)
- Action: REVIEW
- Walkthrough: @docs/sprints/F2-DT-C/walkthrough/done/walkthrough-F2-DT-C.md
- Technical Review: @docs/sprints/F2-DT-C/technical-review/technical-review-2026-04-29-f2-dt-c.md
- Tests: 13/13 PASS (4 test files), npm run build verde, 0 tsc errors
- Notes: Smoke tests para Histograma (4 asserts), ExpandableTreeRow (3 asserts), ProposalsListPage (2 asserts) e ProposalDetailPage (4 asserts). Apenas arquivos novos em `**/__tests__/**`; nenhuma modificação em código de produção.

### [PENDING] 2026-04-27T16:00:00Z — Sprint F2-11
- From: worker (gemini)
- Action: REVIEW
- Walkthrough: @docs/sprints/F2-11/walkthrough/done/walkthrough-F2-11.md
- Review: @docs/sprints/F2-11/technical-review/technical-review-2026-04-27-F2-11.md
- Notes: Histograma and Recursos Extras implemented. Backend API complete and tested. Frontend has functional components for viewing and navigating. Ready for QA.

### [DONE] 2026-04-26T23:11:00Z — Sprint F2-08
- From: worker (kimi-k2.5)
- Action: REVIEW
- Walkthrough: @docs/sprints/F2-08/walkthrough/reviewed/walkthrough-F2-08.md
- Technical Review: @docs/sprints/F2-08/technical-review/technical-review-2026-04-26-f2-08.md
- Feedback: @docs/sprints/F2-08/technical-feedback/technical-feedback-2026-04-26-f2-08-v1.md
- Tests: 158/158 PASS, 0 tsc errors
- Notes: RBAC por Proposta. Migration 021, tabela `proposta_acl`, `require_proposta_role` implementados. Aprovado com sucesso.
- Status: **ACCEPTED → DONE** (QA Gemini 3.1 Pro 2026-04-26)

### [DONE] 2026-04-26T12:00:00Z — Sprint F2-07
- From: worker (kimi-k2.5 rework v1)
- Action: REVIEW
- Walkthrough: @docs/sprints/F2-07/walkthrough/reviewed/walkthrough-F2-07-rework-v1.md
- Technical Review: @docs/sprints/F2-07/technical-review/technical-review-2026-04-26-f2-07-rework-v1.md
- Feedback: @docs/sprints/F2-07/technical-feedback/technical-feedback-2026-04-26-f2-07-v2.md
- Tests: 143/143 PASS, 0 tsc errors
- Notes: Rework v1 completo. MOTOR_BUSCA_4_CAMADAS.md criado, endpoint GET /recursos implementado e testado (2 testes), ProposalResourcesPage com Accordion, rota /recursos e botão Ver Recursos em ProposalDetailPage.
- Status: **ACCEPTED → DONE** (QA Amazon Q 2026-04-26)

### [DONE] 2026-04-26T11:45:00Z — Sprint F2-02 (Rework v1)
- From: worker (kimi-k2.5)
- Action: REVIEW
- Status: ACCEPTED
- Feedback: @docs/sprints/F2-02/techinical-feedback/technical-feedback-2026-04-26-f2-02-v2.md
- Notes: Rework validado. Árvore real implementada, sem duplicação. 118 testes PASS.

### [DONE] 2026-04-26T00:30:00Z — Sprint F2-04
- From: worker (kimi-k2.5)
- Action: REVIEW
- Status: ACCEPTED
- Feedback: @docs/technical-feedback-2026-04-25-f2-04-v1.md
- Notes: APROVADA. Breakdown detalhado e BDI dinâmico validados.

### [DONE] 2026-04-26T00:20:00Z — Sprint F2-02 (Rework v1)
- From: worker (kimi-k2.5)
- Action: REVIEW
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-F2-02.md
- Technical Review: @docs/sprints/F2-02/technical-review/technical-review-2026-04-25-f2-02.md
- Rework Briefing: @docs/briefings/sprint-f2-02-rework-v1.md
- Tests: `pytest app/backend/tests/unit/test_explosao_recursiva.py -v` -> `9 passed`; `pytest app/backend/tests/ -q` -> `118 passed, 0 failed`
- Notes: Rework v1 aplicado. Árvore real sem flattening, metadados completos em sub-níveis, suporte a ItemProprio.
- Status: **ACCEPTED → DONE** (QA Review 2026-04-26)

### [DONE] 2026-04-25T23:30:00Z — Sprint F2-04
- From: worker (kimi-k2.5)
- Action: REVIEW
- Walkthrough: @docs/walkthrough/reviewed/walkthrough-F2-04.md
- Technical Review: @docs/sprints/F2-04/technical-review/technical-review-2026-04-25-f2-04.md
- Tests: `pytest app/backend/tests/ -q` -> `115 passed, 0 failed`; `cd app/frontend && npx tsc --noEmit` -> `0 erros`
- Notes: CPU detalhada com breakdown de insumos, BDI dinamico, ProposalCpuPage desbloqueada. 8 testes unitarios novos.
- Status: **ACCEPTED → DONE** (QA Review 2026-04-26)

### [DONE] 2026-04-23T17:05:00Z — Sprint S-08
- From: worker (codex-5.3)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-08/walkthrough/done/walkthrough-S-08.md
- Technical Review: @docs/sprints/S-08/technical-review/technical-review-2026-04-23-s08.md
- Tests: `pytest app/backend/tests/e2e/test_smoke_proposta.py -q` -> `1 passed`; `powershell -ExecutionPolicy Bypass -File scripts\audit-quality-gate.ps1 -ProjectRoot .` -> `0 falhas`
- Notes: Auditoria de go-live concluida. Bug real no roteador (`health.router` invalido) corrigido durante a sprint. Recomendacao final: `GO`.
- Status: **ACCEPTED → DONE** (Reavaliação 2026-04-23)

### [DONE] 2026-04-23T16:00:00Z — Sprint S-06
- From: worker (gemini-3.1)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-06/walkthrough/done/walkthrough-S-06.md
- Technical Review: @docs/sprints/S-06/technical-review/technical-review-2026-04-23-s06.md
- Tests: `pytest app/backend/tests/unit/test_health.py -v` -> 2 passed. Script PowerShell validado.
- Notes: Runbook e Observabilidade. Endpoint /health e diagnóstico PowerShell para ambiente on-premise.
- Status: **ACCEPTED → DONE** (Reavaliação 2026-04-23)

### [DONE] 2026-04-23T15:30:00Z — Sprint S-12
- From: worker (gemini-3.1)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-12/walkthrough/done/walkthrough-S-12.md
- Technical Review: @docs/sprints/S-12/technical-review/technical-review-2026-04-23-s12.md
- Tests: `npm run build` -> Success.
- Notes: UX Frontend do Módulo de Orçamentos. Telas de Listagem, Detalhe, Criação e Importação integradas. Tela de CPU é um placeholder funcional bloqueado por S-11.
- Status: **ACCEPTED → DONE** (Reavaliação 2026-04-23)

### [DONE] 2026-04-23T15:20:00Z — Sprint S-11
- From: worker (codex-5.3)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-11/walkthrough/done/walkthrough-S-11.md
- Technical Review: @docs/sprints/S-11/technical-review/technical-review-2026-04-23-s11.md
- Tests: `pytest app/backend/tests/unit/test_cpu_geracao_service.py -q` -> 2 passed; `pytest app/backend/tests/unit -q` -> 91 passed.
- Notes: Geração da CPU com rebuild de `PropostaItem`, explosão reutilizada, cálculo de custos e endpoints `/cpu/gerar` e `/cpu/itens`.
- Status: **ACCEPTED → DONE** (Reavaliação 2026-04-23)

### [DONE] 2026-04-23T15:00:00Z — Sprint S-07
- From: worker (gemini-3.1)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-07/walkthrough/done/walkthrough-S-07.md
- Technical Review: @docs/sprints/S-07/technical-review/technical-review-2026-04-23-s07.md
- Tests: `npm run build` -> Success. Wireframes em @docs/ux-wireframes-governanca-2026-04-23.md.
- Notes: UX de Governança finalizada. Menu lateral atualizado (Relatórios e Perfil Ativos), gestão de RBAC centralizada em Usuários e resolução de nomes em Perfil.
- Status: **ACCEPTED → DONE** (Reavaliação 2026-04-23)

### [DONE] 2026-04-23T14:45:00Z — Sprint S-10
- From: worker (codex-5.3)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-10/walkthrough/done/walkthrough-S-10.md
- Technical Review: @docs/sprints/S-10/technical-review/technical-review-2026-04-23-s10.md
- Tests: `pytest app/backend/tests/unit/test_pq_import_service.py app/backend/tests/unit/test_pq_match_service.py -q` -> 4 passed; `pytest app/backend/tests/unit -q` -> 89 passed.
- Notes: Upload PQ `.csv`/`.xlsx`, criação de `PqImportacao`/`PqItem` e match automático via `BuscaService`.
- Status: **ACCEPTED → DONE** (Reavaliação 2026-04-23)

### [PENDING] 2026-04-23T12:10:00Z — Sprint S-09
- From: worker (codex-5.3)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-09/walkthrough/done/walkthrough-S-09.md
- Technical Review: @docs/sprints/S-09/technical-review/technical-review-2026-04-23-s09.md
- Tests: `pytest app/backend/tests/unit/test_proposta_service.py -q` -> 5 passed; `pytest app/backend/tests/unit -q` -> 85 passed; `alembic upgrade head` -> success.
- Notes: Módulo de Orçamentos — entidades operacionais, CRUD de propostas, migration 017 e isolamento por cliente.
- Status: **ACCEPTED → DONE** (QA Review 2026-04-23)

### [PENDING] 2026-04-23T11:30:00Z — Sprint S-04
- From: worker (kimi-k2.5 & gemini-3.1)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-04/walkthrough/done/walkthrough-S-04.md
- Technical Review: @docs/sprints/S-04/technical-review/technical-review-2026-04-23-s04.md
- Tests: `pytest app/backend/tests/unit/ -v` -> 85 passed. Checklist OWASP in @docs/owasp-checklist-2026-04-23-FINAL.md.
- Notes: Implementação consolidada de Kimi e Gemini. Foco em restabelecer isolamento de dados de clientes em rotas GET sensíveis.
- Status: **ACCEPTED → DONE** (QA Review 2026-04-23)

### [DONE] 2026-04-23T12:30:00Z — Sprint S-09
- From: QA (opencode)
- Action: REVIEW
- Status: ACCEPTED
- Feedback: @docs/technical-feedback-2026-04-23-s09-v1.md

### [DONE] 2026-04-23T12:30:00Z — Sprint S-04
- From: QA (opencode)
- Action: REVIEW
- Status: ACCEPTED
- Feedback: @docs/technical-feedback-2026-04-23-s04-v1.md

### [DONE] 2026-04-23T10:15:00Z — Sprint S-03
- From: worker (codex-5.3)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-03/walkthrough/reviewed/walkthrough-S-03.md
- Technical Review: @docs/sprints/S-03/technical-review/technical-review-2026-04-23-s03.md
- Feedback: @docs/technical-feedback-2026-04-23-s03-v1.md
- Notes: ACCEPTED → DONE. Estratégia transacional documentada e testes de pureza validados. S-03 fechada. Slot liberado para S-09.

### [DONE] 2026-04-22T22:45Z — Sprint S-02
- From: worker (Kimi)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-02/walkthrough/reviewed/walkthrough-S-02.md
- Technical Review: @docs/sprints/S-02/technical-review/technical-review-2026-04-22-s02.md
- Feedback: @docs/technical-feedback-2026-04-22-v3.md
- Notes: ACCEPTED → DONE. 74/74 testes unitários PASS. Mock de db.add corrigido pelo QA. Camada de serviço consolidada para Auth e Versões.

### [DONE] 2026-04-22T23:00Z — Sprint S-05
- From: worker (Codex)
- Action: REVIEW
- Walkthrough: @docs/sprints/S-05/walkthrough/reviewed/walkthrough-S-05.md
- Technical Review: @docs/sprints/S-05/technical-review/technical-review-2026-04-22.md
- Feedback: @docs/technical-feedback-2026-04-22-v2.md
- Notes: ACCEPTED → DONE. Todos os artefatos verificados. 2 issues low/info registrados (import dentro de método, benchmark em banco vazio). Riscos residuais documentados no feedback.

### [DONE] 2026-04-22T22:00Z — Sprint S-01
- From: worker (OpenCode)
- Action: REVIEW
- Feedback: @docs/technical-feedback-2026-04-22-v1.md
- Notes: Aceita. 75/75 testes. 2 correções aplicadas pelo QA (test_health_endpoint + SAWarnings). S-01 → DONE.


