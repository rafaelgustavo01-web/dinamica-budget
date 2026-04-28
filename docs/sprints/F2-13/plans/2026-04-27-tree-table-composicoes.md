# Plano de Implementação: Tabela Hierárquica de Composições (Sprint F2-13)

**Data:** 2026-04-27
**Autor:** PO / Scrum Master / Supervisor AI (Gemini)

## 1. Visão Geral
Alterar a visualização do Catálogo de Referência (Base TCPO/BCU) no Frontend para suportar o drill-down em árvore (Tree Table / Master-Detail). Serviços compostos podem ser expandidos para revelar os insumos e sub-serviços que os compõem.

## 2. A Solução (Arquitetura de Componentes)
A UI atual usa o Material UI (`Table`, `TableHead`, `TableRow`, `TableCell`).
Vamos introduzir o conceito de "Expanded Row" usando o componente `<Collapse>` nativo do MUI.

### Componente Principal: `Row` (Componente Extraído)
Para manter o código limpo, a linha da tabela (antigo `<TableRow>`) deve ser abstraída para um novo componente `<ExpandableRow row={item} />`.
Este componente controlará seu próprio estado de expansão: `const [open, setOpen] = useState(false);`.

### Fluxo de Dados e Carregamento Sob Demanda (Lazy Loading)
Como o backend já possui endpoints para explodir e listar composição:
1. O Catálogo primário lista apenas os itens raiz (Serviços Sintéticos).
2. Se o tipo de item for `SERVICO`, renderiza um `IconButton` com seta na primeira célula.
3. Ao clicar na seta, se `open` mudar para `true`:
   - Se os filhos já foram carregados, exibe o `<Collapse>`.
   - Se os filhos não foram carregados, dispara a chamada via `useQuery` (ex: `getComponentesDoServico(row.id)`) exibindo um CircularProgress dentro do collapse até que cheguem.
4. Quando chegarem, renderiza uma sub-tabela aninhada. Para sub-serviços dentro dessa sub-tabela, a lógica recursiva pode ser aplicada.

## 3. Considerações Técnicas
- **React Query:** Utilizar chaves em cache atreladas ao ID do serviço pai `['composicao_componentes', parent_id]`.
- **Componentização:** Não jogar a lógica inteira na página `BcuPage` ou `BaseTcpoPage`. Criar um diretório de componentes granulares (ex: `src/features/catalogo/components/ExpandableTreeRow.tsx`).
- **Indicadores Visuais:** Usar ícones apropriados do `@mui/icons-material` (ex: `KeyboardArrowDown`, `KeyboardArrowRight`). Usar padding / margens laterais nas linhas filhas para demonstrar o aninhamento.

## 4. Ordem de Tarefas (Para o Worker)
1. Analisar as páginas atuais que exibem a tabela da BCU/TCPO.
2. Criar os hooks no React Query e clientes de API do Frontend para carregar os componentes de uma composição específica.
3. Extrair a linha da tabela para o componente `<ExpandableRow />` implementando o estado `open` e o `<Collapse>`.
4. Renderizar a sub-tabela recursivamente para os resultados filhos.
5. Rodar lint/type-check (`tsc --noEmit`).
6. Gerar o `walkthrough` de entrega e abrir handoff para QA.