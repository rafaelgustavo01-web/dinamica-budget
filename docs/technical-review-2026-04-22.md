# Technical Review - 2026-04-22

## Sprint
- `S-05` - Optimize semantic search and operational cost

## Scope Reviewed
- Benchmark fuzzy search vs semantic search on the current repository code paths.
- Measure load time, RAM impact, and encoding throughput of the production embedding model.
- Compare the production model with a multilingual candidate on PT-BR examples.
- Add safe database indexes for the actual search tables used by the current implementation.

## Findings
- The current fuzzy path runs against `referencia.base_tcpo`, not `servico_tcpo`. The older trigram migration (`004`) targets `servico_tcpo`, so it does not accelerate the query that `BaseTcpoRepository.fuzzy_search()` executes today.
- The semantic path is dominated by CPU encoding time on Windows/on-prem, because the request path performs `embedder.encode()` before `TcpoEmbeddingsRepository.vector_search()`.
- `AssociacaoInteligente` has individual indexes on foreign keys, but the hot lookup path still benefits from a composite `(cliente_id, texto_busca_normalizado)` index.
- S-05 therefore needs evidence and safe infra changes, not a production model switch.

## Deliverables Produced
- `scripts/benchmark_search.py`
- `scripts/benchmark_embeddings.py`
- `scripts/test_model_ptbr.py`
- `alembic/versions/016_add_search_indexes.py`
- `logs/benchmark_search_results.csv`
- `logs/benchmark_search_summary.json`
- `logs/benchmark_embeddings_results.json`
- `logs/model_ptbr_evaluation.json`

## Validation Evidence
- `python scripts/benchmark_search.py`
  - Result: generates CSV + JSON summary in `logs/`
- `python scripts/benchmark_embeddings.py`
  - Result: generates model cost report in `logs/benchmark_embeddings_results.json`
- `python scripts/test_model_ptbr.py`
  - Result: generates PT-BR comparison report in `logs/model_ptbr_evaluation.json`
- `alembic upgrade head`
  - Result: applies migration `016_add_search_indexes.py`

## Recommendation
- Keep the production model unchanged during S-05 and use the generated benchmark artifacts to decide follow-up tuning.
- Apply the new search indexes first, because they are backward-compatible and directly reduce risk in the current query paths.
- Only consider a multilingual model migration in a future sprint after reviewing the recorded PT-BR comparison data and planning a full re-embedding window.

## Residual Risk
- The real latency numbers depend on the local Windows Server hardware and database volume, so the generated logs remain the source of truth for the final PO decision.
- HNSW index creation depends on the installed `pgvector` capabilities of the target PostgreSQL environment; if unavailable, the migration strategy may need an ivfflat fallback in a follow-up sprint.
