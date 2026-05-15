# Sprint F4-DT-01 — QA Hygiene + Backlog/Registry Cleanup

## Status
- Status inicial: BACKLOG
- Prioridade: P1
- Dependências: F4-05

## Objetivo
Remover ruídos técnicos pequenos que reduzem confiança do QA antes de retomar M7.

## Critérios de aceite
MSW handler faltante corrigido; nesting HTML do ExpandableTreeRow corrigido; decisão documentada para vulnerabilidade xlsx; workers/backlog/pipeline consistentes; build/test/lint verdes.

## Guardrails
- Sem deploy/restart de produção sem OK explícito.
- Sem force-push/reset destrutivo.
- Preservar compatibilidade dos fluxos que já funcionam.
- Usar observabilidade local (request_id) para diagnosticar erros antes de alterar lógica.
