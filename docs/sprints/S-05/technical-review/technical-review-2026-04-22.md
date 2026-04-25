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
- `app/alembic/versions/016_add_search_indexes.py`
- `app/alembic/versions/012_base_consulta_pc_orcamento.py`
- `app/alembic/versions/013_expand_pc_numeric_ranges.py`
- `app/repositories/tcpo_embeddings_repository.py`
- `logs/benchmark_embeddings_results.json`
- `logs/benchmark_search_results.csv`
- `logs/benchmark_search_summary.json`
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
  - Result: sucesso após corrigir `DATABASE_URL`, linearizar o grafo do Alembic (`012` duplicado) e alinhar FKs legados da branch PC/Orçamento ao dual-schema
- `python scripts/benchmark_search.py`
  - Result: sucesso com:
    - fuzzy avg: `6.02ms`
    - fuzzy median: `0.71ms`
    - fuzzy p95: `53.70ms`
    - semantic avg: `39.49ms`
    - semantic median: `32.80ms`
    - semantic p95: `86.85ms`
  - Observação: o banco local está vazio, então ambos os caminhos retornaram `0` resultados em todas as queries; os números acima validam infraestrutura, índices e custo de execução, não qualidade em corpus populado.

## Database Fix Summary
- O bloqueio original era uma combinação de problemas locais:
  - `DATABASE_URL` incompatível com o caminho sync do `psycopg2` no Windows
  - senha local do PostgreSQL divergente do `.env`
  - duas migrations com `revision = "012"` causando múltiplos heads no Alembic
  - migration de PC/Orçamento ainda apontando para `servico_tcpo`/`clientes` antigos
  - query semântica SQL usando `embedding_metadata` enquanto o schema real expõe a coluna `metadata`
- Após correção, o banco local subiu até `alembic_version = 016` e os índices de S-05 foram confirmados em:
  - `referencia.idx_base_tcpo_descricao_trgm`
  - `referencia.idx_tcpo_embeddings_vetor_hnsw`
  - `operacional.idx_associacao_cliente_texto`

## Recommendation
- Keep the production model unchanged during S-05 and use the generated model artifacts to decide follow-up tuning.
- The multilingual candidate shows higher average similarity (`0.6974` vs `0.5975`), but worse top-1 hit rate (`5/7` vs `6/7`), so there is not yet strong evidence for a production switch.
- Populate `referencia.base_tcpo` and `referencia.tcpo_embeddings` before using the current search benchmark numbers for tuning decisions.

## Residual Risk
- The sprint still lacks corpus-populated latency evidence; the validated benchmark was executed against an empty database.
- HNSW index creation depends on the installed `pgvector` capabilities of the target PostgreSQL environment; if unavailable, the migration strategy may need an ivfflat fallback in a follow-up sprint.
- The PC/Orçamento migration branch required repair to coexist with the dual-schema chain; future migrations must keep a single linear Alembic graph.

