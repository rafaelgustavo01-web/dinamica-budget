# Plano — F3-01: Demo Readiness Audit — UI/UX e fluxos críticos

## Objetivo
Mapear, sem alterar código, todos os erros de UI/UX que possam comprometer a apresentação desta semana.

## Escopo obrigatório
- Rotas/telas: Dashboard, Propostas, Criar Proposta, Importar PQ, Revisão de Match, CPU, Histograma, Composições, Exportação, Histórico/Aprovação e RBAC visual.
- Verificar estados: loading, empty, erro API, permissões, labels, botões, navegação, responsividade mínima desktop/notebook.
- Rodar gates disponíveis: build, typecheck/test frontend e smoke existente.
- Classificar achados: P0 bloqueia demo; P1 prejudica UX; P2 cosmético.

## Fora de escopo
- Implementar correções.
- Refatoração ampla.
- Compras/M7 funcional.

## Entregáveis
- `docs/sprints/F3-01/technical-review/uiux-audit-2026-04-29.md`
- `docs/sprints/F3-01/walkthrough/done/walkthrough-F3-01.md`

## Guardrails
- Branch `main` apenas.
- Commit/push automático ao concluir implementação ou documentação.
- Sem force-push, sem reset destrutivo, sem segredos.
- Produção não deve ser alterada.
