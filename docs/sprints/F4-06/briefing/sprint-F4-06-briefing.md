# Sprint F4-06 — Pós-deploy Import/Match Stabilization

## Status
- Status inicial: BACKLOG
- Prioridade: P0
- Dependências: F4-05

## Objetivo
Reproduzir e corrigir bugs reais remanescentes dos fluxos de Smart Import, PQ Match, criação de proposta e upload individual de bases usando request_id/logs locais.

## Critérios de aceite
Erros reproduzidos com código rastreável; 500 de importação resolvido se confirmado; cliente obrigatório e numeração automática preservados; match não pede reexecução indevida; gates backend/frontend verdes.

## Guardrails
- Sem deploy/restart de produção sem OK explícito.
- Sem force-push/reset destrutivo.
- Preservar compatibilidade dos fluxos que já funcionam.
- Usar observabilidade local (request_id) para diagnosticar erros antes de alterar lógica.
