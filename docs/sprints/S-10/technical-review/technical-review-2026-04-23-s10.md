# Technical Review — S-10 Importação PQ e Match Inteligente

## Status

`TESTED`

## Scope

- Added `PqImportacaoRepository` and expanded `PqItemRepository` for batch creation and match state updates.
- Added `PqImportService` for `.csv` and `.xlsx` ingestion with header alias detection, quantity parsing, and normalized `descricao_tokens`.
- Added `PqMatchService` reusing `BuscaService.buscar()` for PQ item suggestion flow.
- Added `/propostas/{proposta_id}/pq/importar` and `/propostas/{proposta_id}/pq/match` endpoints with `require_cliente_access`.
- Added unit coverage for import and match services.

## Findings

- The repository already had `openpyxl` patterns, so the import flow was implemented with native CSV + `openpyxl` parsing instead of introducing `pandas` into the runtime path.
- `S-10` did not require a new Alembic revision because `pq_importacoes` and `pq_itens` were already introduced in migration `017` during `S-09`.
- Match origin mapping is now explicit:
  - `PROPRIA_CLIENTE` -> `ITEM_PROPRIO`
  - all current global search paths -> `BASE_TCPO`

## Verification

- `pytest app/backend/tests/unit/test_pq_import_service.py app/backend/tests/unit/test_pq_match_service.py -q` -> `4 passed`
- `pytest app/backend/tests/unit -q` -> `89 passed`
- `python -m compileall app/services/pq_import_service.py app/services/pq_match_service.py app/api/v1/endpoints/pq_importacao.py app/repositories/pq_importacao_repository.py app/repositories/pq_item_repository.py app/schemas/proposta.py`

## Residual Risk

- The current import parser recognizes flexible aliases, but not arbitrary spreadsheet layouts; very custom headers may still require future mapping UI in a later sprint.
- Match execution is bounded to 1000 pending items per call, which is safe for this sprint but may need chunking/background execution in higher-volume proposals.

