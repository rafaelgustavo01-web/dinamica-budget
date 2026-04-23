# Technical Feedback — S-05 — QA Review
> Date: 2026-04-22
> Sprint: S-05 — Optimize Semantic Search and Operational Cost
> QA: Amazon Q
> Decision: **ACCEPTED → DONE**

---

## Entry Gate Checklist

| Item | Status |
|---|---|
| Sprint status = TESTED | ✅ |
| Walkthrough existe em `docs/walkthrough/done/walkthrough-S-05.md` | ✅ |
| Technical review existe em `docs/technical-review-2026-04-22.md` | ✅ |
| BACKLOG atualizado de `TODO` para `TESTED` | ✅ |

---

## Deliverables Verificados

| Task | Artefato | Existe | Executa sem erro | Output gerado |
|---|---|---|---|---|
| 5.1 Benchmark fuzzy vs semantic | `scripts/benchmark_search.py` | ✅ | ✅ | `logs/benchmark_search_results.csv` + `logs/benchmark_search_summary.json` |
| 5.2 Benchmark model resource | `scripts/benchmark_embeddings.py` | ✅ | ✅ | `logs/benchmark_embeddings_results.json` |
| 5.3 Evaluate PT-BR model quality | `scripts/test_model_ptbr.py` | ✅ | ✅ | `logs/model_ptbr_evaluation.json` |
| 5.4 Safe database indexes | `alembic/versions/016_add_search_indexes.py` | ✅ | ✅ (upgrade head = 016) | 3 índices criados |
| 5.5 Document findings | `docs/technical-review-2026-04-22.md` | ✅ | — | Números reais referenciados |
| 5.6 Write walkthrough | `docs/walkthrough/done/walkthrough-S-05.md` | ✅ | — | Completo |

---

## Análise de Qualidade dos Artefatos

### `scripts/benchmark_search.py`
- Usa os repositórios reais de produção (`BaseTcpoRepository`, `TcpoEmbeddingsRepository`) — correto.
- Threshold reduzido para `0.30` nos benchmarks — adequado para banco vazio (evita zero resultados por threshold alto).
- Mede latência fim a fim incluindo encode CPU na fase semântica — correto, é o custo real.
- Produz CSV + JSON summary com avg/median/p95 — suficiente para decisão de tuning.
- **Observação aceita:** banco vazio durante execução. Valida infraestrutura e custo de execução, não recall.

### `scripts/benchmark_embeddings.py`
- Usa `psutil` para medir RAM delta — correto.
- Testa batch sizes 1/8/32/64 — cobre o range operacional real.
- Resultados reais registrados:
  - Load time: **63.35s** — alto para Windows Server CPU; risco de timeout em restart de serviço.
  - RAM delta: **28.51 MB** — aceitável.
  - Single encode avg: **8.92ms** — dentro do SLA de busca.
  - Batch 64 per item: **0.88ms** — eficiente para compute-embeddings em lote.

### `scripts/test_model_ptbr.py`
- Compara `all-MiniLM-L6-v2` vs `paraphrase-multilingual-MiniLM-L12-v2` com 7 pares PT-BR + 3 distractors.
- Metodologia correta: cosine similarity normalizada, ranking por distractor.
- Resultados:

| Modelo | avg similarity | top-1 hits |
|---|---|---|
| `all-MiniLM-L6-v2` (produção) | 0.5975 | 6/7 |
| `paraphrase-multilingual-MiniLM-L12-v2` | 0.6974 | 5/7 |

- **Conclusão correta do worker:** multilíngue tem avg similarity maior mas top-1 pior. Não há evidência suficiente para troca. Recomendação de manter modelo atual é válida.
- **Falha identificada no multilíngue:** query `"demolicao parede"` rankeou distractor `"limpeza de caixa dagua"` acima do esperado (0.3495 vs 0.2917). Indica sensibilidade a tokens curtos em PT-BR.

### `alembic/versions/016_add_search_indexes.py`
- Usa `CREATE INDEX IF NOT EXISTS` — idempotente. ✅
- Alvos corretos: `referencia.base_tcpo` (não `servico_tcpo` do schema antigo). ✅
- HNSW com `m=16, ef_construction=64` — parâmetros padrão adequados para corpus inicial. ✅
- Índice composto `(cliente_id, texto_busca_normalizado)` em `operacional.associacao_inteligente` — cobre o hot path da Fase 1. ✅
- **Observação:** `downgrade()` usa `DROP INDEX IF EXISTS schema.nome` — sintaxe correta para PostgreSQL com schema qualificado. ✅

