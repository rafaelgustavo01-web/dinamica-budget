# Sprint F2-01 Briefing

> **Role:** Supervisor / SM
> **Date:** 2026-04-25
> **Sprint:** F2-01 - PQ Layout por Cliente

## Objetivo

Tornar a importacao de planilhas quantitativas flexivel por cliente, eliminando a dependencia de colunas com nomes fixos. Cada cliente tera um layout proprio configurado pelo admin, com mapeamento de colunas personalizadas.

## Escopo

1. **Novas entidades SQLAlchemy (schema `operacional`):**
   - `PqLayoutCliente` — 1:1 com cliente; aba Excel, linha de inicio, nome.
   - `PqImportacaoMapeamento` — N mapeamentos campo_sistema -> coluna_planilha.

2. **Novo enum:** `CampoSistemaPQ` (codigo, descricao, unidade, quantidade, observacao).

3. **Migration `018_pq_layout_cliente.py`** encadeando apos `017`.

4. **`PqLayoutService`:**
   - `criar_ou_substituir(cliente_id, req)` — idempotente.
   - `obter_por_cliente(cliente_id)` — retorna layout ou None.
   - `detectar_colunas_xlsx(filepath, aba)` — le cabecalho do arquivo.
   - `build_coluna_map(layout)` — dict campo->coluna.

5. **Endpoints:**
   - `PUT /clientes/{id}/pq-layout` (ADMIN only)
   - `GET /clientes/{id}/pq-layout` (usuario autenticado)

6. **Integracao em `pq_import_service.py`:** `_resolver_mapa_colunas` busca layout do cliente; fallback para nomes padrao.

7. **Testes:** 7 unitarios + 2 de integracao.

## Criterios de Aceite

- `PUT` com mapeamentos validos retorna 200 com layout serializado.
- `PUT` sem campo `descricao` nos mapeamentos retorna 422.
- `GET` sem layout configurado retorna `null` com status 200.
- Import de PQ usa colunas configuradas.
- Suite de regressao: 93+ PASS, 0 FAIL.

## Dependencias

- S-09 DONE, S-10 DONE
- Migration 018 encadeia apos 017

## Worker Assignment

- **Worker ID:** claude-sonnet-4-6
- **Provider:** Anthropic (Claude Code)
- **Mode:** BUILD

## Plano

Ver: `docs/sprints/F2-01/plans/2026-04-25-pq-layout-cliente.md`

## Restricoes

- Somente branch `main`.
- Nao alterar tabelas existentes de S-01 a S-12.
- Seguir padrao de repository/service existente.
