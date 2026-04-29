# Síntese Brainstorm M7 — Compras e Negociação

**Data:** 2026-04-29  
**Orquestrador:** gedAI  
**Fontes:** Codex + tentativa Claude Code

## Resultado

**Recomendação: GO condicional.**

Seguir com Milestone 7 faz sentido do ponto de vista de produto, porque a base de Proposta, CPU, BCU, Histograma, RBAC e Versionamento já existe. Porém, não é seguro reativar diretamente as sprints antigas de Compras enquanto o pipeline documental está desalinhado e há colisão de IDs (`F2-13`).

## Consenso técnico disponível

Codex recomendou abrir um ciclo curto `M7-0` antes de reativar Compras:

1. normalizar BACKLOG/inboxes/config;
2. evitar reutilizar IDs antigos;
3. decidir contrato de permissão de Compras (`COMPRADOR` vs papéis atuais);
4. decidir onde vive o custo ajustado e quando recalcula totais;
5. tratar ou aceitar formalmente findings HIGH ligados a BCU, Histograma, Exportação, Transações e Árvore.

## Claude

A tentativa de consulta ao Claude Code em 2026-04-29 falhou por limite temporário de uso (`resets 5:10pm UTC`). O brainstorm deve ser repetido com Claude quando a cota liberar, antes de congelar a arquitetura final do M7.

## Proposta de sequência

- `M7-0` — Saneamento operacional e contratos de Compras.
- `M7-1` — Mapa de Compras e papel operacional.
- `M7-2` — Cotações backend.
- `M7-3` — Tela de Compras.
- `M7-4` — Comparativo e impacto na proposta.

## Decisão pendente

PO deve decidir se aprova abertura de `M7-0` como próximo ciclo.
