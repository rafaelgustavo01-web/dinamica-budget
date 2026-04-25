# OWASP API Security Checklist — S-04

> Data: 2026-04-23
> Sprint: S-04 — Endurecer Suíte de Segurança e RBAC
> Executado por: Kimi K2.5

---

## API1:2023 — Broken Object Level Authorization

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 1 | Todos os endpoints com `cliente_id` validam ownership/acesso | ✅ PASS | `busca.py:65`, `servicos.py:35`, `versoes.py:41` |
| 2 | Testes cobrem acesso a recursos de outro cliente | ✅ PASS | `test_security_s04.py` — 3 cenários cobertos |
| 3 | `is_admin` global não expõe dados indevidamente | ✅ PASS | `require_cliente_access` retorna ADMIN para is_admin; endpoint continua protegido por autenticação |

## API2:2023 — Broken Authentication

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 4 | Tokens JWT têm expiração configurada | ✅ PASS | `app/core/security.py` — `ACCESS_TOKEN_EXPIRE_MINUTES = 30` |
| 5 | Refresh token rotation está implementado | ✅ PASS | Endpoint `/auth/refresh` com token type "refresh" |
| 6 | Rate limiting em endpoints de autenticação | ✅ PASS | `@rate_limit` em `/auth/login` e `/auth/refresh` |

## API3:2023 — Broken Object Property Level Authorization

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 7 | PATCH /me permite apenas campos permitidos | ✅ PASS | `UsuarioUpdate` schema restringe campos editáveis |
| 8 | Nenhum endpoint expõe campos sensíveis (password_hash) | ✅ PASS | Schemas usam `exclude=True` ou não incluem campos sensíveis |

## API5:2023 — Broken Function Level Authorization

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 9 | Endpoints admin requerem `is_admin` | ✅ PASS | `test_governance_routes.py` — `list_usuarios`, `patch_usuario`, `create_cliente` requerem admin |
| 10 | Endpoints de escrita requerem perfil no cliente | ✅ PASS | `require_cliente_perfil` em POST/PATCH/DELETE de associações e versões |
| 11 | APROVADOR pode aprovar/itens próprios | ✅ PASS | `assert_edit_permission` valida APROVADOR+ no cliente do item |

## API8:2023 — Security Misconfiguration

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 12 | CORS configurado com origins explícitas | ✅ PASS | `settings.ALLOWED_ORIGINS` — não é wildcard em produção |
| 13 | Headers de segurança presentes | ⚠️ PARTIAL | FastAPI default; HSTS não explicitamente configurado |
| 14 | Rate limiting em endpoints sensíveis | ✅ PASS | `/auth/login`, `/auth/refresh` têm `@rate_limit` |

## Resumo

- **PASS**: 13/14
- **PARTIAL**: 1/14 (HSTS)
- **FAIL**: 0/14

> Nota: HSTS é responsabilidade do reverse proxy (nginx/traefik) em ambiente on-premise. Não aplicável na camada de aplicação FastAPI.
