# BACKLOG — Dinamica Budget

Data de geração: 2026-04-23  
Responsável: Research AI / QA Re-avaliação

## Convenções
- Fluxo de status: `BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`
- Prioridade: `P0` (crítica), `P1` (alta), `P2` (média)
- WIP recomendado: máximo 4 sprints ativas fora de `BACKLOG`/`DONE`

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
| `F2-03` | TESTED | P1 | `S-10`, `F2-01` | Tela de Revisão de Match — confirmação manual dos itens PQ antes de gerar CPU; ações por item: confirmar/substituir/rejeitar | GET /pq/itens retorna lista; PATCH /pq/itens/{id}/match aceita acao; MatchReviewPage com progresso; 110+ PASS, 0 tsc errors |
| `F2-04` | DONE | P1 | `S-11`, `F2-03` | CPU Detalhada — breakdown de insumos por item (material/MO/equipamento) + BDI dinâmico recalculável sem regerar CPU | GET /cpu/itens/{id}/composicoes retorna insumos; POST /cpu/recalcular-bdi atualiza totais; CpuPage desbloqueada com accordion; 115 PASS |
| `F2-05` | TODO | P1 | `F2-03`, `F2-04` | Exportação — folha de rosto e quadro-resumo em Excel/PDF da proposta completa | Endpoint gera arquivo Excel multi-aba; frontend tem botao de download; template com dados do cliente e totais |
| `F2-06` | TODO | P2 | `F2-03` | UX complementar — edição de PQ pós-importação, filtros de proposta, duplicação de proposta | PATCH /pq/itens edita descricao/qtd/unidade; filtros por status na lista; POST /propostas/{id}/duplicar |
| `F2-07` | TODO | P2 | `F2-01`, `F2-02` | Tabelas de Recursos + Motor 4 Camadas — agregado por recurso na CPU + busca formalizada em 4 camadas | PropostaResumoRecurso gerado ao chamar gerar-cpu; busca aplica histórico/código/fuzzy/semântico em ordem |

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

**Fase 3 — segunda leva.** WIP = 4/4 (excecao autorizada pelo PO em 2026-04-26 para acelerar fechamento de Fase 2).

- `F2-01` DONE — PQ Layout por Cliente (Worker: claude-sonnet-4-6) — QA aprovado 2026-04-25
- `F2-02` DONE — Explosão Recursiva de Composições (Worker: kimi-k2.5) — QA aprovado 2026-04-26 (pos-rework)
- `F2-03` TESTED — Tela de Revisão de Match (Worker: claude-sonnet-4-6) — entregue 2026-04-26, aguarda QA
- `F2-04` DONE — CPU Detalhada + BDI Dinâmico (Worker: kimi-k2.5) — QA aprovado 2026-04-25
- `F2-05` TODO — Exportação Excel/PDF (Worker: kimi-k2.5) — backend-pesado: openpyxl + endpoints + small frontend hook
- `F2-06` TODO — UX complementar (Worker: claude-sonnet-4-6) — frontend-pesado: edição PQ, filtros, duplicação
- `F2-07` TODO — Tabelas Recursos + Motor 4 Camadas (Worker: gemini-3.1) — análise documental densa + algoritmo de busca cascata

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

## Observações de Pesquisa
- O repositório atual possui todos os artefatos canônicos do pipeline (`docs/JOB-DESCRIPTION.md`, `docs/superpowers/plans/`, `docs/roles/`, `docs/dispatch/`).
- Suite de testes: **93 unit tests PASS**, **1 smoke E2E PASS**, **build frontend OK**.
- **Nova demanda (2026-04-22):** Módulo de Orçamentos (Fase 2) modelado em `docs/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md`. Adicionadas sprints S-09 a S-12 ao backlog e Milestone 5 ao roadmap.
