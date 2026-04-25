# Technical Review — S-06 Observabilidade e Operação On-Premise

## Status
`TESTED`

## Escopo
- Endpoint `/health/` para monitoramento.
- Script PowerShell de diagnóstico.
- Runbook de operação on-premise.

## Decisões Técnicas
- **Monitoramento sem Auth:** O endpoint de health check foi intencionalmente deixado sem autenticação JWT para facilitar o uso por agentes de infraestrutura (Zabbix, PRTG) que não possuem contexto de usuário, mas retornando apenas status binários (healthy/unhealthy) para evitar vazamento de dados sensíveis.
- **Port-Check para Postgres:** No script PowerShell, optou-se por validar a porta TCP (5432) em vez de usar o comando `psql`, pois o binário do PostgreSQL pode não estar no PATH do sistema Windows local, garantindo maior portabilidade do script de diagnóstico.
- **Versão em Health:** O endpoint retorna a versão "2.2.0" baseada no status atual do projeto, permitindo controle de inventário automático.

## Verificação Técnica
- Cobertura de testes unitários validada com mocking de exceções de banco para garantir que o status `degraded` seja reportado corretamente.
- Script PowerShell testado para lidar com timeouts e erros de rede de forma graciosa.

## Riscos e Observações
- **HSTS:** Conforme notado em sprints anteriores (S-04), o HSTS não está na camada da aplicação, devendo ser configurado no reverse proxy local conforme documentado no novo Runbook.
- **Permissões de Disco:** O script PowerShell requer permissões de leitura das classes WMI/CIM para obter estatísticas de disco.
