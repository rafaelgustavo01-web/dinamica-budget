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
- `logs/benchmark_embeddings_results.json`
- `logs/model_ptbr_evaluation.json`

## Validation Evidence
- `python scripts/benchmark_embeddings.py`
  - Result: `logs/benchmark_embeddings_results.json` gerado com:
    - load time: `63.35s`
    - RAM delta: `28.51 MB`
    - single encode avg: `8.92ms`
    - batch 64 per item: `0.88ms`
- `python scripts/test_model_ptbr.py`
  - Result: `logs/model_ptbr_evaluation.json` gerado com:
    - `all-MiniLM-L6-v2`: avg similarity `0.5975`, top-1 `6/7`
    - `paraphrase-multilingual-MiniLM-L12-v2`: avg similarity `0.6974`, top-1 `5/7`
- `alembic upgrade head`
  - Result: falhou por `UnicodeDecodeError` no driver `psycopg2` local ao conectar no PostgreSQL
- `python scripts/benchmark_search.py`
  - Result: falhou por `asyncpg.exceptions.ConnectionDoesNotExistError` com reset da conexão local durante a operação

## Blocker
- O ambiente local de banco está instável/incompatível em dois caminhos distintos:
  - `psycopg2`: falha de decode já na conexão sync usada pelo Alembic
  - `asyncpg`: conexão encerrada pelo host durante o benchmark de busca
- Isso impede validar a migration `016` e medir a latência fuzzy/semantic contra o banco real nesta máquina.

## Recommendation
- Keep the production model unchanged during S-05 and use the generated model artifacts to decide follow-up tuning.
- The multilingual candidate shows higher average similarity (`0.6974` vs `0.5975`), but worse top-1 hit rate (`5/7` vs `6/7`), so there is not yet strong evidence for a production switch.
- Apply the new search indexes only after the local PostgreSQL connectivity issue is resolved and the migration can be executed safely.

## Residual Risk
- The sprint still lacks the real fuzzy vs semantic latency evidence because the database benchmark could not complete.
- HNSW index creation depends on the installed `pgvector` capabilities of the target PostgreSQL environment; if unavailable, the migration strategy may need an ivfflat fallback in a follow-up sprint.
- Until the local DB connectivity issue is fixed, S-05 should not be promoted from `TODO` to `TESTED`.
