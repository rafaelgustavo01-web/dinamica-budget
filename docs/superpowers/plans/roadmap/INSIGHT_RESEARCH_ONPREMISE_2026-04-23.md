# Insight Estratégico — Research AI

> **Data:** 2026-04-23  
> **Autor:** Research AI (Kimi K2.5)  
> **Destino:** Product Owner (OpenCode CLI)  
> **Tema:** Reavaliação de prioridades para ambiente on-premise / intranet

---

## 1. O Problema

O ROADMAP atual aloca **~60% do esforço em infraestrutura, segurança e operação** antes de entregar o módulo de valor de negócio principal (Orçamentos). Em um ambiente **on-premise, intranet, rede fechada**, parte desse esforço é desproporcional ao risco real.

```
Esforço atual estimado:
├── M1 (Segurança/Arquitetura)  → 35%
├── M2 (Qualidade/Auditoria)    → 20%
├── M3 (Busca/Operação)         → 15%
├── M4 (UX/Governança)          → 10%
└── M5 (Orçamentos — CORE)      → 20%  ← Valor de negócio principal
```

---

## 2. Contexto On-Premise: O que Muda

| Preocupação | Ambiente Cloud/SaaS | Ambiente Intranet On-Premise |
|---|---|---|
| **Ameaças externas** | Alto risco (DDoS, SQLi massivo, data breach) | Baixo risco (rede fechada, VPN corporativa) |
| **Observabilidade** | Crítica (milhares de usuários, SLA 99.9%) | Básica é suficiente (dezenas de usuários, uptime interno) |
| **DevOps/Deploy** | CI/CD completo, blue-green, rollback automático | Script de cópia + IIS restart é aceitável |
| **RBAC** | Multi-tenant complexo, OAuth, SSO | Perfis locais (USUARIO/APROVADOR/ADMIN) são suficientes |
| **Fallbacks** | Circuit breaker, retry, degradation | Não há serviços externos para falhar |

**Conclusão:** Em intranet, o ataque surface é muito menor. Segurança deve focar em **controle de acesso interno**, não em hardening de infraestrutura.

---

## 3. O Custo da Oportunidade

Cada sprint de infra/segurança adiada é uma sprint de Orçamentos não entregue. O módulo de Orçamentos é o **diferencial competitivo** do sistema:

- Sem Orçamentos: o sistema é um catálogo de serviços com busca
- Com Orçamentos: o sistema gera propostas comerciais, CPUs, e justificativa de custos

**O usuário final (orçamentista) não percebe valor em:**
- Checklist OWASP completo
- Métricas de latência em Prometheus
- Runbook de 50 páginas
- Pipeline de embeddings perfeito

**O usuário final percebe valor em:**
- Criar uma proposta em 10 minutos
- Importar uma PQ e fazer match inteligente
- Gerar uma CPU com rastreabilidade de custos

---

## 4. Recomendação Estratégica: "Funciona Primeiro, Endurece Depois"

### 4.1 Reduzir M1 (Segurança/Arquitetura)

| Sprint | Ação Sugerida | Justificativa |
|---|---|---|
| **S-04** | **Simplificar drasticamente** | Em intranet, validar cliente nas rotas de escrita é suficiente. Não precisa de OWASP completo, WAF, ou hardening de headers HTTP. |
| **S-03** | **Adiar ou absorver em S-02** | Transações implícitas são aceitáveis para < 50 usuários concorrentes. Revisitamos quando houver carga real. |

**Escopo mínimo de S-04 (revisado):**
- Validar `cliente_id` nos endpoints POST/PATCH/DELETE
- Garantir que `is_admin` não bypassa tudo em produção
- **Remover:** checklist OWASP, testes de penetração, hardening de headers

### 4.2 Adiar M2 e M3.3 (Qualidade/Operação)

| Item | Decisão | Quando revisitar |
|---|---|---|
| S-06 (Runbook) | **Adiar para pós-M5** | Só quando o sistema estiver gerando orçamentos reais |
| S-08 (Auditoria pré-release) | **Adiar para pós-M5** | Gate de qualidade feito manualmente pelo QA é suficiente |
| S-14 (Observabilidade) | **Cancelar / P3** | Logs em arquivo + health check básico são suficientes |
| S-13 (Testes E2E) | **Reduzir** | Smoke test manual do orçamentista é aceitável para MVP |

### 4.3 Acelerar M5 (Orçamentos)

| Sprint | Nova Posição | Dependências Mínimas |
|---|---|---|
| **S-09** (Entidades/CRUD Propostas) | **Imediata** (assim que S-02 DONE) | S-02 (camadas) ✅ já satisfeita |
| **S-10** (Importação PQ + Match) | Após S-09 | S-05 (busca) — usar implementação atual, otimizar depois |
| **S-11** (Geração CPU) | Após S-10 | PcTabelas já populadas ✅ |
| **S-12** (UX Frontend) | Após S-11 | — |

### 4.4 Nova Ordem de Execução Sugerida

```
FASE A — Funcionalidade Core (entregar valor rápido)
  1. S-01 (Auth) → DONE ✅
  2. S-02 (Camadas) → DONE ✅
  3. S-04 REVISADO (RBAC mínimo para intranet) → PLAN → TODO
  4. S-09 (Propostas/CRUD) → BACKLOG → INICIADA
  5. S-10 (Importação PQ + Match) → BACKLOG
  6. S-11 (CPU) → BACKLOG
  7. S-12 (UX Frontend Orçamentos) → BACKLOG

FASE B — Estabilização (depois de M5 funcionando)
  8. S-03 (Transações) → quando houver carga real
  9. S-05 (Busca otimizada) → DONE ✅ (suficiente para MVP)
  10. S-06 (Runbook) → quando operação real começar
  11. S-07 (UX Permissões) → quando governança for crítica
  12. S-08 (Auditoria) → antes de go-live formal

FASE C — Otimização (pós-go-live)
  13. Observabilidade, E2E, CI/CD, tuning de embeddings
```

---

## 5. Riscos da Nova Estratégia

| Risco | Mitigação |
|---|---|
| Segurança interna negligenciada | S-04 revisado cobre RBAC básico; intranet limita exposição |
| Débito técnico acumula | Documentar TODOs técnicos; revisitar na Fase B |
| Sem runbook, incidentes demoram | Time reduzido (1 dev + 1 ops) conhece o sistema; runbook é 2-3 páginas |
| Sem testes E2E, regressão visual | Orçamentista faz UAT manual em cada release; aceitável para < 20 usuários |

---

## 6. Input para o PO

**Decisão recomendada:**
1. **Aprovar S-04 revisado** (escopo mínimo de RBAC para intranet)
2. **Adiar S-03, S-06, S-08, S-14** para pós-M5
3. **Mover S-09 para o próximo slot de WIP** (assim que S-04 for para DONE)
4. **Manter S-05 como DONE** (busca atual é suficiente para match de PQ)

**Se o PO concordar, o Research AI atualiza o ROADMAP.md e propõe novas descrições de sprint para S-04 revisado.**

---

*Insight gerado por Research AI com base na realidade on-premise do projeto. Aguardar decisão do PO antes de modificar qualquer artefato canônico.*
