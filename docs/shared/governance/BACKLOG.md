# BACKLOG — Dinamica Budget

Data de geração: 2026-04-23  
Responsável: Research AI / QA Re-avaliação

## Convenções
- Fluxo de status: `BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`
- Prioridade: `P0` (crítica), `P1` (alta), `P2` (média)
- WIP recomendado: máximo 4 sprints ativas fora de `BACKLOG`/`DONE`


## Status Operacional — 2026-04-29

- Ciclo concluído: `F2-10`, `F2-11`, `F2-12`, `F2-13`, `F2-DT-A`, `F2-DT-B`, `F2-DT-C` em DONE.
- WIP atual: **2/4** (`F3-01`, `F3-02` em TESTED aguardando QA Gemini).
- WIP assumido pelo PO em 2026-04-29: **4**; abrir novo ciclo assim que QA mover sprint de TESTED para DONE, respeitando dependências.
- Milestone 6 — Proposta Completa: **fechado**.
- Milestone 7 — Compras e Negociação: **GO condicional** validado por Codex + Claude; fica **pós-demo**, após saneamento/contratos.
- Decisão PO 2026-04-29: antes de Compras, abrir **Fase 3 — Demo Readiness / Polimento UI+UX** para corrigir erros de interface e deixar o fluxo apresentável esta semana.
- Sprints ativas: `F3-01` e `F3-02` em TESTED aguardando QA Gemini. Próximo ciclo só abre quando QA mover sprint para DONE.

## Sprints Propostas

