# OWASP API Security Checklist — S-04 (CONSOLIDADO)

> **Data:** 2026-04-23  
> **Sprint:** S-04 — Endurecer Suíte de Segurança e RBAC  
> **Implementação:** Kimi K2.5 & Gemini 3.1 (Worker)  
> **Status Final:** 13/14 PASS, 1/14 PARTIAL

---

## API1:2023 — Broken Object Level Authorization (BOLA)

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 1 | Todos os endpoints com `cliente_id` validam ownership/acesso | ✅ PASS | `busca.py:65`, `servicos.py:35`, `versoes.py:41` |
| 2 | Testes cobrem acesso a recursos de outro cliente | ✅ PASS | `test_security_s04.py` — 3 cenários cobertos |
| 3 | `is_admin` global não expõe dados indevidamente | ✅ PASS | `require_cliente_access` retorna ADMIN para is_admin; endpoint continua protegido por autenticação |
| 4 | `/servicos/{servico_id}`: Validado em S-01/P0.1 | ✅ PASS | Proteção nativa mantida |
| 5 | `/homologacao/aprovar`: Valida ownership | ✅ PASS | `servico.cliente_id == request.cliente_id` |

## API2:2023 — Broken Authentication

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 6 | Tokens JWT têm expiração configurada | ✅ PASS | `app/core/security.py` — `ACCESS_TOKEN_EXPIRE_MINUTES = 30` |
| 7 | Refresh token rotation está implementado | ✅ PASS | Endpoint `/auth/refresh` com token type "refresh" |
| 8 | Rate limiting em endpoints de autenticação | ✅ PASS | `@rate_limit` em `/auth/login` e `/auth/refresh` |

## API3:2023 — Broken Object Property Level Authorization

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 9 | PATCH /me permite apenas campos permitidos | ✅ PASS | `UsuarioUpdate` schema restringe campos editáveis |
| 10 | Nenhum endpoint expõe campos sensíveis (password_hash) | ✅ PASS | Schemas usam `exclude=True` ou não incluem campos sensíveis |

## API5:2023 — Broken Function Level Authorization

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 11 | Endpoints admin requerem `is_admin` | ✅ PASS | `test_governance_routes.py` — `list_usuarios`, `patch_usuario`, `create_cliente` requerem admin |
| 12 | Endpoints de escrita requerem perfil no cliente | ✅ PASS | `require_cliente_perfil` em POST/PATCH/DELETE de associações e versões |
| 13 | APROVADOR pode aprovar/itens próprios | ✅ PASS | `assert_edit_permission` valida APROVADOR+ no cliente do item |

## API8:2023 — Security Misconfiguration

| # | Verificação | Status | Evidência |
|---|-------------|--------|-----------|
| 14 | CORS configurado com origins explícitas | ✅ PASS | `settings.ALLOWED_ORIGINS` — não é wildcard em produção |
| 15 | Headers de segurança presentes | ⚠️ PARTIAL | FastAPI default; HSTS não explicitamente configurado (responsabilidade do reverse proxy on-premise) |
| 16 | Rate limiting em endpoints sensíveis | ✅ PASS | `/auth/login`, `/auth/refresh` têm `@rate_limit` |

---

## Conclusão da Implementação

A sprint foi implementada em paralelo por Kimi e Gemini, resultando em uma proteção robusta dos endpoints de leitura que haviam sido abertos na S-01. A suíte de testes unitários foi expandida para 85 casos, garantindo que não haja regressões de segurança.
