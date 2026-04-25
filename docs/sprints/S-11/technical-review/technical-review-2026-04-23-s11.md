# Technical Review — S-11 Geração da CPU

## Status

`TESTED`

## Scope

- Added `PropostaItemRepository` and `PropostaItemComposicaoRepository`.
- Added `CpuExplosaoService`, `CpuCustoService`, and `CpuGeracaoService`.
- Added CPU endpoints in `app/api/v1/endpoints/cpu_geracao.py` and wired the API router.
- Added CPU response schemas in `app/schemas/proposta.py`.
- Added unit coverage in `app/backend/tests/unit/test_cpu_geracao_service.py`.

## Findings

- The updated plan was closer to the repo state, but the implementation still needed to adapt to the actual schema:
  - `TipoRecurso` and `PropostaItemComposicao` already existed and were reused.
  - `servico_catalog_service.explode_composicao()` was reused instead of reimplementing DFS.
  - `PcTabelas` does not expose `base_id` or `custo_hora`; the implementation uses the real fields `PcMaoObraItem.custo_unitario_h` and `PcEquipamentoItem.(aluguel_r_h + combustivel_r_h + mao_obra_r_h)` with lookup scoped by `pc_cabecalho_id`.
- CPU generation rebuilds `PropostaItem` from matched `PqItem` before exploding and pricing them, which fits the current sprint sequence.
- Leaf services without exploded BOM still generate a snapshot composition line so direct-cost calculation does not disappear.

## Verification

- `pytest app/backend/tests/unit/test_cpu_geracao_service.py -q` -> `2 passed`
- `pytest app/backend/tests/unit -q` -> `91 passed`
- `python -m compileall app/repositories/proposta_item_repository.py app/repositories/proposta_item_composicao_repository.py app/services/cpu_explosao_service.py app/services/cpu_custo_service.py app/services/cpu_geracao_service.py app/api/v1/endpoints/cpu_geracao.py app/schemas/proposta.py app/backend/tests/unit/test_cpu_geracao_service.py`

## Residual Risk

- The current CPU flow accepts `PqItem` in `SUGERIDO`, `CONFIRMADO`, or `MANUAL` because the explicit confirmation endpoint is not part of this sprint.
- PcTabelas lookup is description-based because the current schema has no direct FK between catalog items and cost-table rows.
- No new Alembic migration was required because `proposta_item_composicoes` already exists in revision `017`.

