# F3-01 UI/UX Audit — Demo Readiness

Data: 2026-04-29  
Escopo: auditoria UI/UX para apresentação desta semana, sem alterar código de produção.

## Resultado executivo

- P0: nenhum bloqueador absoluto confirmado por auditoria estática.
- P1: 7 riscos que podem prejudicar a demo em fluxo feliz ou em notebook.
- P2: 4 polimentos de estado vazio/loading/clareza.
- Recomendação: seguir para `F3-02` antes da apresentação, priorizando CPU, Match Review, criação sem cliente e descoberta da fila de aprovação.

## Gates executados

| Gate | Resultado | Evidência |
|---|---:|---|
| `cd app/frontend && npm run build` | BLOCKED | `tsc: not found`; dependências locais ausentes. |
| `cd app/frontend && npm run lint` | BLOCKED | `eslint: not found`; dependências locais ausentes. |
| `cd app/frontend && npm run test` | BLOCKED | `vitest: not found`; dependências locais ausentes. |
| `cd app/frontend && npm ci --cache /tmp/npm-cache --prefer-offline` | BLOCKED | registry indisponível no ambiente: `EAI_AGAIN` para `registry.npmjs.org`; npm terminou com `Exit handler never called`. |
| `cd app && pytest app/backend/tests/e2e/test_smoke_proposta.py -q` | BLOCKED | `pytest: command not found`. |
| `cd app && python3 -m pytest backend/tests/e2e/test_smoke_proposta.py -q` | BLOCKED | `/usr/bin/python3: No module named pytest`. |

Observação: a sprint anterior `F2-DT-C` registrou `npm run test` 13/13 PASS e `npm run build` verde, mas nesta execução os gates não puderam ser reproduzidos por falta de dependências e rede.

## Rotas inspecionadas

| Tela / fluxo | Rota | Status de auditoria |
|---|---|---|
| Dashboard | `/dashboard` | Estados de cliente vazio e erro parcial existem; loading mostra métricas como zero até query resolver. |
| Propostas | `/propostas` | Lista, paginação, empty e erro existem. CTA Nova Proposta desabilita sem cliente. |
| Criar Proposta | `/propostas/nova` | Form direto não protege ausência de cliente. |
| Importar PQ | `/propostas/:id/importar` | Upload, loading e erros de mutation existem; erro da proposta não é tratado. |
| Revisão de Match | `/propostas/:id/match-review` | Fluxo funcional, progresso e empty existem; risco de clipping em tabela larga. |
| CPU | `/propostas/:id/cpu` | Geração/recalculo/export existem; risco alto de clipping e falta erro de query. |
| Histograma | `/propostas/:id/histograma` | 8 abas, divergências, loading e erro existem; divergência genérica incompleta para algumas abas. |
| Composições | `/composicoes` | Empty sem cliente, busca, tabela e dialogs existem; layout em duas colunas no desktop. |
| Exportação | `ExportMenu` em detalhe/CPU | Excel/PDF e erro via Snackbar existem. |
| Histórico/Aprovação | `/propostas/:id`, `/propostas/aprovacoes` | Histórico aparece por accordion; fila existe mas não é descobrível por menu. |
| RBAC visual | menu, `/permissoes`, detalhe proposta | Visibilidade por admin/cliente existe; página Permissões fica fora do menu e marcada como contrato pendente. |

## Achados P1

1. CPU pode ficar cortada em notebook/desktop estreito.
   - Evidência: `AppShell` usa `overflowX: 'clip'` em containers principais (`app/frontend/src/shared/components/layout/AppShell.tsx:17`, `:32`, `:49`) e `CpuTable` renderiza 11 colunas sem `TableContainer`/scroll horizontal (`app/frontend/src/features/proposals/components/CpuTable.tsx:178`).
   - Impacto: tabela central da demo pode esconder colunas de custos/totais.
   - Correção sugerida em F3-02: envolver CPU em `TableContainer` com `overflowX: 'auto'`, largura mínima estável e toolbar/totais responsivos.

2. Revisão de Match também pode ser cortada.
   - Evidência: tabela de 8 colunas é renderizada diretamente dentro de `Paper`, sem `TableContainer` (`app/frontend/src/features/proposals/pages/MatchReviewPage.tsx:136`).
   - Impacto: ações Confirmar/Rejeitar/Substituir podem sair da viewport durante a apresentação.
   - Correção sugerida: mesmo padrão de scroll horizontal aplicado à CPU.

