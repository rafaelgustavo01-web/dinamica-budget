# Walkthrough — S-12 UX Frontend do Módulo de Orçamentos

## Status
`TESTED` (Com funcionalidades parciais devido a bloqueios de backend)

## O que mudou
- **Módulo de Orçamentos:** Criada nova funcionalidade no frontend para gestão de propostas comerciais.
- **Telas Entregues:**
  1. **Listagem de Propostas (`/propostas`):** Tabela paginada com resumo de código, título, status e total geral. Suporta navegação por clique na linha.
  2. **Criação de Proposta (`/propostas/nova`):** Formulário para criação de rascunhos vinculados ao cliente em contexto.
  3. **Detalhe da Proposta (`/propostas/:id`):** Visão consolidada dos metadados e totais financeiros.
  4. **Importação PQ (`/propostas/:id/importar`):** Interface de upload para planilhas `.xlsx` e `.csv` e botão de disparo para o Match Inteligente.
- **Navegação:** Adicionado item "Orçamentos" ao menu lateral na seção de Operação.
- **Integração:** Implementado `proposalsApi.ts` com suporte completo aos endpoints da S-09 e S-10.

## Bloqueios (Sprint S-11)
- A tela de **Visualização de CPU** (`/propostas/:id/cpu`) foi entregue como um placeholder funcional com aviso de contrato pendente (`ContractNotice`), pois os endpoints de geração e listagem de itens de CPU (S-11) ainda não estavam disponíveis no backend.

## Critérios de Aceite
- Listagem paginada com status badges: ✅
- Formulário de criação funcional: ✅
- Upload de arquivos integrado ao backend: ✅ (Via `/pq/importar`)
- Disparo de Match Inteligente funcional: ✅ (Via `/pq/match`)
- Build frontend sem erros: ✅

## Verificação
- `npm run build`: Sucesso em `app/frontend/`.
- Verificação de rotas em `router.tsx` e `navigationConfig.tsx`.

## Notas para o QA (OpenCode)
A funcionalidade de CPU deve ser testada apenas após a conclusão da S-11. As demais telas (Listagem, Detalhe, Criação e Importação) já estão prontas para homologação contra os endpoints das sprints S-09 e S-10.
