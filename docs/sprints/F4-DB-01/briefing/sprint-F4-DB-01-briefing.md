# Sprint F4-DB-01 — Alembic/DB Validation Gate

## Status
- Status inicial: BACKLOG
- Prioridade: P0
- Worker esperado: Kimi na instância de deploy
- Dependências: F4-05, F4-DT-02

## Objetivo
Validar a Fase 4 contra banco real/seguro antes de promover F4-01..F4-05 para DONE.

## Guardrails
- Fazer backup antes de qualquer mutação.
- Não fazer deploy/restart da aplicação sem OK explícito.
- Não usar drop/reset destrutivo em banco com dados reais.
- Se o ambiente não for seguro para downgrade, registrar bloqueio e executar validações read-only + upgrade em clone/staging.
