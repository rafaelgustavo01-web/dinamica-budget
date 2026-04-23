# Walkthrough — S-11 Geração da CPU

## Status

`TESTED`

## What Changed

- Added CPU persistence repositories:
  - `app/repositories/proposta_item_repository.py`
  - `app/repositories/proposta_item_composicao_repository.py`
- Added CPU services:
  - `app/services/cpu_explosao_service.py`
  - `app/services/cpu_custo_service.py`
  - `app/services/cpu_geracao_service.py`
- Added endpoints:
  - `POST /propostas/{proposta_id}/cpu/gerar`
  - `GET /propostas/{proposta_id}/cpu/itens`
- Added response schemas in `app/schemas/proposta.py`.
- Added unit tests in `app/tests/unit/test_cpu_geracao_service.py`.

## Acceptance Criteria

- Todos os `PropostaItem` elegíveis são processados: done via rebuild from matched `PqItem`.
- Explosão reusa composição existente: done via `servico_catalog_service.explode_composicao()`.
- Custo unitário usa PcTabelas quando disponível e fallback quando não: done.
- BDI aplicado sobre custo direto: done.
- `preco_total = preco_unitario * quantidade`: done.
- Rastreabilidade com `fonte_custo` e `composicao_fonte`: done.
- Testes unitários cobrem cenários com e sem composição: done.
- Migração Alembic para `proposta_item_composicoes`: already satisfied by `017_create_proposta_entities`.

## Verification

- `pytest app/tests/unit/test_cpu_geracao_service.py -q` -> `2 passed`
- `pytest app/tests/unit -q` -> `91 passed`

## Notes For QA

- Focus review on CPU rebuild from matched PQ items, BDI application, and fallback behavior when PcTabelas does not have a matching row.
- The explicit manual confirmation endpoint for PQ match selection is still outside this sprint, so the CPU builder accepts items already tagged with a selected match.
