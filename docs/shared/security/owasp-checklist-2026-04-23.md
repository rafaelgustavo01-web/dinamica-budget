# OWASP API Security Checklist — S-04

Data: 2026-04-23
Responsável: Worker (Gemini 3.1)

## API1:2023 — Broken Object Level Authorization
- [x] Verificar se todos os endpoints com item_id validam ownership/acesso
  - [x] `/servicos/{servico_id}`: Validado em S-01/P0.1
  - [x] `/servicos/{item_id}/versoes`: Protegido em S-04/Task 2
  - [x] `/homologacao/aprovar`: Valida `servico.cliente_id == request.cliente_id`
- [x] Testar acesso a recursos de outro cliente
  - [x] `/busca/associacoes`: Protegido em S-04/Task 1

## API2:2023 — Broken Authentication
- [x] Verificar expiração de tokens
  - [x] Configurado: 30min access, 7d refresh.
- [x] Verificar refresh token rotation
  - [x] Hash armazenado no banco e invalidado no logout.

## API3:2023 — Broken Object Property Level Authorization
- [x] Verificar se PATCH /me permite apenas campos permitidos
  - [x] `UsuarioPatch` schema restringe a `nome`, `email`.

## API5:2023 — Broken Function Level Authorization
- [x] Verificar se endpoints admin requerem is_admin
  - [x] `get_current_admin_user` usado em `/admin/*` e `/usuarios/*`.
- [x] Verificar se APROVADOR pode aprovar
  - [x] `require_cliente_perfil(["APROVADOR", "ADMIN"])` aplicado em `/homologacao/aprovar`.

## API8:2023 — Security Misconfiguration
- [x] Verificar headers de segurança (CORS, HSTS)
  - [x] CORS configurado com `ALLOWED_ORIGINS` (não wildcard).
- [x] Verificar rate limiting em endpoints sensíveis
  - [x] Aplicado em `/auth/login` e `/auth/refresh` via `slowapi`.
