# Sprint S-06 Briefing

> **Role:** Supervisor  
> **Date:** 2026-04-23  
> **Sprint:** S-06 — Observabilidade e Operação On-Premise

## Objetivo

Entregar runbook operacional, health checks e scripts de diagnóstico para operação on-premise do Dinamica Budget.

## Escopo

1. **Health Check Endpoint** — `/api/v1/health/` retorna status da API e conexão com banco
2. **Script de Diagnóstico PowerShell** — `scripts/health-check.ps1` verifica API, PostgreSQL e disco
3. **Runbook Operacional** — `docs/runbook-operacional.md` com instalação, operações diárias e troubleshooting

## Critérios de Aceite

- Endpoint `/health/` retorna JSON com `status`, `database`, `version`
- Script PowerShell executa sem erros e reporta status colorido
- Runbook cobre instalação, backup, restore e troubleshooting dos 5 problemas mais comuns
- Sem dependências de cloud ou serviços externos

## Dependências

- Nenhuma (pode rodar a qualquer momento)

## Riscos

- Script PowerShell pode não funcionar em versões antigas do Windows
- Health check expõe informações sensíveis se não for protegido

## Worker Assignment

- Assigned worker: gemini-3.1
- Provider: Google
- Mode: BUILD

## Plano

Ver: `docs/sprints/S-06/plans/2026-04-23-runbook-observabilidade-onpremise.md`

