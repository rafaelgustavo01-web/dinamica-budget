# Walkthrough — Sprint F2-02 (Rework v1)

> **Data:** 2026-04-26
> **Sprint:** F2-02 — Explosão Recursiva de Composições (Rework v1)
> **Worker:** kimi-k2.5

---

## O que foi entregue (Rework)

Refatoração da explosão recursiva para construir uma árvore real sem duplicidade e com metadados completos.

## Correções aplicadas

1. **Fim do achatamento (flattening)** — `CpuExplosaoService` agora usa `_listar_filhos_diretos` que consulta apenas `referencia.composicao_base` (filhos diretos do TCPO) ou `operacional.composicao_cliente` via versão ativa (filhos diretos do ItemProprio). Não usa mais `servico_catalog_service.explode_composicao` que retornava DFS achatada.
2. **Integridade de dados** — Sub-composições criadas via `_build_composicao` que resolve snapshot (BaseTcpo ou ItemProprio) e popula `tipo_recurso`, `custo_unitario_insumo`, `unidade_medida`, `descricao_insumo`.
3. **Polimorfismo** — `_listar_filhos_diretos` e `_resolve_snapshot` suportam ambos os tipos. `explodir_sub_composicao` verifica `insumo_base_id` ou `insumo_proprio_id`.
4. **Testes de árvore** — 3 novos testes validam:
   - Nível 0 cria apenas filhos diretos
   - Sub-explosão cria netos sem duplicar
   - Suporte a ItemProprio na sub-explosão

## Arquivos alterados

- `app/backend/services/cpu_explosao_service.py` — reescrito com `_listar_filhos_diretos`, refatorados `explodir_proposta_item`, `explodir_sub_composicao`, `_build_composicao`.
- `app/backend/tests/unit/test_explosao_recursiva.py` — 3 testes novos de árvore.
- `app/backend/services/cpu_geracao_service.py` — import fix `PropostaItemComposicao`.

## Como validar

```bash
cd app
python -m pytest backend/tests/unit/test_explosao_recursiva.py -v
# Esperado: 9 passed

python -m pytest backend/tests/ -q
# Esperado: 118 passed, 0 failed
```

## Handoff para QA

- Walkthrough: `docs/sprints/F2-02/walkthrough/done/walkthrough-F2-02.md`
- Technical Review: `docs/sprints/F2-02/technical-review/technical-review-2026-04-25-f2-02.md`
- Rework briefing: `docs/briefings/sprint-f2-02-rework-v1.md`
- Tests: 118 PASS / 0 FAIL
