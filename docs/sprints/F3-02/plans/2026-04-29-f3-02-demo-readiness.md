# Plano — F3-02: Correções críticas de UI/UX para apresentação

## Objetivo
Corrigir os achados P0/P1 da F3-01 que afetam a apresentação, com mudanças incrementais e seguras no frontend.

## Prioridade de telas
1. ProposalsListPage / ProposalDetailPage
2. ProposalImportPage / MatchReviewPage
3. ProposalCpuPage / ProposalHistogramaPage
4. CompositionsPage / árvore hierárquica
5. ExportMenu e feedbacks de erro/sucesso

## Critérios de aceite
- Fluxo feliz da demo completo sem erro visual ou quebra de navegação.
- `npm run build` verde.
- `npm run test` verde ou justificativa objetiva se não aplicável.
- Walkthrough com antes/depois e lista de pendências remanescentes.

## Guardrails
- Branch `main` apenas.
- Commit/push automático ao concluir implementação ou documentação.
- Sem force-push, sem reset destrutivo, sem segredos.
- Produção não deve ser alterada.
