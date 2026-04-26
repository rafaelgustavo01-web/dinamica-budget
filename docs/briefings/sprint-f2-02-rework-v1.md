# Briefing de Rework — Sprint F2-02 — v1

> **Data:** 2026-04-25
> **Sprint:** F2-02 — Explosão Recursiva de Composições
> **Original Briefing:** `docs/sprints/F2-02/briefing/sprint-F2-02-briefing.md`
> **Status:** REWORK

---

## Itens de Ajuste Obrigatórios

### 1. Fim da Explosão Achatada (Flattening)
O `CpuExplosaoService` deve parar de usar `servico_catalog_service.explode_composicao` para criar itens de composição, pois este método retorna a árvore inteira de forma flat.
- **Ação:** Criar um método no repositório adequado (ou usar query direta) para obter apenas os **componentes diretos** de um serviço (nível 1).
- **Impacto:** O nível 0 (`explodir_proposta_item`) deve criar apenas os filhos diretos do item da proposta. As sub-explosões criarão os níveis subsequentes sob demanda.

### 2. Integridade de Dados em Sub-níveis
As sub-composições criadas via `explodir_sub_composicao` devem possuir os mesmos metadados que as de nível 0.
- **Ação:** Resolver o snapshot do insumo (Base ou Próprio) antes de criar o objeto `PropostaItemComposicao`.
- **Campos obrigatórios:** `tipo_recurso`, `custo_unitario_insumo`, `unidade_medida`, `descricao_insumo`.

### 3. Polimorfismo de Insumo (Base/Próprio)
Garantir que sub-composições que apontam para `ItemProprio` também possam ser explodidas.
- **Ação:** No método `explodir_sub_composicao`, verificar se o alvo é `insumo_base_id` ou `insumo_proprio_id` e buscar os filhos correspondentes na tabela correta (`composicao_base` ou `composicao_cliente` via versão ativa).

### 4. Testes de Regressão de Árvore
Adicionar um teste unitário que valide:
1. Nível 0 cria apenas N itens (onde N é o número de filhos diretos).
2. Chamada de `explodir-sub` em um desses itens cria M itens (onde M é o número de filhos diretos desse sub-item).
3. Verificação de que não há duplicidade de registros (ex: o neto não aparece como filho direto no nível 0).

---

## Handoff

O Worker deve aplicar estes ajustes e submeter um novo walkthrough.