### `app/repositories/tcpo_embeddings_repository.py`
- Corrigido: SQL agora usa coluna `metadata` (não `embedding_metadata`) no SELECT raw. ✅
- ORM ainda usa `embedding_metadata` como atributo Python (renomeado para evitar conflito com SQLAlchemy). Consistente. ✅
- `import json` dentro do método `vector_search` — **code smell menor**: import deve estar no topo do arquivo. Não bloqueia.

### Grafo Alembic
- `012_dual_schema_migration.py`: `revision = "012"`, `down_revision = "011"` ✅
- `012_base_consulta_pc_orcamento.py`: `revision = "012a"`, `down_revision = "012"` ✅
- `013_expand_pc_numeric_ranges.py`: `revision = "013"`, `down_revision = "012a"` ✅
- Cadeia linear confirmada: `011 → 012 → 012a → 013 → 014 → 015 → 016` ✅
- Duplicata original (`revision = "012"` em dois arquivos) foi resolvida pelo worker. ✅

---

## Números de Benchmark — Validação

### Latência de Busca (banco vazio — valida infraestrutura)

| Fase | avg | median | p95 |
|---|---|---|---|
| Fuzzy (pg_trgm) | 6.02ms | 0.71ms | 53.70ms |
| Semântica (pgvector + encode) | 39.49ms | 32.80ms | 86.85ms |

- p95 fuzzy de 53.70ms é puxado pela primeira query (`escavacao manual em terra` = 53.7ms) — provável cold start do pg_trgm sem corpus. Median de 0.71ms é o valor representativo.
- Semântica dominada pelo encode CPU (~30ms). Confirma que o gargalo é o modelo, não o pgvector.
- **Implicação operacional:** com corpus populado, fuzzy deve ser significativamente mais rápido que semântica para queries com match exato de tokens. Semântica só deve ser acionada na Fase 3 (fallback), o que é o comportamento atual correto.

### Custo do Modelo

- Load time de **63.35s** é o risco operacional mais relevante. Em restart do serviço NSSM, a API fica degradada (embedder_ready=False) por ~1 minuto. Recomendado: documentar no runbook (S-06).

---

## Constraint Compliance

| Constraint do Briefing | Verificado |
|---|---|
| Não alterou modelo de produção | ✅ |
| Não alterou thresholds em `config.py` | ✅ |
| Branch main only | ✅ |
| Migrations usam `IF NOT EXISTS` | ✅ |
| Scripts não modificam código de produção | ✅ |

---

## Issues Identificados (não bloqueantes)

| Severidade | Arquivo | Issue | Ação |
|---|---|---|---|
| Low | `app/repositories/tcpo_embeddings_repository.py:L62` | `import json` dentro do método `vector_search` | Mover para topo do arquivo em S-02 ou próxima passagem no arquivo |
| Low | `scripts/benchmark_embeddings.py` | Benchmarka apenas o modelo de produção; não compara com multilíngue em throughput | Aceitável — comparação de qualidade está em `test_model_ptbr.py` |
| Info | Todos os benchmarks | Executados com banco vazio | Risco residual documentado no technical review. Corpus TCPO deve ser populado antes de decisão de tuning |

---

## Riscos Residuais (carry forward)

1. **Load time 63s** — risco de SLA degradado em restart. Mitigação: health check com retry no deploy script (já existe em `deploy-dinamica.bat`). Documentar no runbook S-06.
2. **Benchmark sem corpus** — números de latência fuzzy/semântica não refletem carga real. Ação: popular `referencia.base_tcpo` via ETL (`scripts/etl_popular_base_consulta.py`) e re-executar `benchmark_search.py`.
3. **Decisão de modelo pendente** — multilíngue não justifica troca hoje. Reavaliar após corpus populado com ≥1000 itens TCPO reais.

---

## Acceptance Criteria vs Delivery

| Critério do Briefing | Atendido |
|---|---|
| `benchmark_search.py` executa e produz CSV | ✅ |
| `benchmark_embeddings.py` executa e produz JSON | ✅ |
| `test_model_ptbr.py` executa e produz JSON | ✅ |
| Alembic migration aplica com `upgrade head` | ✅ |
| `docs/technical-review-2026-04-22.md` com números reais | ✅ |
| `docs/walkthrough/done/walkthrough-S-05.md` escrito | ✅ |
| BACKLOG atualizado para TESTED | ✅ |

---

## Decision

**ACCEPTED. Sprint S-05 → DONE.**

Walkthrough movido para `docs/walkthrough/reviewed/`.
