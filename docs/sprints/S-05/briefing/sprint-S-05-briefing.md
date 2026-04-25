# Sprint Briefing - S-05 - Optimize Semantic Search and Operational Cost

> Date: 2026-04-22
> Prepared by: Supervisor (Kimi Code CLI)
> Assigned role: Worker
> Assigned worker: codex-5.3
> Execution mode: BUILD
> Plan: `docs/sprints/S-05/plans/2026-04-22-optimize-search-and-operational-cost.md`

## Mission

The Dinamica Budget search engine runs a 4-phase cascade (PROPRIA → Association → Fuzzy → Semantic) on a Windows Server on-premise with CPU-only inference. Today we have no quantitative evidence of:

1. Whether fuzzy or semantic search is faster or more accurate for Portuguese TCPO descriptions.
2. How much RAM and CPU the `all-MiniLM-L6-v2` embedding model consumes on the target hardware.
3. Whether a multilingual model would improve PT-BR search quality enough to justify a migration.
4. Whether missing database indexes are degrading search latency.

**Critical constraint:** This project uses only the `main` branch. There are no feature branches. Any production-impacting change must be a safe, backward-compatible Alembic migration (adding indexes) or an isolated script. We must NOT switch the embedding model in production during this sprint — only evaluate and recommend.

## Delegation Envelope

- Sprint status on entry: `TODO`
- Worker status target on exit: `TESTED`
- Assigned worker: codex-5.3
- Provider: OpenAI
- Auth status snapshot: PASS
- Quota status snapshot: PASS
- Execution mode: BUILD

## Current Code State

### `app/ml/embedder.py`
- Line 11-60: Loads `all-MiniLM-L6-v2` via SentenceTransformers at FastAPI startup.
- Risk note: Model load blocks lifespan startup for 2-5 seconds. On Windows Server CPU, this is acceptable but not measured.

### `app/repositories/tcpo_embeddings_repository.py`
- Line 44-74: `vector_search` uses `1 - (vetor <=> CAST(... AS vector))` cosine similarity against `referencia.tcpo_embeddings`.
- Risk note: Assumes HNSW index exists. If missing, query does a sequential scan over all vectors.

### `app/repositories/servico_tcpo_repository.py`
- Line 78-134: `fuzzy_search_scoped` uses `similarity(s.descricao, :query)` with `pg_trgm`.
- Risk note: No GIN index on `descricao` means full table scan for every fuzzy query.

### `app/services/busca_service.py`
- Line 45-157: Orchestrates the 4-phase cascade. Phase 3 semantic search calls `embedder.encode()` while holding an open `AsyncSession`.
- Risk note: Session is held during CPU-bound encoding, tying up a DB pool connection.

### `app/models/associacao_inteligente.py`
- Line 33-38: `(cliente_id, texto_busca_normalizado)` has individual indexes but no composite index.
- Risk note: Phase 1 association lookup may perform two index scans instead of one.

## Required Changes

### Task 5.1 — Benchmark Fuzzy vs Semantic Latency
- File: `scripts/benchmark_search.py` (create)
- Change: Create standalone script that runs 10 PT-BR queries through fuzzy and semantic search, recording latency and result counts.
- Constraints: Must not modify production code. Must run against local dev database.

### Task 5.2 — Benchmark Model Resource Cost
- File: `scripts/benchmark_embeddings.py` (create)
- Change: Measure model load time, peak RAM (via psutil), single-text encoding latency, and batch throughput.
- Constraints: Must not modify production code. Requires `psutil` install.

### Task 5.3 — Evaluate PT-BR Model Quality
- File: `scripts/test_model_ptbr.py` (create)
- Change: Compare `all-MiniLM-L6-v2` vs `paraphrase-multilingual-MiniLM-L12-v2` on a small labeled set of PT-BR query/description pairs.
- Constraints: Must not modify production model or config. Output is JSON report only.

### Task 5.4 — Add Safe Database Indexes
- File: `app/alembic/versions/2026_04_22_add_search_indexes.py` (create)
- Change: Alembic migration adding:
  - `idx_servico_tcpo_descricao_trgm` (GIN, pg_trgm)
  - `idx_tcpo_embeddings_vetor_hnsw` (HNSW, pgvector)
  - `idx_associacao_cliente_texto` (composite B-tree)
- Constraints: Backward-compatible. Adding indexes does not break reads/writes. Must use `CREATE INDEX IF NOT EXISTS`.

### Task 5.5 — Document Findings
- File: `docs/sprints/S-05/technical-review/technical-review-2026-04-22.md` (create/update)
- Change: Consolidate all benchmark outputs into a single technical review with recommendations for the Product Owner.
- Constraints: Must reference actual numbers produced by Tasks 5.1-5.3.

### Task 5.6 — Write Walkthrough
- File: `docs/sprints/S-05/walkthrough/done/walkthrough-S-05.md` (create)
- Change: Evidence that the sprint was executed and all artifacts were produced.
- Constraints: Must be completed before moving sprint to `TESTED`.

## Mandatory Tests

- `scripts/benchmark_search.py` runs without errors and produces `logs/benchmark_search_results.csv`
- `scripts/benchmark_embeddings.py` runs without errors and produces `logs/benchmark_embeddings_results.json`
- `scripts/test_model_ptbr.py` runs without errors and produces `logs/model_ptbr_evaluation.json`
- Alembic migration applies cleanly with `alembic upgrade head`
- Fuzzy benchmark latency improves measurably after index creation
- Validation commands:
```bash
python scripts/benchmark_search.py
python scripts/benchmark_embeddings.py
python scripts/test_model_ptbr.py
alembic upgrade head
```

## Required Artifacts Before Status `TESTED`

- `docs/sprints/S-05/technical-review/technical-review-2026-04-22.md` updated with real numbers
- `docs/sprints/S-05/walkthrough/done/walkthrough-S-05.md` written
- `docs/BACKLOG.md` updated from `TODO` to `TESTED`

## Critical Warnings

1. **Branch main only.** Do not create feature branches. Any code change must be safe to merge directly into `main`.
2. Do NOT switch the production embedding model. Only evaluate and recommend.
3. Do NOT change `app/core/config.py` thresholds permanently. Measure current values and recommend new ones in the technical review.
4. The Alembic migration must use `IF NOT EXISTS` to be idempotent and safe for rerun.
5. If the Windows Server does not have `psutil`, install it locally for the benchmark script only.
6. If blocked, record the blocker in the walkthrough and leave the status unchanged.



