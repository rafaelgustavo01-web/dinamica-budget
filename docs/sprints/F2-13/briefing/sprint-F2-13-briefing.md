# Sprint F2-13: Tabela Hierárquica de Composições (UX/UI Frontend)

## Objetivo
Implementar uma Tabela Expansível (Tree Table ou Master-Detail) no Catálogo de Composições (Base de Referência TCPO/BCU). Como o backend agora suporta Composições N-Níveis (via `F2-02` e `F2-12`), a UI precisa refletir adequadamente a hierarquia de `Serviço > Sub-serviço > Insumo` sem misturar serviços e insumos em uma visão puramente plana ou confusa.

## Requisitos de UX/UI
1. A tabela principal de Referência/Catálogo deve exibir inicialmente apenas os **Serviços Pai** (nível 0).
2. Linhas de serviços compostos devem possuir um ícone de expansão (`>`).
3. Ao clicar na expansão, o componente deve exibir de forma identada/aninhada as linhas correspondentes aos **Insumos** e aos **Sub-serviços** daquela composição.
4. Caso o backend não retorne os filhos aninhados na listagem inicial do catálogo, o clique na expansão deve disparar a busca (`react-query`) para o endpoint de dados daquela composição específica.
5. Manter os padrões do Material UI (e.g. `Collapse`, `Table`, `TableRow`, ou bibliotecas adequadas como `Material-React-Table` se já em uso).

## Artefatos e Paths
- **Código alvo:** `app/frontend/src/features/` (Catálogo/TCPO)
- **Briefing:** `docs/sprints/F2-13/briefing/sprint-F2-13-briefing.md`
- **Plan:** `docs/sprints/F2-13/plans/2026-04-27-tree-table-composicoes.md`

## Worker Delegado
Kimi (kimi-k2.6)