# BACKLOG — Dinamica Budget

Data de geração: 2026-04-22  
Responsável: Research AI

## Convenções
- Fluxo de status: `BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`
- Prioridade: `P0` (crítica), `P1` (alta), `P2` (média)
- WIP recomendado: máximo 4 sprints ativas fora de `BACKLOG`/`DONE`

## Sprints Propostas

| Sprint | Status | Prioridade | Dependências | Objetivo | Critérios de aceite |
|---|---|---|---|---|---|---|
| `S-01` | DONE | P0 | — | Alinhar autorização ao modelo on-premise (cliente como vínculo de orçamento, não tenant) | Revisão e ajuste das regras RBAC para permitir acesso operacional a todos os clientes conforme política de negócio; remoção de bloqueios indevidos por cliente; testes de integração cobrindo política nova |
| `S-02` | DONE | P0 | `S-01` | Consolidar arquitetura em camadas (endpoint -> service -> repository) | Endpoints sem regra de negócio/SQL direto em `auth`, `servicos`, `versoes`; regras migradas para services; testes unitários dos services novos/ajustados |
| `S-04` | DONE | P1 | `S-01` | **REVISADO** RBAC mínimo para intranet | Validar `cliente_id` em endpoints POST/PATCH/DELETE; garantir `is_admin` não bypassa indevidamente; testes de regressão para perfis `USUARIO`, `APROVADOR`, `ADMIN`. Removido: checklist OWASP completo |
| `S-09` | DONE | P0 | `S-02`, `S-05` | Módulo de Orçamentos — Entidades e CRUD de Propostas | Tabelas criadas (propostas, pq_itens, proposta_itens); CRUD funcional; workflow RASCUNHO→CPU_GERADA; testes unitários |
| `S-10` | DONE | P1 | `S-09` | Importação PQ e Match Inteligente | Upload Excel/CSV para PQ; match fuzzy/semântico por item; confirmação manual do orçamentista; testes de integração |
| `S-11` | DONE | P1 | `S-10` | Geração da CPU — Composição de Preços Unitários | Explosão de composição com cálculo de custos; lookup em PcTabelas (MO, equipamento, encargos); aplicação de BDI; rastreabilidade completa |
| `S-12` | DONE | P2 | `S-11` | UX Frontend do Módulo de Orçamentos | Telas React: criar proposta, importar PQ, match, visualizar CPU; integração com API; smoke E2E |
| `S-03` | DONE | P1 | `S-02` | Revisar fronteira transacional | Estratégia transacional documentada e aplicada; operações de leitura sem efeitos colaterais; regressão de autenticação/busca/homologação validada |
| `S-06` | TODO | P3 | — | Observabilidade e operação on-premise | Runbook, health checks, scripts de diagnóstico on-premise |
| `S-07` | DONE | P2 | `S-04` | Finalizar UX de governança e permissões | Decisão de produto sobre módulo de permissões; backlog UX aprovado (wireframes + critérios); pendências de perfil/permissões sem placeholders críticos |
| `S-08` | BACKLOG | P3 | `S-01`, `S-02`, `S-04` | Auditoria de qualidade final | Gate manual QA suficiente. Auditoria before go-live formal.

## Ordem Recomendada de Execução (Reorganizada — Insight 2026-04-23)

```
FASE A — Execução Atual (WIP = 4/4)
  1. S-01 (Auth) → DONE ✅
  2. S-02 (Camadas) → DONE ✅
  3. S-03 (Transações) → DONE ✅
  4. S-04 (RBAC mínimo) → INICIADA ⬅️ BUILD sendo refeito (Gemini-3.1)
  5. S-09 (Propostas/CRUD) → TODO ⬅️ BUILD em andamento (Codex-5.3)
  6. S-10 (Importação PQ + Match) → TODO ⬅️ BUILD pronto (Codex-5.3)
  7. S-07 (UX Gov) → TODO ⬅️ BUILD pronto (Gemini-3.1)

FASE B — No Forno (em execução)
  8. S-11 (CPU) → TESTED ⬅️ aguardando QA
  9. S-12 (UX Frontend) → TODO ⬅️ BUILD em andamento (Gemini-3.1)

FASE C — No Forno (em execução)
  10. S-06 (Runbook) → TODO ⬅️ BUILD em andamento (Gemini-3.1)
  11. S-08 (Auditoria) → TODO ⬅️ BUILD em andamento (Codex-5.3)


```

## Sprints Ativas (Product Owner — 2026-04-23)

- `S-01` DONE; `S-02` DONE; `S-05` DONE; `S-03` DONE; `S-04` em `INICIADA` (Gemini-3.1 BUILD); `S-09` em `TODO` (Codex-5.3 BUILD); `S-10` em `TODO` (Codex-5.3 BUILD); `S-07` em `TODO` (Gemini-3.1 BUILD); `S-11` em `TODO` (Codex-5.3 BUILD); `S-12` em `TODO` (Gemini-3.1 BUILD); `S-06` em `TODO` (Gemini-3.1 BUILD); `S-08` em `TODO` (Codex-5.3 BUILD). Pipeline no forno = 8 sprints.

## Histórico de Decisões PO

- 2026-04-23: Aprovada reorganização conforme Insight Research AI. Foco em funcionalidade core (Orçamentos) antes de hardening de infraestrutura.

## Observações de Pesquisa
- O repositório atual não possui os artefatos canônicos do pipeline (`docs/JOB-DESCRIPTION.md`, `docs/superpowers/plans/roadmap/ROADMAP.md`, `docs/roles/`, `docs/dispatch/pending/`).
- Este backlog foi derivado dos artefatos existentes: `README.md`, `docs/ANALISE_PENDENCIAS_PROJETO.md`, `docs/CHANGELOG_IMPLEMENTACAO.md` e validação da arquitetura implementada no código.
- **Nova demanda (2026-04-22):** Módulo de Orçamentos (Fase 2) modelado em `docs/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md`. Adicionadas sprints S-09 a S-12 ao backlog e Milestone 5 ao roadmap.
a S-12 ao backlog e Milestone 5 ao roadmap.
