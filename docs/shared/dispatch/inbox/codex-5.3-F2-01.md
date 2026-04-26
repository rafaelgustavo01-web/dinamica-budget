# INBOX — Codex 5.3

**Data:** 2026-04-25 10:00
**De:** SM / Supervisor (Claude Sonnet 4.6)
**Assunto:** Nova Sprint Atribuida — F2-01: PQ Layout por Cliente

---

## Atribuicao

Voce foi designado como worker da sprint **F2-01** no projeto **Dinamica Budget**.

| Campo | Valor |
|---|---|
| Sprint | F2-01 |
| Status | TODO |
| Prioridade | P1 |
| Worker | codex-5.3 |
| Mode | BUILD |

## Objetivo da Sprint

Tornar a importacao de planilhas PQ flexivel por cliente, com mapeamento de colunas configuravel via `PqLayoutCliente` e `PqImportacaoMapeamento`.

## Como Executar

Leia o prompt de execucao completo:

```
@docs/sprints/F2-01/dispatch/sprint-F2-01-worker-prompt.md
```

Ou execute diretamente o plano:

```
@docs/sprints/F2-01/plans/2026-04-25-pq-layout-cliente.md
```

## Artefatos que voce deve gerar

- `docs/sprints/F2-01/technical-review/technical-review-2026-04-25-f2-01.md`
- `docs/sprints/F2-01/walkthrough/done/walkthrough-F2-01.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-01 de `TODO` para `TESTED`

## Restricoes criticas

- Branch `main` apenas.
- Nao marcar como DONE — apenas TESTED.
- 93+ PASS na suite de regressao antes de marcar TESTED.
- Migration 018 com `down_revision = "017"`.

## Status no Registry

`available=false`, `busy=true`, `reserved_for_sprint="F2-01"`
