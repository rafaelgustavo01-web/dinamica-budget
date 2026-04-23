# Análise de ROADMAP — Research AI

> **Data:** 2026-04-23  
> **Autor:** Research AI (Kimi K2.5)  
> **Destino:** Product Owner (OpenCode CLI) — para avaliação de inclusão no BACKLOG  
> **Restrição:** NÃO alterar BACKLOG.md diretamente. Este documento é input para decisão do PO.

---

## 1. Resumo Executivo

O ROADMAP atual cobre bem as milestones principais (M1–M5), mas apresenta **lacunas de cobertura** em áreas críticas para pré-produção: testes E2E, observabilidade técnica, documentação de API, automação de deploy e UX da Fase 1. Além disso, algumas fases do ROADMAP não possuem sprints formais mapeadas no BACKLOG.

---

## 2. Lacunas Identificadas (Priorizadas)

### 🔴 P1 — Sem sprint formal no BACKLOG

| # | Fase / Tema | Por que falta | Risco se omitido |
|---|---|---|---|
| 1 | **Testes E2E da Fase 1** (busca, associação, homologação, auth) | Só há testes unitários e integração parcial | Regressão visual/fluxo não detectada em produção |
| 2 | **Observabilidade Técnica** (logs estruturados, métricas de API, tracing) | S-06 cobre runbook operacional, mas não instrumentação | Falhas silenciosas em produção; MTTR alto |
| 3 | **Documentação de API** (OpenAPI/Swagger completo e atualizado) | Não há sprint dedicada | Onboarding lento; integração frontend quebrada por contrato desatualizado |
| 4 | **Automação de Deploy On-Premise** (scripts de build, pacote IIS, rollback) | Deploy é manual | Erros humanos em deploy; sem rollback rápido |

### 🟡 P2 — Fase do ROADMAP sem sprint mapeada

| # | Fase do ROADMAP | Status no BACKLOG | Sugestão |
|---|---|---|---|
| 5 | M2-F2.2 — Suite de Testes e Gate de Qualidade | Não mapeada | Criar sprint `S-13` ou absorver em S-06/S-08 |
| 6 | M3-F3.2 — Evolução do Pipeline de Embeddings | Não mapeada | Criar sprint `S-14` ou absorver em S-09 (match depende de embeddings) |
| 7 | M4-F4.2 — UX de Fluxos Críticos (Fase 1) | Não mapeada | Criar sprint `S-15` para melhorias de UX nos fluxos existentes |

### 🟢 P3 — Melhorias / Oportunidades

| # | Tema | Contexto |
|---|---|---|
| 8 | **ETL e Manutenção de Dados** | PcTabelas já populadas, mas não há sprint para evolução do pipeline ETL |
| 9 | **Performance Audit** (geral, não só busca) | S-05 cobre busca; mas endpoints de composição/versões também podem ter gargalo |
| 10 | **Checklist de Go-Live** formalizado | S-08 menciona auditoria pré-release, mas não um checklist operacional de deploy |

---

## 3. Recomendações de Ação para o PO

### Opção A — Criar sprints novas (recomendado para controle)

```
S-13: Gate de Qualidade e Testes E2E
  - Dependências: S-02, S-04
  - Escopo: Cypress/Playwright para Fase 1, gate de lint + testes + smoke

S-14: Observabilidade e Instrumentação
  - Dependências: S-04, S-06
  - Escopo: logs estruturados (JSON), métricas de API (latência/erros), health checks

S-15: UX de Fluxos Críticos (Fase 1)
  - Dependências: S-02, S-07
  - Escopo: melhorias de UX em busca → associação → homologação
```

### Opção B — Absorver em sprints existentes

- F2.2 (gate de qualidade) → absorver em `S-08` (Auditoria Pré-Release)
- F3.2 (embeddings) → absorver em `S-09` (módulo orçamentos já depende de busca)
- F4.2 (UX Fase 1) → absorver em `S-07` (governança de permissões + UX)

**Contra-indicação:** S-07 já é P2 e depende de S-04. Acumular escopo pode atrasar o módulo de orçamentos.

### Opção C — Adiar para pós-M5

- Mover P2/P3 itens para um **Milestone 6 — Pós-Lançamento** (continuos improvement)
- Risco: débito técnico acumula e dificulta manutenção

---

## 4. Dependências Cruzadas Atualizadas

```
S-03 (Transacional) ─┬─→ S-13 (E2E + Gate)
                     │
S-04 (Segurança) ────┼─→ S-06 (Runbook) ──→ S-14 (Observabilidade)
                     │
S-05 (Busca) ────────┼─→ S-09 (Orçamentos) ─┬─→ S-10 → S-11 → S-12
                     │                        │
                     └────────────────────────┴─→ S-14 (embeddings)
```

---

## 5. Input para ROADMAP.md

Seção sugerida a adicionar ao ROADMAP:

```markdown
## Milestone 6 — Operação e Evolução Contínua (P2/P3)

> **Nota:** Milestone de melhorias contínuas pós-estabilização da Fase 1.

### Fase 6.1 - Testes E2E e Gate de Qualidade
- Cobertura end-to-end dos fluxos críticos da Fase 1.
- Pipeline de verificação automatizada (lint + unit + integration + smoke E2E).

### Fase 6.2 - Observabilidade e Monitoramento
- Logs estruturados com correlação de request ID.
- Métricas de negócio (propostas criadas, CPUs geradas, tempo de match).

### Fase 6.3 - Automação de Deploy
- Scripts de build e pacote para IIS.
- Rollback automático em caso de health check falho.
```

---

## 6. Próximos Passos

1. **PO revisa** esta análise e decide quais itens priorizar
2. **PO cria/adiciona** sprints ao BACKLOG conforme decisão
3. **Research AI** atualiza ROADMAP.md quando PO confirmar inclusão
4. **SM** inclui novas sprints no ciclo de planejamento quando atingirem `INICIADA`

---

*Análise gerada por Research AI. Não alterar BACKLOG.md diretamente — aguardar decisão do PO.*
