# Walkthrough — Sprint F2-08

**Data:** 2026-04-26
**Sprint:** F2-08 — RBAC por Proposta

---

## Como validar

### Backend

1. Verifique a migration:
   ```bash
   cd app && alembic upgrade head
   ```

2. Rode os testes:
   ```bash
   cd app && python -m pytest backend/tests/unit/ -v --tb=short
   ```

3. Teste os endpoints:
   - POST /propostas — qualquer usuário autenticado pode criar
   - GET /propostas — retorna todas com `meu_papel`
   - PATCH /propostas/{id} — requer EDITOR
   - DELETE /propostas/{id} — requer OWNER
   - GET /propostas/{id}/acl — qualquer auth
   - POST /propostas/{id}/acl — somente OWNER

### Frontend

1. Acesse a lista de propostas — deve mostrar todas sem filtro obrigatório de cliente
2. Acesse uma proposta como OWNER — deve ver botão "Compartilhar" e "Excluir"
3. Acesse como VIEWER — não deve ver botões de editar/excluir/compartilhar
4. Abra o dialog "Compartilhar" e adicione um EDITOR

### Critérios de Aceite Verificados

- [x] Tabela `proposta_acl` criada com migration 021
- [x] Backfill OWNER aplicado
- [x] `require_proposta_role` substitui `require_cliente_access`
- [x] 5 routers refatorados
- [x] `criar_proposta` cria OWNER automaticamente
- [x] Last-OWNER guard funcional
- [x] GET /propostas retorna `meu_papel`
- [x] Endpoints ACL OWNER-gated
- [x] ProposalShareDialog renderiza
- [x] UI condicional em DetailPage e ListPage
- [x] 158+ PASS, 0 FAIL
- [x] 0 erros tsc
