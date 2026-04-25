# Walkthrough - S-05: Optimize Semantic Search and Operational Cost

> **Date:** 2026-04-22
> **Sprint:** S-05
> **Status:** TESTED
> **Worker:** codex

---

## Objective

Produzir evidência operacional para a busca do Dinamica Budget em ambiente on-premise Windows: comparar fuzzy vs semantic, medir custo do modelo atual, avaliar um candidato multilíngue e adicionar índices seguros para o caminho real de consulta.

## Delivered Artifacts

- `scripts/benchmark_search.py`: benchmark da busca fuzzy vs semantic usando os repositórios atuais.
- `scripts/benchmark_embeddings.py`: benchmark de carga, RAM e throughput do modelo atual.
- `scripts/test_model_ptbr.py`: comparação do modelo atual com um candidato multilíngue em exemplos PT-BR.
- `app/alembic/versions/016_add_search_indexes.py`: migration segura para índices nos objetos realmente usados hoje.
- `app/alembic/versions/012_base_consulta_pc_orcamento.py`: trilha de PC/Orçamento ajustada para coexistir com o dual-schema.
- `app/alembic/versions/013_expand_pc_numeric_ranges.py`: `down_revision` alinhado à nova sequência linear.
- `app/repositories/tcpo_embeddings_repository.py`: SQL semântico alinhado à coluna real `metadata`.
- `docs/sprints/S-05/technical-review/technical-review-2026-04-22.md`: revisão técnica consolidando resultados, impactos e recomendação.
- `logs/benchmark_embeddings_results.json`: custo operacional do modelo atual.
- `logs/benchmark_search_results.csv`: medições fuzzy vs semantic.
- `logs/benchmark_search_summary.json`: resumo agregado do benchmark de busca.
- `logs/model_ptbr_evaluation.json`: comparação de qualidade entre modelos.

## Validation

```bash
python scripts/benchmark_search.py
python scripts/benchmark_embeddings.py
python scripts/test_model_ptbr.py
alembic upgrade head
```

- Result:
  - `benchmark_embeddings.py`: sucesso
  - `test_model_ptbr.py`: sucesso
  - `benchmark_search.py`: sucesso
  - `alembic upgrade head`: sucesso até `016`
- Notes: a migration foi adaptada ao código real do repositório, porque a busca fuzzy atual usa `referencia.base_tcpo` e não `servico_tcpo`.
- Notes: o benchmark de busca rodou em banco vazio; validou conectividade, grafo de migrations, consultas e índices, mas não mede recall/relevância com corpus carregado.

## Key Decisions

- O sprint não alterou o modelo de embeddings em produção.
- A migration corrige o alvo do índice trigram para o schema/tabela realmente usados pela busca atual.
- O benchmark semantic mede o custo fim a fim, incluindo encode em CPU, que é o principal impacto operacional no servidor Windows.
- A cadeia do Alembic foi linearizada para eliminar o `revision = "012"` duplicado e permitir bootstrap limpo do banco.

## Blockers or Risks

- O benchmark de busca atual foi executado com `0` registros em `referencia.base_tcpo` e `referencia.tcpo_embeddings`.
- A recomendação final de troca de modelo continua dependente dos números registrados no review técnico e não implica mudança automática de produção.

## Status Update

Os artefatos de worker foram produzidos e a validação técnica de banco foi concluída. O sprint pode ficar em `TESTED`; o próximo passo natural é popular a base TCPO local para obter benchmark representativo de corpus real antes de qualquer decisão adicional de tuning.


