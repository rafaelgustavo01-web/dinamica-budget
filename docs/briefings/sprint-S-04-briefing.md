# Sprint S-04 Briefing

> **Role:** Supervisor  
> **Date:** 2026-04-22  
> **Sprint:** S-04 - Endurecer Suíte de Segurança e RBAC

## Objetivo

Fechar lacunas de autorização em endpoints sensíveis. Garantir que nenhum endpoint de READ exponha dados de clientes sem validação de acesso. Consolidar testes de regressão para todos os perfis (USUARIO, APROVADOR, ADMIN, is_admin).

## Escopo

1. **Endpoint `/busca/associacoes` (GET)** — adicionar `require_cliente_access` para o `cliente_id` da query
2. **Endpoint `/servicos/{item_id}/versoes` (GET)** — validar se usuário tem acesso ao cliente do item próprio
3. **Endpoint `/servicos/` (GET)** — validar `cliente_id` quando informado
4. **Cobertura de testes** — testes de regressão para perfis USUARIO, APROVADOR, ADMIN, is_admin
5. **Checklist OWASP API básica** — executar e documentar

## Critérios de Aceite

- Todos os endpoints de READ sensíveis validam acesso ao cliente
- Nenhum endpoint expõe dados cross-client sem autorização
- Testes de regressão cobrem autorização em todos endpoints sensíveis
- Checklist OWASP API básica executada com evidências

## Dependências

- S-01 concluída (OK) — modelo on-premise estabilizado
- S-02 concluída (OK) — arquitetura em camadas pronta

## Riscos

- Quebrar endpoints de leitura legítimos ao adicionar validação
- `is_admin` global pode mascarar falhas em testes (bypass total)
- PcTabelas sem `cliente_id` — fora do escopo desta sprint

## Worker Assignment

- Assigned worker: codex-5.3
- Provider: OpenAI
- Mode: BUILD

## Plano

Ver: `docs/superpowers/plans/2026-04-22-seguranca-rbac.md`
