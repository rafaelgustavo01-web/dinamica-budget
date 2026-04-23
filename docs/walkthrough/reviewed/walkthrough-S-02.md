# Walkthrough — Sprint S-02

> **Sprint:** S-02 — Arquitetura em Camadas  
> **Worker:** Kimi K2.5  
> **Data:** 2026-04-22  
> **Status:** TESTED

---

## O que foi feito

### Task 1: AuthService — Extract Profile Logic
- Adicionado `AuthService.get_user_profile(user_id)` que retorna dict pronto para `MeResponse`
- Inclui lógica de perfis (`UsuarioPerfil`) e regra `is_admin → perfil ADMIN wildcard`
- Arquivo: `app/services/auth_service.py`
- Testes: `app/tests/unit/test_auth_service.py` (3 casos)

### Task 2: auth.py Endpoints — Delegate to AuthService
- `/me` (GET): reduzido para 4 linhas (instancia service + chama get_user_profile + retorna MeResponse)
- `/me` (PATCH): atualiza perfil via service e reconstrói resposta via get_user_profile
- Removido SQL direto (`select(UsuarioPerfil)`), import `UsuarioPerfil`, import `PerfilClienteResponse`, import `select`
- Arquivo: `app/api/v1/endpoints/auth.py`

### Task 3: VersaoService — Create Service
- Criado `VersaoService` com métodos:
  - `list_versoes(item_id)` — lista versões com validação de existência do item
  - `criar_versao(item_id, current_user_id, db)` — cria nova versão clonando composição da ativa
  - `ativar_versao(versao_id, current_user_id, db)` — ativa versão e desativa outras
  - `assert_edit_permission(item_id, current_user, db)` — valida APROVADOR/ADMIN no cliente
- Arquivo: `app/services/versao_service.py`
- Testes: `app/tests/unit/test_versao_service.py` (5 casos)

### Task 4: versoes.py Endpoints — Delegate to VersaoService
- `list_versoes`: delega para `VersaoService.list_versoes()`
- `criar_versao`: valida permissão via `assert_edit_permission()` + delega criação
- `ativar_versao`: resolve versão via repo (sem SQL direto), valida permissão, ativa
- Removido toda lógica de negócio e SQL direto do endpoint
- Arquivo: `app/api/v1/endpoints/versoes.py`

### Task 5: servicos.py — Verify Delegation
- Verificado que todos os 4 endpoints delegam para `ServicoCatalogService`
- Sem alterações necessárias (já estava limpo)

### Task 6: Regression Suite
- Suite unitária: **74/74 PASS**
- Testes de integração: não executados por indisponibilidade do PostgreSQL local (erro de conexão asyncpg)
- Teste de segurança P0 atualizado para reconhecer `assert_edit_permission` como verificação válida de autorização

---

## Decisões Técnicas

1. **Padrão de injeção:** Service recebe repositories no `__init__`. Não recebe `AsyncSession` nos métodos.
2. **Snapshot de dados:** `MeResponse` construído a partir de dados do service, não query direta.
3. **Autorização no service:** `assert_edit_permission` movido para `VersaoService` para manter endpoints enxutos.
4. **Transação:** Mantido request-scoped. Service faz `flush`, endpoint não commita.

---

## Métricas

| Métrica | Valor |
|---|---|
| Arquivos modificados/criados | 6 |
| Commits atômicos | 6 |
| Testes unitários novos | 8 (3 auth + 5 versao) |
| Testes unitários totais passando | 74/74 |
| Endpoints refatorados | 5 (2 auth + 3 versoes) |
| Services criados | 1 (VersaoService) |
| SQL direto removido de endpoints | 3 queries |

---

## Notas para QA

- Nenhuma migration de banco necessária (sem alteração de schema)
- APIs `/auth/me` e `/versoes/*` mantêm contratos inalterados (response models iguais)
- Testes de integração recomendados quando PostgreSQL local estiver disponível
- Verificar se `ServicoCatalogService` ainda tem SQL em métodos privados (documentado como débito técnico aceitável fora do escopo)
