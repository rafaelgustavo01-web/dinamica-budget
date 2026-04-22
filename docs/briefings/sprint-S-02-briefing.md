# Sprint S-02 Briefing — Revisado v1.1

> **Role:** Supervisor  
> **Date:** 2026-04-22  
> **Sprint:** S-02 — Arquitetura em Camadas  
> **Plano Técnico:** `docs/superpowers/plans/2026-04-22-arquitetura-camadas.md` (v2 revisado)  
> **Status:** REVISADO — pronto para execução

---

## Objetivo

Consolidar arquitetura em camadas estritas: **endpoint → service → repository**.  
Remover toda lógica de negócio e query SQL direta dos endpoints `auth`, `versoes`.  
Verificar e documentar estado atual de `servicos`.

---

## Escopo Detalhado

### 1. Refatorar `/auth/me` (GET + PATCH)
- Extrair construção de `MeResponse` (incluindo `UsuarioPerfil` + regra `is_admin`) para `AuthService.get_user_profile()`
- Endpoint deve ter apenas delegação: chamar service → retornar response model
- **Observação:** endpoints `/auth/trocar-senha` e `/auth/usuarios` já delegam corretamente; não alterar

### 2. Criar `VersaoService` e refatorar `/versoes`
- Extrair lógica de `list_versoes`, `criar_versao`, `ativar_versao` do endpoint
- Extrair validação de permissão (`_check_perfil`) para o service
- Endpoint deve ter apenas validação de entrada + chamada ao service
- **Nenhuma query SQL direta no endpoint**

### 3. Verificar `servicos.py`
- Confirmar que todos os endpoints delegam para `ServicoCatalogService`
- Inspecionar `ServicoCatalogService` quanto a queries SQL diretas em métodos públicos
- Documentar achados no walkthrough (não alterar service nesta sprint)

### 4. Testes
- Testes unitários para `AuthService.get_user_profile()` (caminho feliz, admin, not-found)
- Testes unitários para `VersaoService` (list, criar, ativar, permissão negada)
- Regressão: rodar suite de integração existente (`test_auth_access_control.py`, etc.)

---

## Critérios de Aceite (Mensuráveis)

- [ ] `auth.py` endpoints `/me` e `/me` PATCH contêm **≤ 5 linhas** cada (delegação + return)
- [ ] `versoes.py` endpoints contêm **≤ 8 linhas** cada (incluindo chamada de permissão via service)
- [ ] `AuthService` possui método `get_user_profile(user_id, db) → dict` coberto por testes
- [ ] `VersaoService` possui métodos `list_versoes`, `criar_versao`, `ativar_versao`, `assert_edit_permission`
- [ ] `pytest app/tests/unit/test_auth_service.py` — **ALL PASS**
- [ ] `pytest app/tests/unit/test_versao_service.py` — **ALL PASS**
- [ ] `pytest app/tests/integration/test_auth_access_control.py` — **ALL PASS** (regressão)
- [ ] `pytest app/tests/` — **ALL PASS** (suite completa)

---

## Dependências

| Sprint | Status | Vínculo |
|---|---|---|
| S-01 | `TESTED` | Autorização on-premise estabilizada; regras de perfil já validadas |

---

## Riscos e Mitigações

| Risco | Severidade | Mitigação |
|---|---|---|
| Quebrar API `/auth/me` usada pelo frontend | **Alta** | Preservar contrato `MeResponse`; teste de integração obrigatório antes de commit |
| Perda de controle transacional (flush/commit) | **Alta** | Manter padrão atual: service faz `flush`, endpoint não commita (request-scoped) |
| Sessão SQLAlchemy divergente (repo vs service) | **Média** | Service não recebe `db` nos métodos; repos injetados no `__init__` com a sessão do endpoint |
| Conflito com trabalho em andamento em `versoes.py` | **Média** | Verificar `git status` antes de iniciar; nenhum conflito detectado no momento |

---

## Notas para o Worker

1. **Padrão de injeção:** Service recebe repositories no `__init__`. Não passe `AsyncSession` nos métodos do service.
2. **Commit atômico por task:** Cada task do plano técnico termina com `git commit`. Não acumule mudanças.
3. **Se encontrar SQL direto em `ServicoCatalogService`:** Documente no walkthrough mas **não altere** — fora do escopo desta sprint.
4. **Rollback:** Se regressão falhar, `git revert` do commit da task problemática.
