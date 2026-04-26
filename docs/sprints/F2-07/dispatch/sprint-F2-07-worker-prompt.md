# Worker Prompt — Sprint F2-07

**Para:** Gemini 3.1 (gemini-3.1)
**Modo:** Agent / BUILD
**Sprint:** F2-07 — Tabelas de Recursos + Motor 4 Camadas
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget

---

Voce e o worker da Sprint F2-07. Implemente o plano completo em `docs/sprints/F2-07/plans/2026-04-26-tabelas-recursos-motor-4-camadas.md` do inicio ao fim sem pausas.

## Por que voce foi escolhido

Esta sprint tem o **maior componente analitico-documental** entre as 3 ativas:
- Documento tecnico oficial das 4 camadas (entregavel principal, ~250 linhas, com diagrama)
- Refatoracao de servico complexo (`PqMatchService`) preservando comportamento — exige leitura cuidadosa do existente
- Modelagem de tabela agregada com UniqueConstraint composta + estrategia replace
- Pre-requisito explicito de leitura: 4 documentos de roadmap/research + 4 arquivos-chave do codigo

Sua capacidade de sintese documental densa + analise contextual de codebase grande faz match com o trabalho.

## Instrucoes de execucao

1. **OBRIGATORIO antes de codar**: leia em ordem os 8 documentos/arquivos listados na secao "Pre-requisito de leitura" do briefing
2. Leia o briefing em `docs/sprints/F2-07/briefing/sprint-F2-07-briefing.md`
3. Leia o plano em `docs/sprints/F2-07/plans/2026-04-26-tabelas-recursos-motor-4-camadas.md`
4. Execute cada task em ordem, commitando apos cada uma
5. Apos cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
6. Apos cada task de frontend: `cd app/frontend && npx tsc --noEmit`
7. Ao concluir TODAS as tasks: crie
   - `docs/sprints/F2-07/technical-review/technical-review-2026-04-26-f2-07.md`
   - `docs/sprints/F2-07/walkthrough/done/walkthrough-F2-07.md`
   - Atualize status do sprint para TESTED em `docs/shared/governance/BACKLOG.md`

## Atencao especial

- **REFATOR DE PqMatchService NAO MUDA COMPORTAMENTO** — apenas torna explicitas camadas hoje implicitas. Validar com regressao das sprints anteriores (F2-01/02/03/04).
- **Migration 020** segue exato padrao de `019_recursao_composicao.py`:
  - revision = "020", down_revision = "019"
  - schema = "operacional"
  - `tipo_recurso_enum` JA existe (de migration 017) — usar `create_type=False` no `SAEnum`, nao recriar enum no postgres
- **Replace estrategia**: ao re-gerar CPU, deletar resumo anterior e re-inserir. Nao tentar UPSERT row-a-row.
- **Documento das 4 camadas** (`MOTOR_BUSCA_4_CAMADAS.md`) e entregavel principal — tratar com mesmo rigor de codigo. Inclui diagrama ASCII, tabela camada->funcao, thresholds, e referencias para o codigo.
- **Logging estruturado**: usar `from backend.core.logging import get_logger` (structlog) e `logger.info("match_layer", layer=N, item_id=str(item.id), found=bool, confidence=float)`.
- **Conflito leve com F2-06** em `proposalsApi.ts`: adicionar tipos/metodos novos ao final, sem reescrever blocos existentes.
- **Encoding UTF-8 limpo**: docs e codigo sem mojibake. ASCII puro em strings de codigo quando possivel.

## Criterios de conclusao

- 140+ PASS, 0 FAIL no pytest (preserva regressao das sprints anteriores)
- 0 erros no tsc --noEmit
- Todos os 7 tasks com checkbox marcado
- Documento `MOTOR_BUSCA_4_CAMADAS.md` revisado e claro
- Migration 020 sintacticamente correta (`alembic check` sem erro, se tool disponivel)
- Documentos technical-review e walkthrough criados
- BACKLOG atualizado para TESTED

## Diretorio de trabalho

```
docs/shared/analysis/MOTOR_BUSCA_4_CAMADAS.md
app/backend/models/proposta.py
app/alembic/versions/020_proposta_resumo_recursos.py
app/backend/repositories/proposta_resumo_recurso_repository.py
app/backend/services/proposta_resumo_recurso_service.py
app/backend/services/pq_match_service.py
app/backend/services/cpu_geracao_service.py
app/backend/schemas/proposta.py
app/backend/api/v1/endpoints/proposta_recursos.py
app/backend/api/v1/router.py
app/backend/tests/unit/test_pq_match_4_camadas.py
app/backend/tests/unit/test_proposta_resumo_recurso_service.py
app/backend/tests/unit/test_proposta_recursos_endpoint.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/pages/ProposalResourcesPage.tsx
app/frontend/src/features/proposals/routes.tsx
app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
```

## Commits esperados (sequencia minima)

1. `docs(f2-07): formalize 4-layer search engine architecture`
2. `feat(f2-07): add PropostaResumoRecurso model and migration 020`
3. `feat(f2-07): add resumo recursos repository and service`
4. `refactor(f2-07): explicit 4-layer engine in PqMatchService with early-exit`
5. `feat(f2-07): integrate resumo into gerar_cpu and add GET /recursos endpoint`
6. `feat(f2-07): add ProposalResourcesPage with grouped accordion`
7. `docs(f2-07): add technical-review and walkthrough, handoff to QA`
