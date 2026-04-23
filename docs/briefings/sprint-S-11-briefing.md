# Sprint S-11 Briefing

> **Role:** Supervisor  
> **Date:** 2026-04-23  
> **Sprint:** S-11 — Geração da CPU (Composição de Preços Unitários)

## Objetivo

Explodir a composição de cada PropostaItem em insumos, calcular custos unitários via lookup em PcTabelas satélites, aplicar BDI, e gerar a CPU final com rastreabilidade completa.

## Escopo

1. **Modelagem complementar** — enum `TipoRecurso` e modelo `PropostaItemComposicao`
2. **Repository** — batch CRUD para `PropostaItemComposicao`
3. **Explosão de composição** — service que lê `VersaoComposicao`/`ComposicaoItem` e cria `PropostaItemComposicao`
4. **Lookup de custos** — service que consulta `PcMaoObraItem`, `PcEquipamentoItem` por `pc_cabecalho_id`
5. **Orquestração CPU** — service que coordena explosão + custos + BDI + persistência
6. **API endpoints** — `POST /propostas/{id}/cpu/gerar` e `GET /propostas/{id}/cpu/itens`
7. **Testes unitários** — cobertura de geração sem composição, com composição, e lookup

## Critérios de Aceite

- Todos os `PropostaItem` com match confirmado são processados
- Explosão reusa `ComposicaoItem` existente (base TCPQ e itens próprios)
- Custo unitário vem de PcTabelas quando disponível; zero quando não encontrado
- BDI aplicado corretamente sobre custo direto
- `preco_total = preco_unitario * quantidade` para cada item
- Rastreabilidade: `fonte_custo` e `composicao_fonte` preenchidos
- Testes unitários cobrem cenários com e sem composição
- Migração Alembic inclui `proposta_item_composicoes`

## Dependências

- S-09 concluída (OK) — entidades Proposta e PropostaItem existem
- S-10 concluída (assumida OK para planejamento) — PQ importada e match executado
- S-02 concluída (OK) — explosão de composição já implementada
- PcTabelas já modeladas (OK)

## Riscos

- Performance da explosão para propostas com >100 itens
- PcTabelas podem não ter entrada para todos os insumos (custo = 0)
- Heurística de `TipoRecurso` pode ser imprecisa

## Worker Assignment

- Assigned worker: codex-5.3
- Provider: OpenAI
- Mode: BUILD

## Plano

Ver: `docs/superpowers/plans/2026-04-23-geracao-cpu-composicao-precos.md`
