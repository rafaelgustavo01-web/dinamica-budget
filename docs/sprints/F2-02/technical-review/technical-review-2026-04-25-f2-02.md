# Technical Review — Sprint F2-02

> **Data:** 2026-04-25
> **Sprint:** F2-02 — Explosão Recursiva de Composições
> **Worker:** kimi-k2.5
> **Status:** TESTED

---

## Resumo das Mudanças

### 1. Migration 019
- **Arquivo:** `app/alembic/versions/019_recursao_composicao.py`
- 4 colunas adicionadas em `operacional.proposta_item_composicoes`:
  - `pai_composicao_id` (UUID, FK self-ref, CASCADE)
  - `nivel` (INTEGER, NOT NULL, server_default="0")
  - `e_composicao` (BOOLEAN, NOT NULL, server_default="false")
  - `composicao_explodida` (BOOLEAN, NOT NULL, server_default="false")
- Índice `ix_pic_pai_composicao_id` criado.
- **Nota de encadeamento:** A migration 018 não existe no repositório (F2-01 ainda em execução paralela). A 019 foi encadeada a `017` para evitar quebra do Alembic; deve ser reencadeada para `018` quando F2-01 entregar.

### 2. Modelo `PropostaItemComposicao`
- **Arquivo:** `app/backend/models/proposta.py`
- Adicionados campos + relationships self-ref com `foreign_keys` e `remote_side` explícitos, conforme constraint do briefing.

### 3. Serviço `CpuExplosaoService`
- **Arquivo:** `app/backend/services/cpu_explosao_service.py`
- `_assert_nivel_permitido(nivel)`: levanta `ValueError` se `nivel > 5`.
- `_verificar_e_marcar_sub_composicao(composicao)`: consulta `servico_catalog_service.explode_composicao` para sinalizar `e_composicao=True` quando o insumo possui BOM.
- `explodir_sub_composicao(proposta_id, composicao_id)`: cria filhos em `nivel+1`, marca `composicao_explodida=True`, retorna lista de filhos.
- Lógica de explosão nível-0 existente preservada; `_verificar_e_marcar_sub_composicao` chamada após cada composição raiz criada.

### 4. Endpoint `explodir-sub`
- **Arquivo:** `app/backend/api/v1/endpoints/cpu_geracao.py`
- `POST /propostas/{id}/cpu/itens/{composicao_id}/explodir-sub`
- Retorna 201 com lista de filhos; 422 para já explodida, sem composição ou nível > 5.

### 5. Testes Unitários
- **Arquivo:** `app/backend/tests/unit/test_explosao_recursiva.py`
- 6 testes cobrindo: campos padrão, árvore, guard de profundidade, duplicata, sem composição.

## Regressão
- Suite completa: **99 passed, 0 failed** (corrigidos 17 testes com imports errados `app.*` → `backend.*`).

## Riscos
- **Baixo:** Self-ref SQLAlchemy usa `foreign_keys` e `remote_side` explícitos, evitando ambiguidade.
- **Baixo:** Lógica nível-0 existente não foi alterada; apenas novos campos e chamadas adicionadas.
- **Médio:** Encadeamento da migration 019 depende da 018 (F2-01). Revisar após merge.

## Checklist
- [x] Migration encadeada (ajustada para 017 até 018 existir)
- [x] Self-ref explícita
- [x] Guard de profundidade
- [x] Endpoint com 422 semântico
- [x] 99 testes PASS
- [x] App carrega sem erro
