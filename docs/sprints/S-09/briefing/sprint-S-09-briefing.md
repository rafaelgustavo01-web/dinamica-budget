# Sprint S-09 Briefing

> **Role:** Supervisor / SM  
> **Date:** 2026-04-23  
> **Sprint:** S-09 - Entidades e CRUD de Propostas

## Objetivo

Implementar a base do Módulo de Orçamentos, focando nas entidades de Proposta e Itens brutos (PQ). Este sprint é o alicerce para a importação e geração de CPU que virão a seguir.

## Escopo

1. **Modelagem SQLAlchemy 2.0:** Criar as tabelas `propostas`, `pq_importacoes`, `pq_itens`, `proposta_itens` e `proposta_item_composicoes` no schema `operacional`.
2. **Enums Operacionais:** Adicionar `StatusProposta`, `StatusImportacao`, `StatusMatch` e `TipoServicoMatch`.
3. **Padrão em Camadas:**
   - Repositories para Proposta e PqItem.
   - `PropostaService` para gerenciar o ciclo de vida (CRUD + Mudança de Status).
4. **API Endpoints:**
   - `POST /propostas` (Criar rascunho)
   - `GET /propostas` (Listar do cliente)
   - `GET /propostas/{id}` (Detalhe)
   - `PATCH /propostas/{id}` (Editar metadados)
   - `DELETE /propostas/{id}` (Soft delete)
5. **Segurança:** Garantir `require_cliente_access` em todas as rotas.

## Critérios de Aceite

- Tabelas criadas via Alembic.
- CRUD de Proposta funcional e validado com testes unitários.
- Isolamento por cliente (cross-tenant check) funcionando.
- Modelos seguem a `MODELAGEM_ORCAMENTOS_FASE2.md`.

## Dependências

- S-02 (Arquitetura em Camadas) ✅
- S-03 (Transações) ✅

## Worker Assignment

- Assigned worker: codex-5.3
- Provider: OpenAI
- Mode: BUILD

## Plano

Ver: `docs/sprints/S-09/plans/2026-04-23-entidades-propostas-crud.md`

