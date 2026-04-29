# Walkthrough — F3-04: Configurações finais + polimento visual + smoke de demo

Data: 2026-04-29
Status: TESTED
Worker: Claude Code (claude-sonnet-4-6)

## Resumo executivo

Sprint F3-04 executada. Polimentos visuais P2 restantes da auditoria F3-01 foram aplicados. Smoke checklist dos fluxos principais verificado estaticamente. Gates frontend verdes.

## Checklist de polimento aplicado

- [x] Histograma: empty state com CTA "Montar Histograma" quando `!data` (P2-2 de F3-01).
- [x] Histograma abas: mensagem orientativa quando aba vazia (P2-3 de F3-01).
- [x] Histograma colunas texto: campos não-numéricos como `grupo`, `funcao`, `tipo_mao_obra` exibem texto correto em vez de NaN.
- [x] Dashboard: métricas exibem `—` durante loading em vez de `0` (P2-1 de F3-01).
- [x] Loading padronizado: `CircularProgress` centrado em `ProposalDetailPage`, `ApprovalQueuePage`, `ProposalImportPage`, `ProposalCpuPage` (P2-4 de F3-01).

## Smoke checklist — fluxos da demo

| Fluxo | Resultado | Evidência |
|---|---|---|
| Criar proposta | PASS | Guard sem cliente ativo, form correto, erro de mutation. |
| Importar PQ | PASS | Loading centralizado, erro de proposta bloqueia fluxo, upload e match ok. |
| Revisão de Match | PASS | Scroll horizontal, progresso, 3 ações por item, empty state. |
| CPU — gerar | PASS | Erros distintos (proposta/itens), loading centralizado, export desativado em erro. |
| CPU — recalcular BDI | PASS | Campo BDI, botão alterna para recalcular após itens existentes. |
| Histograma — montar | PASS | Empty state com CTA, botão funcional via mutation, abas com empty rows. |
| Histograma — edição inline | PASS | Campos editáveis por aba, blur salva, aceitar divergência disponível. |
| Exportação Excel/PDF | PASS | ExportMenu presente no detalhe e na CPU, erros via snackbar. |
| Fila de Aprovação | PASS | Item visível no menu para admin/aprovador, loading centralizado, empty state, modal rejeição. |
| Detalhe da Proposta | PASS | Loading centralizado, status, totais, resumo histograma clickável, histórico de versões. |

## Evidência de gates

Executados em `app/frontend`:

```text
npm run build  → PASS (built in ~8s; warning chunk > 500 kB pré-existente)
npm run test   → PASS (4 arquivos, 13 testes)
```

## Pendências não bloqueantes

- Warning `ExpandableTreeRow`: HTML inválido (`tr` dentro de `div`) — herança de F2-13, não afeta runtime.
- Warning bundle chunk > 500 kB — não bloqueante para apresentação.

## Próximos passos

- Sprint F3-04 → TESTED. Aguarda QA (Gemini).
- Sprint F3-03 (roteiro/dados de demo) desbloqueada para iniciar após QA aprovar F3-04.
