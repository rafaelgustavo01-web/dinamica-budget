# Síntese Brainstorm M7 — Compras e Negociação

**Data:** 2026-04-29  
**Orquestrador:** gedAI  
**Fontes:** Codex + Claude Code

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

Consulta repetida com sucesso em 2026-04-29 após liberação da cota. Claude concordou com o Codex na recomendação **GO condicional**, com uma nuance importante: não abrir outro milestone antes; abrir imediatamente `M7-0` como sprint de saneamento e contrato, e só depois despachar as sprints funcionais de Compras.

Documento: `docs/sprints/multi/brainstorm-m7-claude-2026-04-29.md`.

## Proposta de sequência

- `M7-0` — Saneamento operacional e contratos de Compras.
- `M7-1` — Mapa de Compras e papel operacional.
- `M7-2` — Cotações backend.
- `M7-3` — Tela de Compras.
- `M7-4` — Comparativo e impacto na proposta.

## Decisão pendente

PO deve decidir se aprova abertura de `M7-0` como próximo ciclo.
