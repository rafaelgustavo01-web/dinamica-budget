# Sprint F2-02 Briefing

> **Role:** Supervisor / SM
> **Date:** 2026-04-25
> **Sprint:** F2-02 - Explosao Recursiva de Composicoes

## Objetivo

Permitir que composicoes de proposta explodam em sub-niveis (composicao dentro de composicao), registrando a arvore completa de insumos com rastreabilidade de nivel e origem.

## Escopo

1. **Migration `019_recursao_composicao.py`** — 4 colunas em `operacional.proposta_item_composicoes`:
   - `pai_composicao_id UUID` (FK self-ref, CASCADE)
   - `nivel INTEGER NOT NULL DEFAULT 0`
   - `e_composicao BOOLEAN NOT NULL DEFAULT false`
   - `composicao_explodida BOOLEAN NOT NULL DEFAULT false`

2. **Modelo `PropostaItemComposicao`:** 4 colunas + relationships `sub_composicoes`/`pai` com `foreign_keys` explicito.

3. **`cpu_explosao_service.py`:**
   - `_assert_nivel_permitido(nivel)` — ValueError se nivel > 5.
   - `_verificar_e_marcar_sub_composicao(composicao)` — seta `e_composicao=True` quando insumo tem `composicao_base`.
   - `explodir_sub_composicao(proposta_id, composicao_id)` — valida, cria filhos em `nivel+1`, marca `composicao_explodida=True`.
   - Na explosao nivel-0 existente: passar `pai_composicao_id=None, nivel=0` e chamar `_verificar_e_marcar_sub_composicao`.

4. **Endpoint:** `POST /propostas/{id}/cpu/itens/{composicao_id}/explodir-sub` — 201 com filhos; 422 se ja explodida, sem composicao, ou nivel > 5.

5. **Testes:** 6 unitarios (campos padrao, arvore, guard, duplicata, sem composicao).

## Criterios de Aceite

- `POST explodir-sub` retorna 201 com lista de filhos.
- Filho criado tem `nivel = pai.nivel + 1` e `pai_composicao_id = pai.id`.
- Nivel 6 retorna 422 com "Profundidade maxima".
- Composicao ja explodida retorna 422.
- Suite de regressao: 93+ PASS, 0 FAIL.

## Dependencias

- S-11 (Geracao CPU) DONE
- F2-01 pode rodar em paralelo (sem dependencia direta)
- Migration 019 encadeia apos 018

## Worker Assignment

- **Worker ID:** kimi-k2.5
- **Provider:** Kimi CLI
- **Mode:** BUILD

## Plano

Ver: `docs/sprints/F2-02/plans/2026-04-25-explosao-recursiva.md`

## Restricoes

- Somente branch `main`.
- Nao quebrar logica de explosao nivel-0 existente — apenas adicionar campos e chamadas.
- Self-reference SQLAlchemy: `foreign_keys` e `remote_side` explicitos obrigatorios.
