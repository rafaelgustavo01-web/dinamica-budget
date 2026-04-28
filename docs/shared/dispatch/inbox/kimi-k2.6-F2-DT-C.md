# INBOX — Kimi K2.6 (HOLD)

**Data:** 2026-04-27
**De:** Scrum Master (PO + Arquiteto)
**Assunto:** Sprint Pre-Atribuida (HOLD) — F2-DT-C: Frontend Smoke Tests

---

## STATUS: HOLD

Esta sprint **nao deve ser iniciada agora**. Aguarda:

- [ ] F2-DT-A em DONE (contrato `codigo_origem` no backend)
- [ ] F2-DT-B em DONE (scaffold Vitest + RTL + MSW)

Quando ambas estiverem em DONE no `BACKLOG.md`, esta sprint sera
movida de `PLAN` para `TODO` pelo Scrum Master e voce sera notificado
nesta INBOX com nova mensagem.

---

## Atribuicao (futura)

| Campo | Valor |
|---|---|
| Sprint | F2-DT-C |
| Status atual | PLAN (HOLD) |
| Status quando despachar | TODO |
| Prioridade | P2 |
| Worker | kimi-k2.6 (Solo) |
| Mode | BUILD |
| Branch | main |
| Bloqueada por | F2-DT-A DONE + F2-DT-B DONE |

## Objetivo da Sprint

Escrever smoke tests minimos (1 por feature critica) para Histograma,
Composicoes (arvore), Propostas (lista + detalhe). Rede de seguranca
minima de regressao apos refactors futuros.

## Como Executar (apos hold liberado)

```
@docs/sprints/F2-DT-C/dispatch/sprint-F2-DT-C-worker-prompt.md
@docs/sprints/F2-DT-C/briefing/sprint-F2-DT-C-briefing.md
@docs/sprints/F2-DT-C/plans/2026-04-27-frontend-smoke-tests.md
```

## Artefatos que voce devera gerar

- `docs/sprints/F2-DT-C/technical-review/technical-review-YYYY-MM-DD-f2-dt-c.md`
- `docs/sprints/F2-DT-C/walkthrough/done/walkthrough-F2-DT-C.md`
- 4 arquivos de teste em `app/frontend/src/**/__tests__/`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-DT-C
  `TODO -> TESTED`

## Restricoes criticas (futuras)

- **NAO COMECE** sem confirmar F2-DT-A E F2-DT-B em DONE no BACKLOG.
- **Branch `main` apenas.** Sem feature branches.
- **1 commit unico:**
  `test(f2-dt-c): smoke tests for histograma, composicoes, propostas`
- Apenas arquivos novos em `**/__tests__/**` — NAO modificar producao.
- Nao marcar como DONE — apenas TESTED.

## Status no Registry

`available=true`, `busy=false`, `reserved_for_sprint=null` (reserva
ativa apenas quando sprint sair de HOLD).