| Sprint | Status | Prioridade | Dependências | Objetivo | Critérios de aceite |
|---|---|---|---|---|---|
| `S-01` | DONE | P0 | — | Alinhar autorização ao modelo on-premise (cliente como vínculo de orçamento, não tenant) | Revisão e ajuste das regras RBAC para permitir acesso operacional a todos os clientes conforme política de negócio; remoção de bloqueios indevidos por cliente; testes de integração cobrindo política nova |
| `S-02` | DONE | P0 | `S-01` | Consolidar arquitetura em camadas (endpoint -> service -> repository) | Endpoints sem regra de negócio/SQL direto em `auth`, `servicos`, `versoes`; regras migradas para services; testes unitários dos services novos/ajustados |
| `S-03` | DONE | P1 | `S-02` | Revisar fronteira transacional | Estratégia transacional documentada e aplicada; operações de leitura sem efeitos colaterais; regressão de autenticação/busca/homologação validada |
| `S-04` | DONE | P1 | `S-01` | **REVISADO** RBAC mínimo para intranet | Validar `cliente_id` em endpoints POST/PATCH/DELETE; garantir `is_admin` não bypassa indevidamente; testes de regressão para perfis `USUARIO`, `APROVADOR`, `ADMIN`. Removido: checklist OWASP completo |
| `S-05` | DONE | P1 | `S-02` | Otimizar busca e custo operacional | Benchmark de embeddings; índices pg_trgm/pgvector; cache de embedding com controle de versão; scripts de benchmark validados |
| `S-06` | DONE | P3 | — | Observabilidade e operação on-premise | Runbook, health checks, scripts de diagnóstico on-premise |
| `S-07` | DONE | P2 | `S-04` | Finalizar UX de governança e permissões | Decisão de produto sobre módulo de permissões; backlog UX aprovado (wireframes + critérios); pendências de perfil/permissões sem placeholders críticos |
| `S-08` | DONE | P3 | `S-01`, `S-02`, `S-04` | Auditoria de qualidade final | Gate manual QA suficiente. Auditoria before go-live formal. Projeto PRONTO para go-live |
| `S-09` | DONE | P0 | `S-02`, `S-05` | Módulo de Orçamentos — Entidades e CRUD de Propostas | Tabelas criadas (propostas, pq_itens, proposta_itens); CRUD funcional; workflow RASCUNHO→CPU_GERADA; testes unitários |
| `S-10` | DONE | P1 | `S-09` | Importação PQ e Match Inteligente | Upload Excel/CSV para PQ; match fuzzy/semântico por item; confirmação manual do orçamentista; testes de integração |
| `S-11` | DONE | P1 | `S-10` | Geração da CPU — Composição de Preços Unitários | Explosão de composição com cálculo de custos; lookup em PcTabelas (MO, equipamento, encargos); aplicação de BDI; rastreabilidade completa |
| `S-12` | DONE | P2 | `S-11` | UX Frontend do Módulo de Orçamentos | Telas React: criar proposta, importar PQ, match, visualizar CPU; integração com API; smoke E2E |
| `F2-01` | DONE | P1 | `S-09`, `S-10` | PQ Layout por Cliente — mapeamento de colunas configurável via `PqLayoutCliente` e `PqImportacaoMapeamento` | PUT /clientes/{id}/pq-layout retorna 200; PUT sem descricao retorna 422; GET sem config retorna null; 93+ PASS |
| `F2-02` | DONE | P1 | `S-11` | Explosão Recursiva de Composições — árvore N níveis com guard de profundidade (max 5) e endpoint `explodir-sub` | POST explodir-sub retorna 201 com lista de filhos; nivel>5 retorna 422; já explodida retorna 422; árvore real sem flattening; 118 PASS |
| `F2-03` | DONE | P1 | `S-10`, `F2-01` | Tela de Revisão de Match — confirmação manual dos itens PQ antes de gerar CPU; ações por item: confirmar/substituir/rejeitar | GET /pq/itens retorna lista; PATCH /pq/itens/{id}/match aceita acao; MatchReviewPage com progresso; 110+ PASS, 0 tsc errors |
| `F2-04` | DONE | P1 | `S-11`, `F2-03` | CPU Detalhada — breakdown de insumos por item (material/MO/equipamento) + BDI dinâmico recalculável sem regerar CPU | GET /cpu/itens/{id}/composicoes retorna insumos; POST /cpu/recalcular-bdi atualiza totais; CpuPage desbloqueada com accordion; 115 PASS |
| `F2-05` | DONE | P1 | `F2-03`, `F2-04` | Exportação — folha de rosto e quadro-resumo em Excel/PDF da proposta completa | Excel multi-aba (Capa/Resumo/CPU/Composições) e PDF folha de rosto; endpoints autenticados; frontend ExportMenu em ProposalDetailPage e ProposalCpuPage; 130+ PASS; 0 tsc errors |
| `F2-06` | DONE | P2 | `F2-03` | UX complementar — edição de PQ pós-importação, filtros de proposta, duplicação de proposta | PATCH /pq/itens edita descricao/qtd/unidade; filtros por status na lista; POST /propostas/{id}/duplicar |
| `F2-07` | DONE | P2 | `F2-01`, `F2-02` | Tabelas de Recursos + Motor 4 Camadas — agregado por recurso na CPU + busca formalizada em 4 camadas | PropostaResumoRecurso gerado ao chamar gerar-cpu; busca aplica histórico/código/fuzzy/semântico em ordem |
| `F2-08` | DONE | P0 | `F2-03`, `F2-04` | RBAC por Proposta — desacoplar autorização de cliente; ACL por usuário com papéis OWNER/EDITOR/APROVADOR (VIEWER implícito) e bypass via is_admin | Tabela proposta_acl + migration 021 + backfill OWNER; require_proposta_role substitui require_cliente_access em 5 routers; criador vira OWNER; last-OWNER guard; GET /propostas retorna meu_papel; modal de compartilhamento no front; 158 PASS; 0 tsc |
| `F2-09` | DONE | P1 | `F2-08` | Versionamento de Propostas + Workflow de Aprovação — proposta_root_id como agrupador, nova_versao clona snapshot, fluxo opcional aprovador/aprovado | Migration 022 com campos de versão + aprovação; POST /propostas/{id}/nova-versao; ACL herdada por root; aba Histórico no front; tela fila do APROVADOR; 170+ PASS; 0 tsc |
| `F2-10` | DONE | P1 | `F2-09` | **BCU Unificada (Base de Custos Unitários) + De/Para** — substituir `pc_*` por schema `bcu.*`; unificar uploads (remover Converter ETL + Carga inteligente PC); De/Para 1:1 manual entre `referencia.base_tcpo` e `bcu.*`; refatorar `cpu_custo_service` para usar mapeamento explícito | Migration 023 (drop pc_*, create schema bcu + de_para); BcuService importa BCU.xlsx + sync `referencia.base_tcpo` (codigo_origem); BcuDeParaService CRUD + validação tipo coerente; UI: BcuPage + BcuDeParaPage + uploads unificados; cpu_custo_service usa De/Para com fallback BaseTcpo; 200+ PASS; 0 tsc |
| `F2-11` | DONE | P1 | `F2-10` | **Histograma da Proposta** — snapshot editável per-proposta gerado a partir da sumarização das composições + BCU; recursos extras alocáveis; detecção de divergência BCU; trigger CPU desatualizada | Migration 024 (8 tabelas `proposta_pc_*` + recurso_extra + alocação + flag cpu_desatualizada); HistogramaService.montar_histograma; ProposalHistogramaPage com 7 abas editáveis + aba Recursos Extras + AlocacaoRecursoDialog; cpu_custo_service hierarquia proposta_pc > bcu > BaseTcpo; nova_versao clona histograma; 245+ PASS; 0 tsc |
| `F2-12` | DONE | P1 | `F2-11` | **Refatoração Importação TCPO (Débito Técnico)** — corrigir bug arquitetural onde subserviços `SER.CG` quebravam hierarquia; detectar serviço pai via `font.bold` + `alignment.indent==0` + `startswith("SER.")` | `parse_tcpo_pini` usa `values_only=False` + AND triplo (bold + indent + prefixo); 8 testes unitários com mocks openpyxl; 197 PASS regressão; 0 novos failures |
| `F2-13` | DONE | P1 | `F2-12` | **Tabela Hierárquica de Composições (UX Frontend)** — endpoint `GET /servicos/{id}/componentes` + `ExpandableTreeRow` recursivo/lazy loading | QA aprovado em 2026-04-29; smoke test incluído; branch `main` |
<!-- M7: Sprints originais de Compras permanecem ON-HOLD/SUPERSEDED até decisão PO pós-M7-0; não reutilizar `F2-13`. -->
| `F2-14` | ON-HOLD | P2 | `F2-13` | M7.3 — Frontend Tela de Compras — ProposalPurchasingPage com tabela de recursos, edição inline de ajustado, drawer de cotações por recurso **(SUSPENSA por decisão PO 2026-04-27)** | Rota /compras + menu; tabela com edição debounced; CotacaoForm com validações; botão Selecionar por cotação; 0 tsc errors |
| `F2-15` | ON-HOLD | P2 | `F2-13`, `F2-14` | M7.4 — Comparativo + Recálculo — endpoint comparativo agregado + recálculo automático de totais da Proposta + card no DetailPage **(SUSPENSA por decisão PO 2026-04-27)** | GET /comparativo-base-vs-ajustado retorna agregado; recalcular_totais disparado por selecionar/PATCH; card Comparativo no detail; coluna Total Ajustado na lista |
| `F2-DT-A` | DONE | P0 | — | **Backend Tech Debt Cleanup** — pytest infra resiliente + purga pipeline legado (subprocess + import_preview_service) + N+1 batch (5 services) + ETL durabilidade (tabela etl_preview); fecha 18 itens do checkpoint 2026-04-27 | 4 commits atomicos `feat(f2-dt-a/N)`; suite verde apos cada commit (197+ PASS); migration etl_preview com down_revision correto; query log histograma <=15 queries para 100 insumos; `codigo_origem` em ComposicaoComponenteResponse; branch main apenas |
| `F2-DT-B` | DONE | P1 | — | **Frontend Tech Debt Cleanup** — Vitest+RTL+MSW scaffold + ExportMenu erro/toast + ExpandableTreeRow exibe codigo_origem em filhos + ProposalDetailPage botao Excluir resolvido + dedup tema; paralela disjoint com F2-DT-A | 2 commits atomicos `feat(f2-dt-b/N)`; npm run build + tsc --noEmit verdes; npm run test "no tests found" sem erro; codigo_origem declarado no TS interface; branch main apenas |
| `F2-DT-C` | DONE | P2 | `F2-DT-A`, `F2-DT-B` | **Frontend Smoke Tests** — 4 arquivos de teste smoke em **/__tests__/** para Histograma (3 abas), ExpandableTreeRow, ProposalsListPage, ProposalDetailPage | 1 commit `test(f2-dt-c)`; 13 asserts; npm run test 13 PASS; npm run build verde; apenas arquivos novos (sem modificar producao); branch main apenas |
| `F3-01` | TESTED | P0 | `F2-DT-C` | **Demo Readiness Audit — UI/UX e fluxos críticos**: mapear erros visuais/funcionais que impedem apresentação; validar rotas principais de Propostas, Importação PQ, Match, CPU, Histograma, Composições, Exportação e RBAC visual | Relatório em `docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md`; 0 P0, 7 P1, 4 P2; sem alterar código; gates bloqueados por dependências/rede do ambiente |
| `F3-02` | TESTED | P0 | `F3-01` | **Correções críticas de UI/UX para apresentação**: corrigir bugs bloqueantes identificados em F3-01 nos fluxos demonstráveis; foco em telas de Proposta, Histograma, Composições e Exportação | Correções aplicadas em CPU, Match Review, Nova Proposta, Importar PQ, CPU error states, navegação da fila de aprovação e Histograma; `npm run build` PASS; `npm run test` PASS — 13 testes |
| `F3-03` | PLAN | P1 | `F3-02` | **Roteiro de apresentação + dados de demo**: preparar narrativa, checklist operacional, massa mínima/seed ou instruções reproduzíveis para demonstrar proposta completa | Documento `docs/sprints/F3-03/demo/demo-script-2026-04-29.md`; checklist de 10–15 minutos; dados/fixtures sem segredo; reset seguro documentado |
| `F3-04` | PLAN | P1 | `F3-02`, `F3-03` | **Polimento visual final + smoke de demo**: ajustar estados vazios/loading/erro, labels, botões, navegação e responsividade mínima; rodar QA final da apresentação | Demo checklist 100% PASS; screenshots/evidências em walkthrough; sem regressão em build/test; pendências não-críticas documentadas |

## Ordem Recomendada de Execução

```
FASE A — Fundação
  1. S-01 (Auth) → DONE ✅
  2. S-02 (Camadas) → DONE ✅
  3. S-03 (Transações) → DONE ✅
  4. S-04 (RBAC mínimo) → DONE ✅
  5. S-05 (Busca/Otimização) → DONE ✅

FASE B — Infraestrutura & Governança
  6. S-06 (Runbook/Observabilidade) → DONE ✅
  7. S-07 (UX Gov) → DONE ✅
  8. S-08 (Auditoria Final) → DONE ✅

FASE C — Módulo de Orçamentos
  9. S-09 (Propostas/CRUD) → DONE ✅
 10. S-10 (Importação PQ + Match) → DONE ✅
 11. S-11 (CPU) → DONE ✅
 12. S-12 (UX Frontend) → DONE ✅
```

## Sprints Ativas

**Fase 3 — Demo Readiness / Polimento UI+UX aberta em 2026-04-29.**

- WIP: **1/4**.
- Objetivo imediato: deixar o produto estável e apresentável esta semana antes de retomar Compras/M7.
- `F3-01` em TESTED: auditoria UI/UX concluída, com relatório e walkthrough gerados.
- `F3-02` em TESTED: correções críticas P1 aplicadas e gates frontend verdes.
- `F3-03` pode iniciar roteiro/dados de demo; `F3-04` aguarda QA/smoke final.
- Milestone 7 permanece **GO condicional pós-demo**.

### Decisões de alocação (Scrum Master, 2026-04-26)

- **Claude Code (sonnet-4-6)** → F2-06: maior superfície de UI/UX (tabela editável de PQ, filtros, modal de duplicação) com poucos endpoints de apoio.
- **Kimi-k2.5** → F2-05: domínio backend (openpyxl multi-aba, streaming de bytes, headers HTTP), template Excel determinístico, frontend mínimo.
- **Gemini-3.1** → F2-07: requer análise documental do RESEARCH/MODELAGEM_FASE2 para formalizar as 4 camadas, agregação por TipoRecurso, e novo modelo `PropostaResumoRecurso`.

## Sprints Concluídas (Fases 1 e 2)

Todas as 12 sprints concluídas com aprovação do QA:
- **S-01** DONE — Auth on-premise (QA: Amazon Q → reavaliado OpenCode)
- **S-02** DONE — Arquitetura em camadas (QA: Gemini CLI → reavaliado OpenCode)
- **S-03** DONE — Fronteira transacional (QA: OpenCode reavaliação)
- **S-04** DONE — RBAC mínimo intranet (QA: OpenCode)
- **S-05** DONE — Otimização de busca (QA: Amazon Q → reavaliado OpenCode)
- **S-06** DONE — Observabilidade on-premise (QA: OpenCode)
- **S-07** DONE — UX Governança e permissões (QA: OpenCode)
- **S-08** DONE — Auditoria de qualidade final (QA: OpenCode)
- **S-09** DONE — CRUD Propostas (QA: OpenCode)
- **S-10** DONE — Importação PQ + Match (QA: OpenCode)
- **S-11** DONE — Geração CPU (QA: OpenCode)
- **S-12** DONE — UX Frontend Orçamentos (QA: OpenCode)

## Evidências de QA

| Sprint | Technical Feedback | Technical Review | Walkthrough | Tests |
|---|---|---|---|---|
| S-01 | `technical-feedback-2026-04-22-v1.md` | `technical-review-2026-04-22.md` | `reviewed/walkthrough-S-01.md` | 93 passed (regressão) |
| S-02 | `technical-feedback-2026-04-22-v3.md` | `technical-review-2026-04-22-s02.md` | `reviewed/walkthrough-S-02.md` | 93 passed (regressão) |
| S-03 | `technical-feedback-2026-04-23-reavaliacao-sprints-v1.md` | `technical-review-2026-04-23-s03.md` | `done/walkthrough-S-03.md` | 93 passed (regressão) |
| S-04 | `technical-feedback-2026-04-23-s04-v1.md` | `technical-review-2026-04-23-s04.md` | `done/walkthrough-S-04.md` | 93 passed (regressão) |
| S-05 | `technical-feedback-2026-04-22-v2.md` | `technical-review-2026-04-22.md` | `reviewed/walkthrough-S-05.md` | 93 passed (regressão) |
| S-06 | `technical-feedback-2026-04-23-s06-v1.md` | `technical-review-2026-04-23-s06.md` | `done/walkthrough-S-06.md` | 93 passed (regressão) |
| S-07 | `technical-feedback-2026-04-23-s07-v1.md` | `technical-review-2026-04-23-s07.md` | `done/walkthrough-S-07.md` | 93 passed (regressão) |
| S-08 | `technical-feedback-2026-04-23-s08-v1.md` | `technical-review-2026-04-23-s08.md` | `done/walkthrough-S-08.md` | 93 passed (regressão) |
| S-09 | `technical-feedback-2026-04-23-s09-v1.md` | `technical-review-2026-04-23-s09.md` | `done/walkthrough-S-09.md` | 93 passed (regressão) |
| S-10 | `technical-feedback-2026-04-23-s10-v1.md` | `technical-review-2026-04-23-s10.md` | `done/walkthrough-S-10.md` | 93 passed (regressão) |
| S-11 | `technical-feedback-2026-04-23-s11-v1.md` | `technical-review-2026-04-23-s11.md` | `done/walkthrough-S-11.md` | 93 passed (regressão) |
| S-12 | `technical-feedback-2026-04-23-s12-v1.md` | `technical-review-2026-04-23-s12.md` | `done/walkthrough-S-12.md` | 93 passed (regressão) |

> **Nota:** Sprints S-03, S-04, S-06–S-12 não possuem cópia física do walkthrough em `docs/walkthrough/reviewed/` (apenas em `done/`). O QA aprovou via technical feedback formal. Recomenda-se mover os walkthroughs para `reviewed/` para fechar o ciclo documental.

## Histórico de Decisões PO

- 2026-04-23: Aprovada reorganização conforme Insight Research AI. Foco em funcionalidade core (Orçamentos) antes de hardening de infraestrutura.
- 2026-04-23 16:15: Reavaliação completa por QA (OpenCode) confirmou **todas as 12 sprints em DONE**. Pipeline encerrado. Projeto pronto para go-live.
- 2026-04-26: F2-03 entregue por claude-sonnet-4-6 (status TESTED, aguarda QA). F2-05/F2-06/F2-07 movidas para INICIADA → PLAN → TODO em batch para fechamento de Fase 2. WIP cap elevado para 4 por decisão excepcional do PO.
- 2026-04-26 (QA Amazon Q): F2-03 → DONE (6 PASS, 0 tsc). F2-06 → DONE (143 PASS, 0 tsc; bug debounce corrigido). F2-07 → DONE após rework v1 (143 PASS, 0 tsc; MOTOR_BUSCA_4_CAMADAS.md + GET /recursos + ProposalResourcesPage entregues).
- 2026-04-26 (PO pós-revisão "plano gpt"): adicionadas F2-08 (RBAC por Proposta — kimi-k2.5, P0) e F2-09 (Versionamento + Aprovação — claude-sonnet-4-6, P1). RBAC por proposta (OWNER/EDITOR/APROVADOR; VIEWER implícito) substitui gating por cliente em todos endpoints de proposta. Mini módulo de Compras + papel COMPRADOR + custo base/ajustado adiados para Milestone 7. F2-08 entra como prioridade por ser gap de segurança ativo.
- 2026-04-26 (Scrum Master): F2-08 despachada para kimi-k2.5. Status BACKLOG → INICIADA. Worker prompt em `docs/sprints/F2-08/dispatch/sprint-F2-08-worker-prompt.md`. WIP = 1/4 (apenas F2-08 ativa).
- 2026-04-27 (Scrum Master): F2-09 despachada para claude-sonnet-4-6. Desbloqueada por F2-08 DONE (QA Amazon Q). Status BACKLOG → INICIADA. Worker prompt em `docs/sprints/F2-09/dispatch/sprint-F2-09-worker-prompt.md`. WIP = 1/4 (F2-09 ativa). Fecha Milestone 6.
- 2026-04-26 (QA Amazon Q): F2-08 → DONE. Migration 021 validada (backfill OWNER correto, enum proposta_papel_enum pronto para F2-10). Bulk loader confirmado sem N+1. 25 testes novos (4 arquivos). Regressão dos 5 routers refatorados aprovada. Desbloqueia F2-09, F2-10, F2-11, F2-12, F2-13.
- 2026-04-26 (PO confirma Opção A para Milestone 7): adicionadas F2-10 a F2-13 cobrindo Compras + Negociação. F2-10 (custo base/ajustado + papel COMPRADOR — kimi); F2-11 (cotações CRUD — kimi); F2-12 (frontend tela Compras — claude-sonnet-4-6); F2-13 (comparativo + recálculo — claude-sonnet-4-6). Todas em BACKLOG aguardando F2-08 e F2-09 saírem de TESTED. Pré-requisito explícito: F2-08 entrega o enum proposta_papel_enum onde COMPRADOR será adicionado em F2-10.
- 2026-04-27 (PO + Arquiteto): **Reorganização de Milestone 7.** Identificada duplicação entre `pc_tabelas`, `Converter ETL` e `Carga inteligente PC`. Confirmada arquitetura nova com 2 sprints inseridos:
  - **F2-10 BCU Unificada** (substitui pc_* por schema bcu.* com schema dedicado; De/Para 1:1 manual TCPO↔BCU; unifica todos os uploads em um único pipeline; PO autorizou reset do banco — sem dados em PRD)
  - **F2-11 Histograma da Proposta** (snapshot editável per-proposta gerado pós-match; recursos extras alocáveis; detecção de divergência BCU; trigger cpu_desatualizada)
  - Sprints originais de Compras e Negociação **renomeadas e suspensas**: F2-12 (era F2-10 — Custo Base/Ajustado), F2-13 (era F2-11 — Cotações), F2-14 (era F2-12 — Frontend Compras), F2-15 (era F2-13 — Comparativo). Todas marcadas `ON-HOLD` até segunda ordem do PO.
  - Defaults arquiteturais aprovados: nome **BCU — Base de Custos Unitários** (pareia com CPU); De/Para 1:1 manual; trigger explícito "Montar Histograma"; snapshot sincronizado com aviso de divergência; recursos extras criáveis + alocáveis a composições; clonagem de histograma na nova versão; CPU desatualizada via flag (recálculo manual).
  - Plans gerados: `docs/sprints/F2-10/plans/2026-04-27-bcu-unificada-de-para.md` e `docs/sprints/F2-11/plans/2026-04-27-histograma-proposta.md`.
- 2026-04-27 (Scrum Master): F2-10 despachada para **kimi-k2.6** (backend-heavy: migration 023, BcuService, BcuDeParaService, cpu_custo_service refactor, endpoints). Status PLAN → TODO. Worker prompt em `docs/sprints/F2-10/dispatch/sprint-F2-10-worker-prompt.md`. F2-11 permanece PLAN (depende de F2-10 DONE); briefing + worker prompt preparados para **Gemini** (frontend-evident: 8 abas, 4 novos componentes, AlocacaoRecursoDialog) em `docs/sprints/F2-11/dispatch/`. WIP = 2/4 (F2-09 TESTED + F2-10 TODO).
- 2026-04-27 (PO + Arquiteto + SM): **Sprint de Divida Tecnica consolidada e particionada por ownership de arquivo.** Checkpoint tecnico (Amazon Q + Gemini + Kimi em `docs/analysis/`) consolidou 26 achados. Validacao manual confirmou 18 reais (3 falsos: DEBUG=release ja resolvido localmente; alguns parking lot). Estrategia force-multiplier: 3 sprints, 2 paralelas (zero conflito git por trees disjuntas) + 1 solo bloqueada.
  - **F2-DT-A (claude-sonnet-4-6, P0):** backend cleanup em 4 commits — pytest infra → purga legado (subprocess + import_preview_service) → N+1 batch (5 services) → ETL durabilidade. Fecha 18 itens. Plan em `docs/sprints/F2-DT-A/plans/2026-04-27-backend-tech-debt-cleanup.md`.
  - **F2-DT-B (kimi-k2.6, P1):** frontend cleanup em 2 commits — Vitest scaffold → polimento UI (ExportMenu, codigo_origem em filhos, botao delete, dedup tema). Fecha 5 itens. Plan em `docs/sprints/F2-DT-B/plans/2026-04-27-frontend-tech-debt-cleanup.md`.
  - **F2-DT-C (kimi-k2.6, P2, Solo HOLD):** smoke tests apos A+B em DONE. 4 arquivos de teste, 12+ asserts. Plan em `docs/sprints/F2-DT-C/plans/2026-04-27-frontend-smoke-tests.md`.
  - **Contrato congelado entre A e B:** `codigo_origem: str | None` em `ComposicaoComponenteResponse` — backend entrega no Commit 3 da DT-A, frontend declara TS na DT-B; codigo tolera assincronia.
  - **Regra de branch:** `main` apenas em todas as sprints. Sem feature branches (regra global do PO).
  - WIP = 4/4 (F2-09 TESTED + F2-10 TESTED + F2-11 TESTED + F2-13 TESTED + F2-DT-A TODO + F2-DT-B TODO + F2-DT-C PLAN-HOLD; cap excepcional para janela de cleanup).

- 2026-04-29 (PO): aprovada recomendação Codex+Claude de **GO condicional** para Milestone 7, mas com prioridade operacional alterada: antes de implementar Compras, abrir **Fase 3 — Demo Readiness / Polimento UI+UX** para corrigir erros de interface/experiência e preparar apresentação da semana. Criadas `F3-01` a `F3-04`; `F3-01` vai para TODO imediatamente, WIP=1/4. M7 permanece pós-demo, dependente de saneamento/contratos.
- 2026-04-29 (Worker/Codex): `F3-01` executada sem alteração de produção. Auditoria em `docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md`; walkthrough em `docs/sprints/F3-01/walkthrough/done/walkthrough-F3-01.md`. Resultado: 0 P0, 7 P1, 4 P2. Gates locais bloqueados por ausência de dependências e rede indisponível para `npm ci`.

## Observações de Pesquisa
- O repositório atual possui todos os artefatos canônicos do pipeline (`docs/JOB-DESCRIPTION.md`, `docs/superpowers/plans/`, `docs/roles/`, `docs/dispatch/`).
- Suite de testes: **93 unit tests PASS**, **1 smoke E2E PASS**, **build frontend OK**.
- **Nova demanda (2026-04-22):** Módulo de Orçamentos (Fase 2) modelado em `docs/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md`. Adicionadas sprints S-09 a S-12 ao backlog e Milestone 5 ao roadmap.
oadmap.
 S-12 ao backlog e Milestone 5 ao roadmap.
oadmap.

- 2026-04-29 (Worker/gedAI): `F3-02` implementada para demo readiness. Correções P1 em CPU/Match responsivo, guards de cliente/proposta, estados de erro de Importar/CPU, navegação de aprovação e divergências do Histograma. Gates frontend: `npm ci`, `npm run build`, `npm run test` PASS (13 testes).

- 2026-04-29 (PO): QA passa a ser executado preferencialmente por Gemini nas sprints em TESTED. Manter fluxo documental obrigatório: Briefing, Plan, Technical Review, Technical Feedback e Walkthrough.

- 2026-04-29 (QA dispatch): Gemini QA acionado para validar `F3-01` e `F3-02`, mas o Gemini CLI retornou 429 `MODEL_CAPACITY_EXHAUSTED` para `gemini-2.5-pro` e `gemini-2.5-flash`. QA permanece PENDING para retry; não mover TESTED para DONE sem feedback.

