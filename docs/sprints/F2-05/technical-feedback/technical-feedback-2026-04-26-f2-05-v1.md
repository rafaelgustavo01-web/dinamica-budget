# Technical Feedback — F2-05 (QA Review)

## Sprint
F2-05 — Exportação Excel/PDF

## Data
2026-04-26

## QA
Amazon Q (revisão documental)

## Status
**ACCEPTED → DONE**

## Verificação QA

| Item | Resultado |
|---|---|
| Walkthrough | `docs/sprints/F2-05/walkthrough/done/walkthrough-F2-05.md` |
| Technical Review | `docs/sprints/F2-05/technical-review/technical-review-2026-04-26-f2-05.md` |
| Testes unitários | `130+ passed, 0 failed` |
| TypeScript | `0 erros (npx tsc --noEmit)` |

## Critérios de Aceite

- [x] Excel com 4 abas: Capa, Quadro-Resumo, CPU, Composições
- [x] PDF válido com header `%PDF`
- [x] Headers HTTP com `Content-Disposition: attachment`
- [x] Componente `ExportMenu` presente em `ProposalDetailPage` e `ProposalCpuPage`
- [x] Download via `Blob + URL.createObjectURL` no frontend
- [x] Quadro-Resumo agrega `custo_total_insumo` por `tipo_recurso`
- [x] Endpoints autenticados via `require_proposta_role`
- [x] 130+ pytest PASS, 0 FAIL, 0 tsc errors

## Observações

- Dependência `reportlab>=4.0.0` adicionada ao `requirements.txt`.
- Streaming de bytes via `StreamingResponse` no backend — sem materialização em memória.
- Excel gerado com `openpyxl` multi-aba de forma determinística.

## Scorecard

| Critério | Resultado |
|---|---|
| Escopo do plano entregue | YES |
| Testes aceitáveis | YES |
| Lint aceitável | YES |
| Documentação completa | YES |
| Estado do backlog correto | YES |

## Decisão

Sprint F2-05 → **DONE**.
