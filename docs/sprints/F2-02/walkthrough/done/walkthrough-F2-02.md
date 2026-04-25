# Walkthrough — Sprint F2-02

> **Data:** 2026-04-25
> **Sprint:** F2-02 — Explosão Recursiva de Composições
> **Worker:** kimi-k2.5

---

## O que foi entregue

Permitir que composições de proposta explodam em sub-níveis (composição dentro de composição), registrando a árvore completa de insumos com rastreabilidade de nível e origem.

## Arquivos alterados/criados

1. `app/alembic/versions/019_recursao_composicao.py` — Migration com 4 colunas e FK self-ref.
2. `app/backend/models/proposta.py` — 4 colunas + relationships `sub_composicoes`/`pai`.
3. `app/backend/services/cpu_explosao_service.py` — Guard de profundidade, marcação de sub-composição, método `explodir_sub_composicao`.
4. `app/backend/api/v1/endpoints/cpu_geracao.py` — Endpoint `POST .../explodir-sub`.
5. `app/backend/tests/unit/test_explosao_recursiva.py` — 6 testes unitários.
6. Correções em testes existentes (imports `app.*` → `backend.*`):
   - `test_busca_service.py`
   - `test_cpu_geracao_service.py`
   - `test_composicao_clone_new.py`
   - `test_security_p0.py`
   - `test_security_s04.py`
   - `test_transactional_purity.py`

## Como validar

```bash
cd app
# Testes da sprint
python -m pytest backend/tests/unit/test_explosao_recursiva.py -v
# Regressão completa
python -m pytest backend/tests/unit/ -v
```

Resultado esperado: 99 passed, 0 failed.

## Decisões de implementação

- `ComposicaoBaseRepository` não existe no codebase. Substituído por `servico_catalog_service.explode_composicao` para obter a BOM do insumo.
- `_verificar_e_marcar_sub_composicao` usa `explode_composicao` e verifica se `resultado.itens` é não-vazio.
- Migration 019 encadeada em 017 porque 018 (F2-01) ainda não existe. Será reencadeada quando F2-01 entregar.

## Handoff para QA

- Walkthrough: `docs/sprints/F2-02/walkthrough/done/walkthrough-F2-02.md`
- Technical Review: `docs/sprints/F2-02/technical-review/technical-review-2026-04-25-f2-02.md`
- Tests: 99 PASS / 0 FAIL
