# Technical Review - Sprint F2-13: Tabela Hierarquica de Composicoes

**Data:** 2026-04-27
**Worker:** kimi-k2.6
**Branch:** main

## Arquivos alterados

| Arquivo | Tipo | Descricao |
|---|---|---|
| `app/backend/schemas/servico.py` | Modificado | Novo schema `ComposicaoComponenteResponse` com `tipo_recurso` |
| `app/backend/services/servico_catalog_service.py` | Modificado | Metodo `listar_componentes_diretos` (nivel 1, TCPO + PROPRIA) |
| `app/backend/api/v1/endpoints/servicos.py` | Modificado | Endpoint `GET /servicos/{id}/componentes` |
| `app/frontend/src/shared/types/contracts/servicos.ts` | Modificado | Tipo `ComposicaoComponenteResponse` |
| `app/frontend/src/shared/services/api/servicesApi.ts` | Modificado | Metodo `getComponentes` |
| `app/frontend/src/features/compositions/components/ExpandableTreeRow.tsx` | Novo | Componente recursivo expansivel com lazy loading |
| `app/frontend/src/features/compositions/CompositionsPage.tsx` | Modificado | Refatorado de DataTable para Table MUI com ExpandableTreeRow |

## Checklist de qualidade

- [x] Codigo segue padrao do repositorio (PEP 8, type hints, MUI patterns)
- [x] Novo endpoint autenticado e documentado no OpenAPI
- [x] Lazy loading via react-query com cache por servico_id
- [x] Recursao controlada por `tipo_recurso === 'SERVICO'`
- [x] Componente reutilizavel (`ExpandableTreeRow`) desacoplado da pagina
- [x] Painel lateral de edicao preservado sem regressao
- [x] tsc --noEmit: 0 erros
- [x] pytest regressao: 199 passed, 0 novos failures

## Decisoes tecnicas

1. **Por que criar endpoint novo em vez de reaproveitar `GET /composicao`?**
   - O endpoint existente `explode_composicao` faz DFS e **achata** (flatten) todos os niveis, multiplicando quantidades.
   - Para uma tree table, precisamos da estrutura hierarquica original: saber quais filhos sao subservicos (expansiveis) e quais sao insumos (folhas).
   - `listar_componentes_diretos` retorna apenas nivel 1, preservando a identidade de cada filho.

2. **Por que `tipo_recurso` no response?**
   - O frontend precisa saber se um item eh `SERVICO` (expandivel) ou `MO`/`INSUMO`/`EQUIPAMENTO`/`FERRAMENTA` (folha) antes de renderizar o icone de expansao.

3. **Por que nao usar `DataTable` generico?**
   - `DataTable` eh um componente de lista plana sem suporte a linhas aninhadas ou collapse.
   - A tabela MUI nativa (`Table`/`TableBody`/`Collapse`) oferece controle total sobre o layout recursivo.

4. **Cross-check: clique na linha vs. clique no icone de expandir**
   - `onClick` na linha inteira seleciona o servico para o painel lateral.
   - `stopPropagation` no `IconButton` evita que o clique na seta dispare a selecao.
   - Isso permite expandir sem perder a selecao atual.

## Riscos

| Risco | Severidade | Mitigacao |
|---|---|---|
| Recursao profunda em composicoes muito aninhadas | Baixa | Depth limitada pela estrutura TCPO (tipicamente <= 5); indentacao cresce linearmente |
| N+1 queries no backend ao listar componentes diretos | Baixa | Metodo faz `select` unico em `composicao_base` + `get_by_id` por filho; aceitavel para nivel 1 |
| Cache stale apos edicao de composicao | Baixa | `queryClient.invalidateQueries` ja eh disparado pelas mutacoes existentes (clonar, adicionar, remover) |

## Observacoes para QA

- Testar com servicos TCPO que tenham subservicos (ex: SER.CG que consome outro SER.CG).
- Verificar que insumos diretos nao exibem seta de expansao.
- Verificar que a selecao de servico no painel lateral funciona mesmo apos expandir/colapsar.
