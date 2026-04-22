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
- `alembic/versions/016_add_search_indexes.py`: migration segura para índices nos objetos realmente usados hoje.
- `docs/technical-review-2026-04-22.md`: revisão técnica consolidando resultados, impactos e recomendação.
- `logs/benchmark_search_results.csv`: resultados brutos do benchmark de busca.
- `logs/benchmark_search_summary.json`: resumo agregado da latência fuzzy vs semantic.
- `logs/benchmark_embeddings_results.json`: custo operacional do modelo atual.
- `logs/model_ptbr_evaluation.json`: comparação de qualidade entre modelos.

## Validation

```bash
python scripts/benchmark_search.py
python scripts/benchmark_embeddings.py
python scripts/test_model_ptbr.py
alembic upgrade head
```

- Result: executado e registrado nos artefatos acima.
- Notes: a migration foi adaptada ao código real do repositório, porque a busca fuzzy atual usa `referencia.base_tcpo` e não `servico_tcpo`.

## Key Decisions

- O sprint não alterou o modelo de embeddings em produção.
- A migration corrige o alvo do índice trigram para o schema/tabela realmente usados pela busca atual.
- O benchmark semantic mede o custo fim a fim, incluindo encode em CPU, que é o principal impacto operacional no servidor Windows.

## Blockers or Risks

- Nenhum blocker impeditivo durante a conclusão do ciclo.
- A recomendação final de troca de modelo continua dependente dos números registrados no review técnico e não implica mudança automática de produção.

## Status Update

Os artefatos de worker foram produzidos e o sprint pode sair de `TODO` para `TESTED`.
