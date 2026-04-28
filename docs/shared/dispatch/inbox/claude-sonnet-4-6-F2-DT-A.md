# INBOX — Claude Sonnet 4.6

**Data:** 2026-04-27
**De:** Scrum Master (PO + Arquiteto)
**Assunto:** Nova Sprint Atribuida — F2-DT-A: Backend Tech Debt Cleanup

---

## Atribuicao

Voce foi designado como worker da sprint **F2-DT-A** no projeto
**Dinamica Budget**.

| Campo | Valor |
|---|---|
| Sprint | F2-DT-A |
| Status | TODO |
| Prioridade | P0 |
| Worker | claude-sonnet-4-6 |
| Mode | BUILD |
| Branch | main |
| Paralela com | F2-DT-B (Kimi, frontend — disjoint) |

## Objetivo da Sprint

Eliminar 18 itens de divida tecnica backend identificados no checkpoint
2026-04-27 (Amazon Q + Gemini + Kimi). Quatro commits atomicos
sequenciais: pytest infra -> purga pipeline legado -> N+1 batch +
bundle -> ETL durabilidade.

## Como Executar

Leia o prompt de execucao completo:

```
@docs/sprints/F2-DT-A/dispatch/sprint-F2-DT-A-worker-prompt.md
```

Briefing:

```
@docs/sprints/F2-DT-A/briefing/sprint-F2-DT-A-briefing.md
```

Plano aprovado:

```
@docs/sprints/F2-DT-A/plans/2026-04-27-backend-tech-debt-cleanup.md
```

## Artefatos que voce deve gerar

- `docs/sprints/F2-DT-A/technical-review/technical-review-2026-04-27-f2-dt-a.md`
- `docs/sprints/F2-DT-A/walkthrough/done/walkthrough-F2-DT-A.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-DT-A
  `TODO -> TESTED`

## Restricoes criticas

- **Branch `main` apenas.** Sem feature branches.
- **4 commits atomicos** com mensagem `feat(f2-dt-a/N): <descricao>`.
- **Suite verde apos cada commit** (197+ PASS, 0 FAIL).
- Nao marcar como DONE — apenas TESTED.
- **Nao tocar `app/frontend/**`** — ownership exclusivo de F2-DT-B.
- Contrato `codigo_origem` em `ComposicaoComponenteResponse` esta
  FROZEN no plan 3.5.
- Migration ETL nova com `down_revision` correto (proxima apos 024).

## Status no Registry

`available=false`, `busy=true`, `reserved_for_sprint="F2-DT-A"`
