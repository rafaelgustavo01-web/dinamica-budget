# Technical Review — Sprint F2-01: PQ Layout Cliente

**Data:** 2026-04-25
**Worker:** claude-sonnet-4-6
**Sprint:** F2-01
**Status:** TESTED

---

## Resumo

Implementação completa do feature de layout configurável de importação de PQ por cliente. O sistema permite que admins definam o mapeamento entre campos do sistema (`codigo`, `descricao`, `unidade`, `quantidade`, `observacao`) e os nomes reais das colunas nas planilhas dos clientes.

---

## Artefatos entregues

| Artefato | Caminho | Status |
|---|---|---|
| Enum CampoSistemaPQ | `app/backend/models/enums.py` | OK |
| Models ORM | `app/backend/models/pq_layout.py` | OK |
| Migration 018 | `app/alembic/versions/018_pq_layout_cliente.py` | OK |
| Schemas Pydantic | `app/backend/schemas/pq_layout.py` | OK |
| Repository | `app/backend/repositories/pq_layout_repository.py` | OK |
| Service | `app/backend/services/pq_layout_service.py` | OK |
| Endpoint | `app/backend/api/v1/endpoints/pq_layout.py` | OK |
| Router registration | `app/backend/api/v1/router.py` | OK |
| Import service integration | `app/backend/services/pq_import_service.py` | OK |
| Import endpoint update | `app/backend/api/v1/endpoints/pq_importacao.py` | OK |
| Unit tests | `app/backend/tests/unit/test_pq_layout_service.py` | OK |
| Integration tests | `app/backend/tests/integration/test_pq_layout_endpoint.py` | OK |

---

## Decisoes tecnicas

- **Tabelas**: `operacional.pq_layout_cliente` (1:1 com cliente) e `operacional.pq_importacao_mapeamento` (N por layout). FK com CASCADE DELETE.
- **Enum PostgreSQL**: `campo_sistema_pq_enum` criado com padrao idempotente `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL; END $$`.
- **PUT semantico**: `criar_ou_substituir` apaga layout existente antes de criar novo.
- **Fallback automatico**: `PqImportService` mantém compatibilidade total com clientes sem layout — usa aliases padrao quando repo retorna `None`.
- **Autenticacao**: PUT exige `get_current_admin_user`; GET exige `get_current_active_user`.

---

## Resultado dos testes

- 107 passed, 0 failed
- 11 errors pre-existentes (integration — DB indisponivel em test env)

---

## Commits

- `b93a02a` — models e migration
- `c439281` — schemas e repository
- `7a980a6` — service e endpoint
- `d617e9d` — integracao no import service
- `0a8bf70` — testes
