# Technical Feedback — Sprint F2-02 — v1

> **Data:** 2026-04-25
> **Sprint:** F2-02 — Explosão Recursiva de Composições
> **QA:** Gemini CLI
> **Status:** REJECTED

---

## Análise Técnica

A implementação cumpre os critérios básicos de endpoint e guard de profundidade, mas apresenta falhas estruturais graves que inviabilizam o uso em produção e contradizem o objetivo de uma "árvore N níveis".

### 1. Duplicação e Achatamento (Flattening)
O serviço `CpuExplosaoService` utiliza `servico_catalog_service.explode_composicao` tanto para o nível 0 quanto para as sub-explosões. 
- Como `explode_composicao` é **recursivo (DFS)** e retorna uma lista achatada de todos os insumos da árvore, a explosão de nível 0 (`explodir_proposta_item`) já cria todos os itens subjacentes como se fossem nível 0.
- Ao chamar o novo endpoint `explodir-sub`, o sistema busca novamente a explosão recursiva do insumo e cria duplicatas desses mesmos itens no `nivel + 1`.
- **Correção necessária:** `CpuExplosaoService` deve obter apenas os **filhos diretos** (nível 1 da composição) para construir a árvore corretamente. O nível 0 deve criar apenas o nível 1, e cada sub-explosão deve criar apenas o seu respectivo nível 1.

### 2. Falta de Metadados e Resolução de Snapshot
Os itens criados em sub-explosões estão com `tipo_recurso=None` e sem resolução de custo unitário.
- Isso impede que o `CpuCustoService` aplique tabelas de preços (PC) ou agrupe custos por categoria (Material/MO/Equipamento).
- **Correção necessária:** Reutilizar o método `_resolve_snapshot` e `_build_composicao` (ou lógica equivalente) dentro de `explodir_sub_composicao` para garantir integridade dos dados.

### 3. Suporte a Itens Próprios
O método `explodir_sub_composicao` verifica apenas `insumo_base_id`.
- Se a composição contiver um `ItemProprio` (insumo_proprio_id), ele será ignorado ou causará erro na explosão.
- **Correção necessária:** Suportar ambos os tipos de insumo na sub-explosão, assim como é feito no nível 0.

### 4. Migration e Encadeamento
A migration 019 foi encadeada na 017 no review, mas no arquivo final está na 018. Isso está correto, pois a 018 (F2-01) já foi entregue.

---

## Veredito

**REJECTED.** É necessária uma rodada de refatoração para garantir que o sistema construa uma árvore real sem duplicidade e com metadados completos.

Veja o briefing de rework em: `docs/briefings/sprint-f2-02-rework-v1.md`
