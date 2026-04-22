# BACKLOG — Dinamica Budget

Data de geração: 2026-04-22  
Responsável: Research AI

## Convenções
- Fluxo de status: `BACKLOG -> INICIADA -> PLAN -> TODO -> TESTED -> DONE`
- Prioridade: `P0` (crítica), `P1` (alta), `P2` (média)
- WIP recomendado: máximo 2 sprints ativas fora de `BACKLOG`/`DONE`

## Sprints Propostas

| Sprint | Status | Prioridade | Dependências | Objetivo | Critérios de aceite |
|---|---|---|---|---|---|
| `S-01` | TESTED | P0 | — | Alinhar autorização ao modelo on-premise (cliente como vínculo de orçamento, não tenant) | Revisão e ajuste das regras RBAC para permitir acesso operacional a todos os clientes conforme política de negócio; remoção de bloqueios indevidos por cliente; testes de integração cobrindo política nova |
| `S-02` | PLAN | P0 | `S-01` | Consolidar arquitetura em camadas (endpoint -> service -> repository) | Endpoints sem regra de negócio/SQL direto em `auth`, `servicos`, `versoes`; regras migradas para services; testes unitários dos services novos/ajustados |
| `S-03` | BACKLOG | P1 | `S-02` | Revisar fronteira transacional para reduzir commit implícito global | Estratégia transacional documentada e aplicada; operações de leitura sem efeitos colaterais; regressão de autenticação/busca/homologação validada |
| `S-04` | BACKLOG | P1 | `S-01` | Endurecer suíte de segurança e RBAC | Cobertura de autorização em todos endpoints sensíveis; testes de regressão para perfis `USUARIO`, `APROVADOR`, `ADMIN` e `is_admin`; checklist OWASP API básica executada |
| `S-05` | TODO | P1 | — | Otimizar busca semântica e custo operacional no servidor Windows | Plano de benchmark fuzzy vs semântico; decisão de modelo pt-BR/multilíngue; proposta de índice vetorial e tuning com evidência de latência |
| `S-06` | BACKLOG | P1 | — | Fechar lacunas de observabilidade e operação on-premise | Runbook de incidentes (API, DB, IIS, backup); procedimentos de restore testados; health checks e logs com critérios de alerta definidos |
| `S-07` | BACKLOG | P2 | `S-04` | Finalizar UX de governança e permissões | Decisão de produto sobre módulo de permissões; backlog UX aprovado (wireframes + critérios); pendências de perfil/permissões sem placeholders críticos |
| `S-08` | BACKLOG | P2 | `S-01`, `S-02`, `S-04` | Auditoria de qualidade final para pré-produção | Gate de qualidade definido (testes, lint, segurança, smoke E2E); evidências anexadas; checklist de go-live aprovado |

## Ordem Recomendada de Execução
1. `S-01`
2. `S-02`
3. `S-04` em paralelo com `S-03` (se equipe permitir)
4. `S-05` e `S-06`
5. `S-07`
6. `S-08`

## Sprints Ativas (Product Owner — 2026-04-22)
- `S-01` concluída em `TESTED`; `S-02` movida para `INICIADA`; `S-05` permanece em `TODO`. WIP atual = 2/2.
- Justificativa: `S-01` entregou o alinhamento de autorização on-premise com evidência de testes unitários e de integração. `S-02` é a próxima dependente crítica. `S-05` já tem plano e briefing preparados.

## Observações de Pesquisa
- O repositório atual não possui os artefatos canônicos do pipeline (`docs/JOB-DESCRIPTION.md`, `docs/superpowers/plans/roadmap/ROADMAP.md`, `docs/roles/`, `docs/dispatch/pending/`).
- Este backlog foi derivado dos artefatos existentes: `README.md`, `docs/ANALISE_PENDENCIAS_PROJETO.md`, `docs/CHANGELOG_IMPLEMENTACAO.md` e validação da arquitetura implementada no código.
