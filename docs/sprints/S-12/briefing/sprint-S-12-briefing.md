# Sprint S-12 Briefing

> **Role:** Supervisor  
> **Date:** 2026-04-23  
> **Sprint:** S-12 — UX Frontend do Módulo de Orçamentos

## Objetivo

Entregar telas React funcionais para o fluxo completo de Orçamentos: criar proposta, listar propostas, importar PQ, executar match, visualizar CPU.

## Escopo

1. **Estrutura de features** — rotas, tipos TypeScript, organização em `features/proposals/`
2. **Tela de listagem** — tabela com código, título, status, total, data
3. **Tela de criação** — formulário simples (título, descrição)
4. **Tela de importação** — upload de arquivo + botão de match inteligente
5. **Tela de CPU** — tabela com código, descrição, quantidade, preço unitário, preço total + input BDI
6. **Integração de rotas** — adicionar ao router principal
7. **Smoke test** — build sem erros TypeScript

## Critérios de Aceite

- Listagem paginada de propostas com status badge colorido
- Formulário de criação valida campos obrigatórios
- Upload aceita `.xlsx` e `.csv`
- Match inteligente executa via API e atualiza a tela
- CPU exibe totais formatados em BRL
- Build do frontend passa sem erros TypeScript
- Navegação entre telas via React Router

## Dependências

- S-09 concluída (OK) — endpoints de propostas disponíveis
- S-10 concluída (assumida OK para planejamento) — endpoints de importação e match disponíveis
- S-11 concluída (assumida OK para planejamento) — endpoint de geração de CPU disponível
- Componentes UI base já existem (OK)

## Riscos

- APIs podem mudar se S-10/S-11 ainda estiverem em BUILD
- Necessidade de novos componentes UI não previstos
- Performance de listagem para muitas propostas (sem virtualização)

## Worker Assignment

- Assigned worker: gemini-3.1
- Provider: Google
- Mode: BUILD

## Plano

Ver: `docs/sprints/S-12/plans/2026-04-23-ux-frontend-modulo-orcamentos.md`

