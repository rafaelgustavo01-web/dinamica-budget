# Sprint F4-DT-02 — QA Residual Debt Cleanup

## Status
- Status inicial: TODO
- Status final: TESTED
- Prioridade: P1
- Dependências: F4-DT-01

## Objetivo
Corrigir os débitos técnicos residuais encontrados no QA das últimas 10 sprints sem ampliar escopo funcional.

## Escopo
- Derivar status de match PQ do banco quando o cache em memória não existir.
- Corrigir mojibake em ProposalItemsExpandedPage.
- Substituir body: dict por schemas Pydantic nos endpoints principais de itens da proposta.
- Normalizar documentação da F4-DT-01 e registrar evidências.

## Fora de escopo
- Alembic/DB em ambiente de deploy.
- M7/Compras.
- Deploy/restart de produção.
