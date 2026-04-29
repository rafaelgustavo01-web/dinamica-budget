# Walkthrough - Sprint F2-13: Tabela Hierarquica de Composicoes (UX/UI Frontend)

## O que foi entregue

Implementacao de uma tabela expansivel (Tree Table) na pagina de Composicoes, permitindo drill-down hierarquico de servicos compostos em subservicos e insumos.

## Mudancas de codigo

### Backend

#### `app/backend/schemas/servico.py`
- Novo schema `ComposicaoComponenteResponse` com campo `tipo_recurso` para identificar itens expansiveis.

#### `app/backend/services/servico_catalog_service.py`
- Novo metodo `listar_componentes_diretos(servico_id, db)` que retorna **apenas filhos de nivel 1** (nao achatados) de uma composicao TCPO ou PROPRIA.
- Suporte a ambos os schemas: `referencia.composicao_base` (TCPO) e `ComposicaoCliente` via `VersaoComposicao` (PROPRIA).

#### `app/backend/api/v1/endpoints/servicos.py`
- Novo endpoint `GET /servicos/{servico_id}/componentes` autenticado, retornando `list[ComposicaoComponenteResponse]`.

### Frontend

#### `app/frontend/src/shared/types/contracts/servicos.ts`
- Adicionado `ComposicaoComponenteResponse` com `tipo_recurso: TipoRecurso | null`.

#### `app/frontend/src/shared/services/api/servicesApi.ts`
- Adicionado `getComponentes(servicoId: string)` que consome o novo endpoint.

#### `app/frontend/src/features/compositions/components/ExpandableTreeRow.tsx` (novo)
- Componente recursivo que renderiza uma linha de tabela expansivel.
- Recebe `item` (id, descricao, codigo, unidade, custo, tipo_recurso), `depth`, `isSelected`, `onSelect`.
- Se `tipo_recurso === 'SERVICO'`, exibe icone de expandir/colapsar (KeyboardArrowRight/Down).
- Ao expandir, dispara `useQuery(['composicao-componentes', item.id])` com lazy loading (`enabled: open && canExpand`).
- Filhos carregados sao renderizados recursivamente com `depth + 1` e indentacao visual (`pl: depth * 24px`).
- Estados: loading (CircularProgress), error, empty, recursivo.

#### `app/frontend/src/features/compositions/CompositionsPage.tsx`
- Substituindo o `DataTable` generico por `TableContainer` + `Table` MUI com `ExpandableTreeRow`.
- Mantido painel lateral para acoes de edicao (clonar, adicionar, remover componente) ao selecionar um servico.
- Cada linha da tabela eh clicavel para selecionar o servico (`onSelect`), separado do botao de expandir (`stopPropagation`).
- Mantida paginacao manual (Anterior/Proxima) e busca.

## Regressao

- `npx tsc --noEmit`: **0 erros**
- `pytest tests/unit -q`: **199 passed**, 12 errors (conexao Windows, pre-existentes), 0 novos failures

## Critérios de aceite verificados

| # | Criterio | Status |
|---|---|---|
| 1 | Tabela principal exibe servicos com icone de expansao | OK |
| 2 | Clique na expansao carrega filhos diretos via react-query lazy | OK |
| 3 | Sub-servicos tambem sao expansiveis (recursao) | OK |
| 4 | Indentacao visual demonstra aninhamento | OK |
| 5 | Padrões Material UI mantidos (Table, Collapse, IconButton) | OK |
| 6 | Painel lateral de edicao preservado | OK |

## Como testar manualmente

1. Acessar Composicoes e buscar um servico do tipo SERVICO.
2. Clicar na seta `>` ao lado da descricao — deve carregar os componentes diretos.
3. Se houver um sub-servico, ele tambem tera seta `>` e pode ser expandido.
4. Insumos (MAT., M.O., EQP., FER.) nao possuem seta de expansao.
5. Clicar na linha seleciona o servico no painel lateral para edicao.

## Proximos passos

- QA review do walkthrough + technical-review.
- Se aprovado, mover status para DONE.