3. Criar Proposta é acessível por URL sem cliente ativo.
   - Evidência: a lista desabilita o CTA sem cliente, mas `/propostas/nova` cria payload com `cliente_id: selectedClientId` mesmo quando vazio (`app/frontend/src/features/proposals/pages/ProposalCreatePage.tsx:15`, `:19`).
   - Impacto: demo pode cair em erro de API se o apresentador abrir rota direta ou trocar contexto.
   - Correção sugerida: empty/guard igual ao Dashboard/Composições quando não houver cliente.

4. Importar PQ não trata erro ao carregar a proposta.
   - Evidência: query de proposta só expõe `data` e `isLoading`; erro não é lido (`app/frontend/src/features/proposals/pages/ProposalImportPage.tsx:19`), então o header pode ficar sem código e os botões continuam disponíveis (`:44`, `:127`).
   - Impacto: falha de API/404 vira tela parcialmente funcional e confusa.
   - Correção sugerida: estado de erro e bloqueio de upload/match quando a proposta não carregar.

5. CPU não trata erro de proposta/itens.
   - Evidência: queries de proposta e itens não expõem `isError/error` (`app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx:31`, `:37`); se `listCpuItens` falhar, a tela pode mostrar "Nenhum item" e permitir ações.
   - Impacto: falhas reais parecem estado vazio, prejudicando diagnóstico na demo.
   - Correção sugerida: alertas distintos para erro de proposta e erro de itens; desabilitar export/gerar em erro.

6. Fila de Aprovação existe, mas não é descobrível.
   - Evidência: rota `/propostas/aprovacoes` existe (`app/frontend/src/features/proposals/routes.tsx:35`), mas não há item no `navigationItems` nem link localizado fora de URL manual (`app/frontend/src/shared/components/layout/navigationConfig.tsx:35`).
   - Impacto: fluxo "Histórico/Aprovação" fica frágil para apresentação.
   - Correção sugerida: adicionar entrada visível por perfil aprovador/admin ou CTA contextual em Orçamentos.

7. Divergências do Histograma não aparecem em todas as abas genéricas.
   - Evidência: `HistogramaTabGenerica` mapeia divergências apenas para `equipamento`, `epi` e `ferramenta` (`app/frontend/src/features/proposals/components/HistogramaTabGenerica.tsx:76`), mas a página usa o mesmo componente para `encargo` e `mobilizacao` (`app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx:147`, `:196`).
   - Impacto: chip global pode indicar divergência e a aba correspondente não mostrar linha/ação, gerando desconfiança na demo.
   - Correção sugerida: completar mapa de tabelas e cobrir com teste de abas de encargos/mobilização.

## Achados P2

1. Dashboard mostra métricas `0` enquanto queries carregam.
   - Impacto cosmético: pode parecer ausência de dados em vez de loading.
   - Sugestão: skeleton/linear progress ou helper "Carregando".

2. Histograma retorna `null` se a API devolver vazio.
   - Evidência: `if (!data) return null` (`app/frontend/src/features/proposals/pages/ProposalHistogramaPage.tsx:74`).
   - Sugestão: empty state com ação "Montar / Atualizar Histograma".

3. Abas vazias do Histograma renderizam tabela sem mensagem específica.
   - Impacto cosmético: parece quebra ou ausência de conteúdo.
   - Sugestão: linha vazia por aba com texto orientado ao domínio.

4. Labels de loading são heterogêneos.
   - Exemplos: `Carregando...`, `Carregando itens...`, circular central, linear progress.
   - Sugestão: padronizar estados críticos antes da apresentação.

## Cobertura de testes existente inspecionada

- `ProposalsListPage.test.tsx`: lista com 3 propostas e navegação para detalhe.
- `ProposalDetailPage.test.tsx`: header, ExportMenu, erro de export e botão Excluir para OWNER.
- `ProposalHistogramaPage.test.tsx`: render, troca de aba, divergência e edição inline.
- `ExpandableTreeRow.test.tsx`: raiz, filhos e recursão de 2 níveis.
- `src/test/msw/handlers.ts`: handler global ainda é placeholder de `/api/health`; os testes principais configuram handlers por arquivo.

## Decisão para F3-02

Prioridade recomendada:

1. P1-1 e P1-2: responsividade/scroll de CPU e Match Review.
2. P1-3, P1-4 e P1-5: guards/erros de Proposta, Importar PQ e CPU.
3. P1-6: descoberta da fila de aprovação.
4. P1-7 e P2: polimento de Histograma/loading/empty.

