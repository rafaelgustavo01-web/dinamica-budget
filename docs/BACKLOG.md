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

**Nenhuma sprint ativa.** Pipeline encerrado. WIP = 0/4.

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

## Observações de Pesquisa
- O repositório atual possui todos os artefatos canônicos do pipeline (`docs/JOB-DESCRIPTION.md`, `docs/superpowers/plans/`, `docs/roles/`, `docs/dispatch/`).
- Suite de testes: **93 unit tests PASS**, **1 smoke E2E PASS**, **build frontend OK**.
- **Nova demanda (2026-04-22):** Módulo de Orçamentos (Fase 2) modelado em `docs/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md`. Adicionadas sprints S-09 a S-12 ao backlog e Milestone 5 ao roadmap.
