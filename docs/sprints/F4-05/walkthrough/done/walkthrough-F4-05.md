# Walkthrough — F4-05 Smart Import Hardening

## Arquivos Alterados

### Backend
- `app/backend/api/v1/endpoints/smart_import.py` — autorização `_authorize_job` + `_get_job` com `for_update`
- `app/backend/services/smart_import_service.py` — JSONB imutável, guarda `committed_at`, `_write_pq_items`, parser BR
- `app/backend/services/smart_import/extractor.py` — bounds de linhas/colunas, validação de aba, `wb.close()` seguro
- `app/backend/services/smart_import/header_detector.py` — validação de `profile_header_row` fora de range
- `app/backend/services/smart_import/number_parser.py` — **novo** — parser decimal brasileiro
- `app/backend/services/smart_import/row_classifier.py` — usa `parse_br_decimal`
- `app/backend/services/smart_import/profile_learner.py` — `_ALLOWED_FIELDS`, `_MAX_HEADER_ROW`, rejeita valores inválidos
- `app/backend/schemas/smart_import.py` — expõe `has_warnings` e `warnings` no response

### Frontend
- `app/frontend/src/shared/services/api/smartImportApi.ts` — tipagem `has_warnings`, `warnings`
- `app/frontend/src/features/smart-import/SmartImportStagingPage.tsx` — alerta condicional a `has_warnings`

### Testes
- `app/backend/tests/unit/smart_import/test_smart_import_auth.py` — **novo** — 7 testes de autorização
- `app/backend/tests/unit/smart_import/test_number_parser.py` — **novo** — 11 testes de parsing decimal
- `app/backend/tests/unit/smart_import/test_smart_import_service.py` — 4 testes de JSONB imutável + status
- `app/backend/tests/unit/smart_import/test_commit.py` — 8 testes de idempotência + PQ items
- `app/backend/tests/unit/smart_import/test_extractor.py` — 3 testes de bounds + aba inexistente
- `app/backend/tests/unit/smart_import/test_header_detector.py` — 2 testes de profile row inválida
- `app/backend/tests/unit/smart_import/test_profile_learner.py` — 3 testes de validação de inputs
- `app/backend/tests/unit/smart_import/test_row_classifier.py` — 1 teste de decimal BR

## Por Quê
- Fechar gaps P0 de autorização, duplicação de commit e parsing numérico incorreto.
- Evitar mutação silenciosa de JSONB que dificulta auditoria.
- Proteger contra planilhas abusivas (100k+ linhas ou colunas).
- Impedir que o learning loop aprenda campos arbitrários ou header rows absurdos.

## Verificações Realizadas
| Comando | Resultado |
|---------|-----------|
| `pytest tests/unit/smart_import -q` | **77 passed, 8 warnings** |
| `pytest tests/unit/test_security_p0.py tests/unit/test_proposta_acl_dependency.py` | **28 passed** (excluindo falha pré-existente em `test_security_s04.py`) |
| `git diff --check` | **Sem trailing whitespace** |

## Risco Residual
- Build frontend bloqueado por dependências faltantes no ambiente (`xlsx`, `@tanstack/react-virtual`); não é regressão do F4-05.
- Teste `test_security_s04.py::test_list_servicos_validates_cliente_id_access_when_present` falha por bug pré-existente de Pydantic `Query(None)` em `servicos.py`.

## QA Handoff
- Suite `tests/unit/smart_import` está verde e pode ser usada como gate de regressão.
- Commit idempotente coberto por teste unitário; QA deve validar concorrência real com múltiplas requisições paralelas.
- Pronto para merge local. Não fazer push até QA aprovar.
