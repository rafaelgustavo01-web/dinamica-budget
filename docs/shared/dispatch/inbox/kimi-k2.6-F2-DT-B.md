# INBOX — Kimi K2.6

**Data:** 2026-04-27
**De:** Scrum Master (PO + Arquiteto)
**Assunto:** Nova Sprint Atribuida — F2-DT-B: Frontend Tech Debt Cleanup

---

## Atribuicao

Voce foi designado como worker da sprint **F2-DT-B** no projeto
**Dinamica Budget**.

| Campo | Valor |
|---|---|
| Sprint | F2-DT-B |
| Status | TODO |
| Prioridade | P1 |
| Worker | kimi-k2.6 |
| Mode | BUILD |
| Branch | main |
| Paralela com | F2-DT-A (Claude, backend — disjoint) |

## Objetivo da Sprint

Estabelecer fundacao Vitest + RTL + MSW no frontend (zero testes hoje)
e fechar 4 itens pendentes de polimento UI: ExportMenu sem feedback de
erro, codigo_origem ausente em filhos da arvore, botao Excluir com TODO
em ProposalDetailPage, e arquivo de tema duplicado.

## Como Executar

Leia o prompt de execucao completo:

```
@docs/sprints/F2-DT-B/dispatch/sprint-F2-DT-B-worker-prompt.md
```

Briefing:

```
@docs/sprints/F2-DT-B/briefing/sprint-F2-DT-B-briefing.md
```

Plano aprovado:

```
@docs/sprints/F2-DT-B/plans/2026-04-27-frontend-tech-debt-cleanup.md
```

## Artefatos que voce deve gerar

- `docs/sprints/F2-DT-B/technical-review/technical-review-2026-04-27-f2-dt-b.md`
- `docs/sprints/F2-DT-B/walkthrough/done/walkthrough-F2-DT-B.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-DT-B
  `TODO -> TESTED`

## Restricoes criticas

- **Branch `main` apenas.** Sem feature branches.
- **2 commits atomicos** com mensagem `feat(f2-dt-b/N): <descricao>`.
- `npm run build` + `tsc --noEmit` verdes apos cada commit.
- Nao marcar como DONE — apenas TESTED.
- **Nao tocar `app/backend/**`, `app/alembic/**`, `scripts/**`** —
  ownership exclusivo de F2-DT-A.
- Contrato `codigo_origem` em `ComposicaoComponenteResponse` esta
  FROZEN no plan secao 3.
- Para botao Excluir (2.4): VERIFIQUE backend primeiro; se endpoint
  nao existir, ESCONDA o botao (nao implemente backend).
- NAO escrever testes smoke reais — apenas scaffold (testes ficam para
  Sprint F2-DT-C).

## Status no Registry

`available=false`, `busy=true`, `reserved_for_sprint="F2-DT-B"`
