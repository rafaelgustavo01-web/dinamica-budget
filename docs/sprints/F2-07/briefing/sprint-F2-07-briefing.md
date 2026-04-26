# Sprint F2-07 — Briefing

**Sprint:** F2-07
**Titulo:** Tabelas de Recursos + Motor 4 Camadas
**Worker:** gemini-3.1 (Gemini CLI)
**Status:** TODO
**Data:** 2026-04-26

---

## Objetivo

Entrega dual com forte componente analitico-documental:

1. **Documentar e formalizar o motor de busca em 4 camadas** ja parcialmente presente no codigo (`BuscaService` + `PqMatchService`):
   - Camada 1: Historico Confirmado do Cliente (`associacao_inteligente`)
   - Camada 2: Codigo Exato (`base_tcpo.codigo` / `itens_proprios.codigo`)
   - Camada 3: Fuzzy pg_trgm (`similarity >= 0.65`)
   - Camada 4: Semantico pgvector (`1 - cosine_distance >= 0.70`)

2. **Tornar as 4 camadas explicitas no codigo** com early-exit, logging estruturado e cobertura de testes isolados por camada (refatoracao de `PqMatchService`).

3. **Criar `PropostaResumoRecurso`** — tabela agregada por `(tipo_recurso, descricao_insumo, unidade)` populada automaticamente apos `gerar-cpu`, exposta via `GET /propostas/{id}/recursos`.

4. **Frontend leve** — `ProposalResourcesPage` exibindo agregados por `TipoRecurso` (Accordion por grupo).

## Criterios de Aceite

- Documento `docs/shared/analysis/MOTOR_BUSCA_4_CAMADAS.md` criado com diagrama, thresholds e referencias para o codigo
- `PqMatchService` refatorado com metodos privados `_camada_1_historico`, `_camada_2_codigo_exato`, `_camada_3_fuzzy`, `_camada_4_semantico` e early-exit explicito
- Logging estruturado por camada (`logger.info("match_layer", layer=N, ...)`)
- Migration 020 criada e aplicavel (`alembic upgrade head` sem erro)
- `PropostaResumoRecurso` populada apos `gerar_cpu_para_proposta` (replace estrategia)
- `GET /propostas/{id}/recursos` retorna lista com filtro opcional por `tipo_recurso`
- Frontend `ProposalResourcesPage` com Accordion por TipoRecurso e subtotais
- Botao "Ver Recursos" em ProposalDetailPage
- Regressao de match (sprints anteriores) ainda passa
- npx tsc --noEmit sem erros
- python -m pytest backend/tests/ com 140+ PASS, 0 FAIL

## Plano

Arquivo: `docs/sprints/F2-07/plans/2026-04-26-tabelas-recursos-motor-4-camadas.md`

7 tasks:
1. Documento tecnico das 4 camadas
2. Backend model + migration 020 PropostaResumoRecurso
3. Backend repository + service de resumo (com testes)
4. Refatoracao do PqMatchService (4 camadas explicitas)
5. Integracao em gerar_cpu + endpoint GET /recursos
6. Frontend api + ProposalResourcesPage + rota
7. Validacao final

## Pre-requisito de leitura (CRITICO)

Antes de codar, leia em ordem:
1. `docs/shared/superpowers/plans/roadmap/MODELAGEM_ORCAMENTOS_FASE2.md`
2. `docs/shared/research/RESEARCH_CORE_FEATURES.md`
3. `docs/shared/superpowers/plans/roadmap/ANALISE_RESEARCH_2026-04-23.md`
4. `docs/shared/superpowers/plans/roadmap/ROADMAP.md` (Milestone 6, Fase 6.5)
5. `app/backend/services/busca_service.py` (Fase 0/1/2/3 ja codificadas como camadas)
6. `app/backend/services/pq_match_service.py` (match atual em PQ)
7. `app/backend/services/cpu_geracao_service.py`
8. `app/backend/models/enums.py` — TipoRecurso

## Contexto tecnico

- Tabela nova: `operacional.proposta_resumo_recursos` (UniqueConstraint composta)
- `tipo_recurso_enum` ja existe (criado em migration 017) — nao recriar
- Repo pattern: BaseRepository[Model] em `app/backend/repositories/base_repository.py`
- Logging: `from backend.core.logging import get_logger` (structlog)
- Frontend: padrao MUI Accordion, sem libs novas

## Dependencias

- F2-01 DONE (PQ Layout)
- F2-02 DONE (Explosao Recursiva — composicoes existem com tipo_recurso)
- F2-04 DONE (CPU gerada — necessaria para resumo)
- Conflito leve com F2-06 em `proposalsApi.ts` — coordenar imports

## Atencao especial (Gemini)

- **Refator de PqMatchService deve preservar comportamento** — esta sprint nao muda o que o motor encontra, apenas como ele se organiza. Validar com regressao.
- **Migration 020** deve seguir exato padrao de `019_recursao_composicao.py` (revision string, depends_on, schema "operacional")
- **Replace estrategia em resumo**: ao re-gerar CPU, deletar resumo anterior e re-inserir. Nao tentar UPSERT row-a-row.
- **Documento das 4 camadas** e entregavel principal — tratar com mesmo rigor de codigo
- **Encoding**: docs em UTF-8 limpo, sem mojibake. ASCII puro quando possivel
- **Aplicar migration localmente nao e obrigatorio** se DB nao estiver disponivel — mas a migration deve ser sintatically correta (`alembic check` se houver)
