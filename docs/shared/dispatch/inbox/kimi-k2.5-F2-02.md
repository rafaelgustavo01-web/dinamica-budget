# INBOX — Kimi K2.5

**Data:** 2026-04-25 10:00
**De:** SM / Supervisor (Claude Sonnet 4.6)
**Assunto:** Nova Sprint Atribuida — F2-02: Explosao Recursiva de Composicoes

---

## Atribuicao

Voce foi designado como worker da sprint **F2-02** no projeto **Dinamica Budget**.

| Campo | Valor |
|---|---|
| Sprint | F2-02 |
| Status | TODO |
| Prioridade | P1 |
| Worker | kimi-k2.5 |
| Mode | BUILD |

## Objetivo da Sprint

Permitir explosao recursiva de composicoes em arvore (N niveis), com guard de profundidade (max 5) e novo endpoint `explodir-sub`.

## Como Executar

Leia o prompt de execucao completo:

```
@docs/sprints/F2-02/dispatch/sprint-F2-02-worker-prompt.md
```

Ou execute diretamente o plano:

```
@docs/sprints/F2-02/plans/2026-04-25-explosao-recursiva.md
```

## Artefatos que voce deve gerar

- `docs/sprints/F2-02/technical-review/technical-review-2026-04-25-f2-02.md`
- `docs/sprints/F2-02/walkthrough/done/walkthrough-F2-02.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-02 de `TODO` para `TESTED`

## Restricoes criticas

- Branch `main` apenas.
- Nao marcar como DONE — apenas TESTED.
- 93+ PASS na suite de regressao antes de marcar TESTED.
- Migration 019 com `down_revision = "018"`.
- Self-reference SQLAlchemy: `foreign_keys` e `remote_side` explicitos obrigatorios.
- Nao alterar logica de explosao nivel-0 existente.

## Status no Registry

`available=false`, `busy=true`, `reserved_for_sprint="F2-02"`
