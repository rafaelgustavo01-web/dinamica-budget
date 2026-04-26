# Worker Prompt — Sprint F2-04

**Para:** Kimi K2.5 (kimi-k2.5)
**Modo:** BUILD / Always Proceed
**Sprint:** F2-04 — CPU Detalhada — Breakdown de Insumos e BDI Dinamico
**Repo:** /path/to/dinamica-budget

---

Voce e o worker da Sprint F2-04. Implemente o plano completo em `docs/sprints/F2-04/plans/2026-04-25-cpu-detalhada.md` do inicio ao fim sem pausas.

## Instrucoes de execucao

1. Leia o plano em `docs/sprints/F2-04/plans/2026-04-25-cpu-detalhada.md`
2. Leia o briefing em `docs/sprints/F2-04/briefing/sprint-F2-04-briefing.md`
3. Execute cada task em ordem, fazendo commit apos cada uma
4. Execute `python -m pytest backend/tests/ -v --tb=short` apos cada task de backend
5. Execute `npx tsc --noEmit` apos cada task de frontend (tasks 5, 6, 7)
6. Ao concluir: crie `docs/sprints/F2-04/technical-review/technical-review-2026-04-25-f2-04.md` e `docs/sprints/F2-04/walkthrough/done/walkthrough-F2-04.md`

## Atencao especial

- `PropostaItemComposicao` tem coluna `tipo_recurso` que e um enum SQLAlchemy. Ao serializar para `ComposicaoDetalheResponse`, use `tipo_recurso.value if tipo_recurso else None`
- `PropostaItemRepository` pode nao ter `get_by_id` — verifique e adicione se necessario antes de usar
- `PropostaItemComposicaoRepository` — leia o arquivo antes de adicionar `list_by_proposta_item` para nao duplicar imports

## Criterios de conclusao

- 115+ PASS, 0 FAIL no pytest
- 0 erros no tsc --noEmit
- Todos os 7 tasks com checkbox marcado

## Diretorio de trabalho

```
app/backend/schemas/proposta.py
app/backend/repositories/proposta_item_composicao_repository.py
app/backend/services/cpu_geracao_service.py
app/backend/api/v1/endpoints/cpu_geracao.py
app/backend/tests/unit/test_cpu_bdi_breakdown.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/components/CpuTable.tsx
app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx
```
