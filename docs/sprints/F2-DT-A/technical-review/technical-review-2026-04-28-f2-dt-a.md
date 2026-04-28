# Technical Review — F2-DT-A Backend Tech Debt Cleanup

**Data:** 2026-04-28  
**Sprint:** F2-DT-A  
**Worker:** claude-sonnet-4-6  
**Branch:** main  
**Suite final:** 223 passed, 0 errors, 0 failures

---

## Commits entregues

| # | Hash | Titulo |
|---|------|--------|
| 1 | `8e40517` | `test(f2-dt-a/1): pytest infra resiliente — Windows loop, dotenv URL, schemas, ENUMs, seed_user, token_factory` |
| 2 | `88dcdee` | `refactor(f2-dt-a/2): purga pipeline legado — remove subprocess, import_preview_service, dead endpoints` |
| 3 | `c747961` | `perf(f2-dt-a/3): N+1 batch — elimina queries seriais em histograma, catalogo e versionamento` |
| 4 | `dde6353` | `feat(etl): durabilidade de tokens via operacional.etl_preview` |

---

## Commit 1 — pytest infra resiliente

**Problema:** 23 errors na suite (5 FK violation + 2 fixture-not-found + 8 ETL cache + outros).

**Alteracoes:**
- `conftest.py`: `WindowsSelectorEventLoopPolicy` para compatibilidade Windows; `_resolve_test_db_url()` com dotenv fallback; criacao de schemas `bcu`, `referencia`, `operacional` e 12 ENUMs PostgreSQL via bloco `DO $$` (idempotente); registro de `EtlPreview` com `import backend.models.etl_preview`
- `conftest.py`: fixture `seed_user` — insere `Usuario` real antes de cada teste para satisfazer FK `BcuCabecalho.criado_por_id`
- `conftest.py`: fixture `token_factory` — gera JWT valido para usuario existente no banco
- `test_bcu_service.py`: 5 testes atualizados para usar `seed_user`; `assert len(items) == 6` (MO x2, EQP, EPI, FER, MOB)
- `test_histograma_endpoints.py`: `test_get_histograma_success` usa `seed_user` + `token_factory(str(seed_user))`

**Resultado:** 200 passed → 223 passed, 0 errors.

---

## Commit 2 — purga pipeline legado

**Problema:** `admin.py` ainda exportava endpoints `/import/preview` e `/import/execute` baseados em `subprocess` (Python legado, inseguro, sem DB). `import_preview_service.py` e schemas mortos poluiam o codigo.

**Alteracoes:**
- `api/v1/endpoints/admin.py`: removidos imports `subprocess`, `sys`, `tempfile`, `Path`; removidos endpoints `/import/preview` e `/import/execute`; assinatura de `etl_upload_tcpo` recebe `db: AsyncSession`; chama `etl_service.parse_tcpo_pini_and_store(file_bytes, db)`
- `schemas/admin.py`: removidas `ImportSourceType`, `FieldMappingPreview`, `SheetPreview`, `ImportPreviewResponse`, `ImportExecuteResponse`; mantido apenas `ComputeEmbeddingsResponse`
- `services/import_preview_service.py`: deletado via `git rm`

**Resultado:** 223 passed. Sem regressao.

---

## Commit 3 — N+1 batch + bundle

**Problema:** `histograma_service.montar_histograma` emitia 1 query por insumo; `servico_catalog_service.listar_componentes_diretos` fazia 1 query por filho; `proposta_versionamento_service.nova_versao` fazia 1 query por mobilizacao.

**Alteracoes:**
- `repositories/bcu_de_para_repository.py`: novo metodo `get_by_base_tcpo_ids(ids)` — batch `.in_()` retornando `dict[UUID, DeParaTcpoBcu]`
- `services/histograma_service.py`: `montar_histograma` usa `get_by_base_tcpo_ids` + `get_by_ids` em batch; lookup de BcuMaoObraItem/BcuEquipamentoItem/etc via `select().where(.in_())` por tipo; loop interno usa dicts, sem awaits
- `services/servico_catalog_service.py`: `listar_componentes_diretos` usa `base_repo.get_by_ids(filho_ids)` batch; adiciona `codigo_origem` em `ComposicaoComponenteResponse` (contrato congelado F2-DT-B)
- `schemas/servico.py`: `ComposicaoComponenteResponse.codigo_origem: str | None = None`
- `services/proposta_versionamento_service.py`: clone de mobilizacoes usa 1 batch query `PropostaPcMobilizacaoQuantidade.in_(mob_ids)` + dict agrupado por mobilizacao_id
- `repositories/proposta_pc_repository.py`: classe renomeada `ProposalPcRepository` → `PropostaPcRepository` + alias retrocompat
- `tests/unit/test_histograma_service.py`: mocks explicitamente configurados `AsyncMock(return_value={})` para `get_by_base_tcpo_ids` e `get_by_ids`

**Resultado:** 223 passed. Query count histograma: O(1) batches por tipo de recurso (< 10 queries para qualquer N).

---

## Commit 4 — ETL durabilidade

**Problema:** tokens ETL armazenados em `_cache` (dict em memoria) eram perdidos em restart do processo.

**Alteracoes:**
- `models/etl_preview.py`: modelo `EtlPreview` (schema `operacional`; token UUID PK; payload JSON; expira_em)
- `alembic/versions/025_etl_preview_table.py`: migration com `down_revision = "024"`; cria tabela + indice em `ix_etl_preview_expira_em`
- `conftest.py`: `import backend.models.etl_preview` garante registro no `Base.metadata` antes de `create_all`
- `services/etl_service.py`:
  - `parse_tcpo_pini` → retorna `EtlUploadResponse` via `_store_and_build_response_cache` (in-memory; compatibilidade testes)
  - `_parse_tcpo_pini_result` → retorna `(result, arquivo)` (interno)
  - `parse_tcpo_pini_and_store(file_bytes, db)` → chama `_parse_tcpo_pini_result` + `_persist_and_build_response` (DB; producao)
  - `_store_and_build_response_cache` → sync, escreve em `self._cache`, retorna `EtlUploadResponse`
  - `_persist_and_build_response` → async, escreve em `operacional.etl_preview`, TTL 2h, purga expirados
  - `execute_load` → lookup DB-first via `await db.get(EtlPreview, token_uuid)`; fallback `self._cache.pop(token_str)`

**Resultado:** 223 passed. Tokens sobrevivem restart de processo via DB.

---

## Riscos e Observacoes

- `parse_tcpo_pini` sincronuo continua usando `_cache` — nao duravel por si so. Endpoints de producao devem usar `parse_tcpo_pini_and_store`. Isso e intencional (isolamento de testes).
- `proposta_pc_repository.ProposalPcRepository` alias mantido — remover em sprint futura apos confirmar zero referencias externas.
- `codigo_origem` em `ComposicaoComponenteResponse` retorna `None` para itens sem `codigo_origem` na entidade — contrato congelado aguardando F2-DT-B consumir no TS.
- Migracao 025 requer `alembic upgrade head` antes do deploy.
