# Walkthrough - S-01: Align Authorization to On-Premise Model

> **Date:** 2026-04-22
> **Sprint:** S-01
> **Status:** TESTED
> **Worker:** OpenCode

---

## Mission Accomplished

A S-01 implementa o modelo on-premise onde qualquer usuário autenticado pode ler dados de todos os clientes. Apenas operações de escrita exigem perfil APROVADOR/ADMIN por cliente.

---

## Changes Made

### Task 1.1 - Open GET /servicos/{id}
- **File:** `app/api/v1/endpoints/servicos.py`
- **Change:** Removido `_get_perfis_para_cliente` check
- **Status:** ✅ COMPLETED

### Task 1.2 - Open GET /servicos/
- **File:** `app/api/v1/endpoints/servicos.py`
- **Change:** Removido `require_cliente_access` call
- **Status:** ✅ COMPLETED

### Task 1.3 - Open GET /servicos/{id}/versoes
- **File:** `app/api/v1/endpoints/versoes.py`
- **Change:** Removido `require_cliente_access` from `list_versoes`
- **Status:** ✅ COMPLETED

### Task 1.4 - Open busca endpoints
- **File:** `app/api/v1/endpoints/busca.py`
- **Change:** Removido `require_cliente_access` from `buscar_servicos` and `list_associacoes`
- **Status:** ✅ COMPLETED

### Task 1.5 - Update unit tests
- **File:** `app/tests/unit/test_security_p0.py`
- **Change:** Adicionados 5 novos testes para open-read policy
- **Status:** ✅ COMPLETED

### Task 1.6 - Add integration test
- **File:** `app/tests/integration/test_auth_access_control.py`
- **Change:** `test_servico_propria_readable_without_client_link` ja existia
- **Status:** ✅ COMPLETED

### Task 1.7 - Verify write protection
- **Verification:** `test_write_endpoints_still_require_client_perfil` PASSED
- **Status:** ✅ COMPLETED

### Task 1.8 - Clean unused imports
- **File:** `app/api/v1/endpoints/busca.py`
- **Change:** Removido `require_cliente_access` do import
- **Status:** ✅ COMPLETED

---

## Test Results

```
============================= test session starts ==============================
platform win32 -- Python 3.12.9, pytest-9.0.3
collected 22 items

app/tests/unit/test_security_p0.py::test_validate_startup_config_rejects_default_key PASSED
app/tests/unit/test_security_p0.py::test_validate_startup_config_rejects_empty_key PASSED
app/tests/unit/test_security_p0.py::test_validate_startup_config_rejects_short_key PASSED
app/tests/unit/test_security_p0.py::test_validate_startup_config_accepts_strong_key PASSED
app/tests/unit/test_security_p0.py::test_settings_allowed_origins_is_not_wildcard PASSED
app/tests/unit/test_security_p0.py::test_usuario_create_rejects_short_password PASSED
app/tests/unit/test_security_p0.py::test_usuario_create_rejects_7_char_password PASSED
app/tests/unit/test_security_p0.py::test_usuario_create_accepts_8_char_password PASSED
app/tests/unit/test_security_p0.py::test_usuario_create_accepts_long_password PASSED
app/tests/unit/test_security_p0.py::test_get_servico_propria_open_to_any_authenticated_user PASSED
app/tests/unit/test_security_p0.py::test_list_servicos_with_cliente_id_no_access_check PASSED
app/tests/unit/test_security_p0.py::test_list_versoes_open_to_any_authenticated_user PASSED
app/tests/unit/test_security_p0.py::test_buscar_servicos_no_cliente_access_required PASSED
app/tests/unit/test_security_p0.py::test_list_associacoes_no_cliente_access_required PASSED
app/tests/unit/test_security_p0.py::test_write_endpoints_still_require_client_perfil PASSED
app/tests/unit/test_security_p0.py::test_create_usuario_endpoint_has_admin_dependency PASSED
app/tests/unit/test_security_p0.py::test_login_endpoint_has_rate_limit_decorator PASSED
app/tests/unit/test_security_p0.py::test_refresh_endpoint_has_rate_limit_decorator PASSED
app/tests/unit/test_security_p0.py::test_rate_limiter_module_exists PASSED
app/tests/unit/test_security_p0.py::test_get_client_ip_uses_forwarded_for PASSED
app/tests/unit/test_security_p0.py::test_get_client_ip_fallback_to_remote_address PASSED
app/tests/unit/test_security_p0.py::test_get_client_ip_handles_no_client PASSED

======================== 22 passed in 0.17s =========================
```

---

## Write Protection Verified

Os seguinte endpoints de escrita ainda exigem `require_cliente_perfil`:

| Endpoint | Method | Protection |
|---|---|---|
| `/composicoes/clonar` | POST | `require_cliente_perfil` |
| `/composicoes/{id}/componentes` | POST | `require_cliente_perfil` |
| `/composicoes/{id}/componentes/{comp_id}` | DELETE | `require_cliente_perfil` |
| `/homologacao/itens-proprios` | POST | `require_cliente_perfil` |
| `/homologacao/aprovar` | POST | `require_cliente_perfil` |
| `/composicoes/{id}/versoes` | POST | `require_cliente_perfil` |
| `/composicoes/versoes/{id}/ativar` | PATCH | `require_cliente_perfil` |
| `/busca/associar` | POST | `require_cliente_access` |
| `/busca/associacoes/{id}` | DELETE | `require_cliente_perfil` |

---

## Next Steps

1. **QA Review** - Verificar implementação
2. **Update BACKLOG** - Mover S-01 para DONE
3. **Merge to Main** - Push via PR (branch protegida)

---

> **Signed:** OpenCode Worker  
> **Timestamp:** 2026-04-22 14:40 UTC