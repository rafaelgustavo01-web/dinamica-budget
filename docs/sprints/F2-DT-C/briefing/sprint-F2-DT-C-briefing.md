# Sprint Briefing — F2-DT-C — Frontend Smoke Tests

> Data: 2026-04-27
> Preparado por: Supervisor (PO + Arquiteto)
> Worker designado: kimi-k2.6 (Solo)
> Execution mode: BUILD
> Status: PLAN (HOLD ate F2-DT-A E F2-DT-B em DONE)
> Plan: `docs/sprints/F2-DT-C/plans/2026-04-27-frontend-smoke-tests.md`

## Mission

Apos F2-DT-B entregar o scaffold Vitest + RTL + MSW e F2-DT-A entregar
o contrato `codigo_origem`, esta sprint escreve **smoke tests minimos**
para 3 features criticas: Histograma da Proposta, Composicoes (arvore
expansivel), Propostas (lista + detalhe).

Sao testes de integracao no nivel de componente — nao cobertura
completa. Objetivo: rede de seguranca minima para refactors futuros.

## Delegation Envelope

| Campo | Valor |
|---|---|
| Sprint | F2-DT-C |
| Status entrada | PLAN (HOLD) |
| Status saida | TESTED |
| Worker | kimi-k2.6 |
| Provider | Moonshot |
| Mode | BUILD |
| Branch | main (regra global) |
| Bloqueada por | F2-DT-A DONE + F2-DT-B DONE |

## Pre-requisitos

- **F2-DT-A em DONE** — contrato `codigo_origem` no backend
- **F2-DT-B em DONE** — scaffold Vitest + MSW disponivel
- `npm run test` deve retornar "no tests found" sem erro de
  configuracao antes de comecar

## Required Changes (resumo — detalhe no plan)

| # | Test File | Cobertura |
|---|---|---|
| 1 | ProposalHistogramaPage.test.tsx | render + troca aba + edicao + divergencia |
| 2 | ExpandableTreeRow.test.tsx | render + expand + filhos com codigo_origem |
| 3 | ProposalsListPage.test.tsx | render + filtro + navegacao |
| 4 | ProposalDetailPage.test.tsx | render + ExportMenu + erro export + botao delete (conforme F2-DT-B) |

## Mandatory Tests

- 4 arquivos de teste novos em `**/__tests__/**`
- 12+ asserts no total
- `npm run test` passa
- `npm run build` continua verde

```bash
cd app/frontend
npm run test
npm run build
```

## Required Artifacts Before Status `TESTED`

- `docs/sprints/F2-DT-C/technical-review/technical-review-YYYY-MM-DD-f2-dt-c.md`
- `docs/sprints/F2-DT-C/walkthrough/done/walkthrough-F2-DT-C.md`
- `docs/shared/governance/BACKLOG.md` atualizado de `TODO` para `TESTED`

## Critical Warnings

1. **NAO COMECE** ate F2-DT-A E F2-DT-B estarem ambas em DONE.
2. **Branch `main` apenas.**
3. **1 commit unico** com todos os 4 arquivos de teste:
   `test(f2-dt-c): smoke tests for histograma, composicoes, propostas`.
4. Apenas arquivos novos em `**/__tests__/**` — NAO modificar codigo de
   producao do frontend ou do backend.
5. Para o botao Excluir em ProposalDetailPage: verifique a decisao
   tomada em F2-DT-B (botao escondido OU implementado) e teste
   conforme.
6. Se algum componente for intestavel sem refactor, registre como
   debito no walkthrough — NAO refactore producao nesta sprint.
7. Nao marcar como DONE — apenas TESTED.
