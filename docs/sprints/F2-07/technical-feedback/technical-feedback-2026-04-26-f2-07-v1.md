# Technical Feedback — F2-07 (QA Review)

## Sprint
F2-07 — Tabelas de Recursos + Motor 4 Camadas

## Data
2026-04-26

## QA
Amazon Q (revisão documental)

## Status
**ACCEPTED → DONE**

## Verificação QA

| Item | Resultado |
|---|---|
| Walkthrough | `docs/sprints/F2-07/walkthrough/done/walkthrough-F2-07.md` |
| Technical Review | `docs/sprints/F2-07/technical-review/technical-review-2026-04-26-f2-07.md` |
| Testes unitários | `133 passed, 0 failed` |

## Critérios de Aceite

- [x] `PropostaResumoRecurso` gerado ao chamar `gerar-cpu`
- [x] Migration 020 aplicada com sucesso (`proposta_resumo_recursos`)
- [x] Constraint `uq_proposta_recurso` previne duplicidade por categoria
- [x] BDI aplicado proporcionalmente por linha de resumo
- [x] Motor de busca aplica cascata: código exato → itens próprios → associação → global
- [x] `GET /propostas/{id}/recursos` retorna agregado por `TipoRecurso`
- [x] `ProposalResourcesPage` exibe tabela de recursos
- [x] 133 PASS, 0 regressions

## Observações

- Heurística de BDI (fração vs porcentagem) mantida para compatibilidade retroativa. Recomenda-se padronizar para porcentagem literal em sprints futuras de UI.
- Circuit-break por código exato evita custo de IA quando código é fornecido diretamente.
- Rework v1 foi necessário para corrigir achatamento da árvore de composições (entregue pelo worker após feedback QA).

## Scorecard

| Critério | Resultado |
|---|---|
| Escopo do plano entregue | YES |
| Testes aceitáveis | YES |
| Lint aceitável | YES |
| Documentação completa | YES |
| Estado do backlog correto | YES |

## Decisão

Sprint F2-07 → **DONE**.
