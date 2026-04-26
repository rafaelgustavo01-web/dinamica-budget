# Walkthrough — Sprint F2-04

> **Data:** 2026-04-25
> **Sprint:** F2-04 — CPU Detalhada + BDI Dinâmico
> **Worker:** kimi-k2.5

---

## O que foi entregue

Exposição do breakdown completo de insumos por item da CPU via API e frontend, com recálculo dinâmico de BDI sem regerar toda a CPU.

## Arquivos alterados/criados

1. `app/backend/schemas/proposta.py` — 3 novos schemas.
2. `app/backend/repositories/proposta_item_composicao_repository.py` — ordenação por nivel.
3. `app/backend/services/cpu_geracao_service.py` — `recalcular_bdi` + `listar_composicoes_item`.
4. `app/backend/api/v1/endpoints/cpu_geracao.py` — 2 novos endpoints.
5. `app/backend/tests/unit/test_cpu_bdi_breakdown.py` — 8 testes unitários.
6. `app/frontend/src/shared/services/api/proposalsApi.ts` — tipos e métodos CPU.
7. `app/frontend/src/features/proposals/components/CpuTable.tsx` — accordion de insumos.
8. `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` — página desbloqueada.

## Como validar

```bash
# Backend
cd app
python -m pytest backend/tests/unit/ -q
# Esperado: 114 passed

python -m pytest backend/tests/ -q
# Esperado: 115 passed, 0 failed

# Frontend
cd app/frontend
npx tsc --noEmit
# Esperado: 0 erros
```

## Decisões de implementação

- `percentual_indireto` já existia em `PropostaItem`; reutilizado para persistir BDI.
- `CpuItemDetalhado` usa strings para campos numéricos para compatibilidade com JSON Decimal do backend.
- Accordion de insumos carrega lazy via `useQuery` ao expandir (cache por `queryKey`).
