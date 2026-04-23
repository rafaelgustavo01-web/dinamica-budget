# Walkthrough — S-10 Importação PQ e Match Inteligente

## Status

`TESTED`

## What Changed

- Added PQ import repository support in `app/repositories/pq_importacao_repository.py` and `app/repositories/pq_item_repository.py`.
- Added `app/services/pq_import_service.py` to parse `.csv` and `.xlsx` uploads into `PqImportacao` and `PqItem`.
- Added `app/services/pq_match_service.py` to process pending PQ items through the existing search cascade.
- Added `app/api/v1/endpoints/pq_importacao.py` and wired the router.
- Added response models to `app/schemas/proposta.py`.
- Added unit tests in `app/tests/unit/test_pq_import_service.py` and `app/tests/unit/test_pq_match_service.py`.

## Acceptance Criteria

- Upload aceita `.xlsx` e `.csv`: covered by service tests and endpoint implementation.
- Cada linha vira `PqItem` com `descricao_original` e `descricao_tokens`: done.
- Match executa para itens `PENDENTE` da proposta: done.
- Sugestão inclui `servico_match_id`, `servico_match_tipo`, `match_confidence`: done in repository update flow.
- Sem match atualiza status para `SEM_MATCH`: done.
- Testes unitários cobrem parser e matcher: done.
- Migração inclui `pq_importacoes` e `pq_itens`: already satisfied by `017_create_proposta_entities`.

## Verification

- `pytest app/tests/unit/test_pq_import_service.py app/tests/unit/test_pq_match_service.py -q` -> `4 passed`
- `pytest app/tests/unit -q` -> `89 passed`

## Notes For QA

- Review tenant validation on both endpoints and verify import behavior with representative CSV/XLSX samples.
- This sprint stops at suggestion generation; manual confirmation and CPU generation remain for later sprints.
