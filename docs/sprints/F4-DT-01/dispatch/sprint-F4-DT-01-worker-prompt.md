# Dispatch - F4-DT-01

Worker principal: Kimi K2.5.

Execute a sprint F4-DT-01 QA Hygiene + Backlog/Registry Cleanup seguindo:
- Briefing: docs/sprints/F4-DT-01/briefing/sprint-F4-DT-01-briefing.md
- Plano: docs/sprints/F4-DT-01/plans/2026-05-15-f4-dt-01-plan.md

## Escopo fechado
1. Corrigir MSW handler faltante nos testes.
2. Corrigir warning de nesting HTML em ExpandableTreeRow.
3. Tratar vulnerabilidade do xlsx com a melhor mitigacao segura para este repo: preferir upgrade/substituicao se compativel; se nao houver correcao viavel sem quebrar importacao, documentar mitigacao, risco e plano de troca.
4. Limpar/normalizar templates/workers.json ao finalizar a sprint.

## Regras
- Nao fazer deploy/restart de producao.
- Nao usar force-push, reset hard ou acoes destrutivas.
- Nao ampliar escopo para F4-06/M7/Compras.
- Preservar fluxos existentes de Smart Import, TCPO e CPU.
- Rodar gates obrigatorios do plano.
- Se os gates passarem, atualizar backlog de TODO para TESTED.
- Gerar technical review e walkthrough.
- Commitar e pushar em main.

## Saida esperada
Informe no final: arquivos alterados; gates executados e resultado; commit hash; status do push.
