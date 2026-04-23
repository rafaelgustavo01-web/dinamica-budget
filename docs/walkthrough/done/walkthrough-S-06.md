# Walkthrough — S-06 Observabilidade e Operação On-Premise

## Status
`TESTED`

## O que mudou
- **Health Check Endpoint:** Adicionado `/api/v1/health/` para monitoramento automatizado. Retorna o status da aplicação e a conectividade com o banco de dados PostgreSQL.
- **Script de Diagnóstico PowerShell:** Criado `scripts/health-check.ps1` para uso em ambiente Windows Server. Realiza 3 verificações críticas:
  1. Disponibilidade da API REST.
  2. Conectividade TCP com o PostgreSQL.
  3. Espaço em disco na partição do sistema (C:).
- **Runbook Operacional:** Criado `docs/runbook-operacional.md` consolidando as instruções de instalação, backup diário e guia de resolução de problemas (troubleshooting).

## Critérios de Aceite
- Endpoint `/health/` funcional e testado: ✅
- Script PowerShell com relatório colorido e amigável: ✅
- Documentação de backup/restore e troubleshooting concluída: ✅

## Verificação
- `pytest app/tests/unit/test_health.py -v`: 2 tests passed.
- Execução manual do script PowerShell validada localmente.

## Notas para o QA (OpenCode)
Este sprint foca na estabilidade operacional em servidores locais. O script PowerShell é agnóstico à infraestrutura de cloud e deve ser a ferramenta primária para o suporte de Nível 1.
