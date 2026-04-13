# CHANGELOG — Implementação de Pendências Validadas

> Gerado após validação profunda de 22 pontos do documento `ANALISE_PENDENCIAS_PROJETO.md`.
> Cada mudança é documentada com ANTES/DEPOIS para facilitar reversão se necessário.

---

## Resumo das Alterações

| # | Arquivo | Tipo | Descrição |
|---|---------|------|-----------|
| 1 | `app/schemas/auth.py` | BACKEND | Adicionados schemas `ProfileUpdateRequest` e `PasswordChangeRequest` |
| 2 | `app/repositories/usuario_repository.py` | BACKEND | Adicionados métodos `update_nome()` e `update_hashed_password()` |
| 3 | `app/services/auth_service.py` | BACKEND | Adicionados métodos `update_profile()` e `change_password()` |
| 4 | `app/api/v1/endpoints/auth.py` | BACKEND | Adicionados endpoints `PATCH /auth/me` e `POST /auth/trocar-senha` |
| 5 | `app/main.py` | BACKEND | Health check expandido com verificação de conectividade DB |
| 6 | `frontend/src/shared/types/contracts/auth.ts` | FRONTEND | Adicionadas interfaces `ProfileUpdateRequest` e `PasswordChangeRequest` |
| 7 | `frontend/src/shared/services/api/authApi.ts` | FRONTEND | Adicionados métodos `updateProfile()` e `changePassword()` |
| 8 | `frontend/src/features/profile/ProfilePage.tsx` | FRONTEND | Reescrito: formulário de edição de nome + troca de senha (substituiu read-only + ContractNotice) |
| 9 | `frontend/src/shared/components/FeedbackMessages.ts` | FRONTEND | Adicionadas mensagens de sucesso/erro para perfil e senha |
| 10 | `docs/ANALISE_PENDENCIAS_PROJETO.md` | DOC | Corrigidas imprecisões e itens marcados como concluídos |

---

## Detalhes por Arquivo

### 1. `app/schemas/auth.py`

**ANTES:** Continha apenas `LoginRequest`, `TokenResponse`, `RefreshRequest`, `UsuarioCreate`, `UsuarioResponse`, `PerfilClienteResponse`, `MeResponse`.

**DEPOIS:** Adicionados ao final do arquivo:
```python
class ProfileUpdateRequest(BaseModel):
    """Atualização parcial do perfil do próprio usuário."""
    nome: str = Field(min_length=2, max_length=200, description="Nome completo.")

class PasswordChangeRequest(BaseModel):
    """Troca de senha — exige senha atual para validação."""
    current_password: str = Field(description="Senha atual para verificação.")
    new_password: str = Field(min_length=8, description="Nova senha com mínimo de 8 caracteres.")
```

**REVERTER:** Remover as duas classes no final do arquivo.

---

### 2. `app/repositories/usuario_repository.py`

**ANTES:** Apenas `update_refresh_token()` existia para atualizações.

**DEPOIS:** Adicionados dois métodos após `update_refresh_token()`:
```python
async def update_nome(self, user_id, nome) -> Usuario | None
async def update_hashed_password(self, user_id, hashed_password) -> None
```

**REVERTER:** Remover os dois métodos.

---

### 3. `app/services/auth_service.py`

**ANTES:** Import de schemas não incluía os novos tipos. Apenas `login`, `refresh_token`, `logout`, `create_user`.

**DEPOIS:**
- Import atualizado: `from app.schemas.auth import LoginRequest, PasswordChangeRequest, ProfileUpdateRequest, TokenResponse, UsuarioCreate`
- Adicionados dois métodos ao final da classe `AuthService`:
  - `update_profile()` — atualiza nome via repository
  - `change_password()` — valida senha atual, atualiza hash, revoga refresh tokens

**REVERTER:** Remover os dois métodos e reverter o import para `from app.schemas.auth import LoginRequest, TokenResponse, UsuarioCreate`.

---

### 4. `app/api/v1/endpoints/auth.py`

**ANTES:** 6 endpoints: POST /login, POST /token, POST /refresh, POST /logout, GET /me, POST /usuarios.

**DEPOIS:**
- Import atualizado: adicionados `PasswordChangeRequest`, `ProfileUpdateRequest`
- 8 endpoints (+2 novos):
  - `PATCH /auth/me` — editar nome do próprio usuário
  - `POST /auth/trocar-senha` — trocar senha (exige senha atual, revoga refresh tokens)

**REVERTER:** Remover os dois novos endpoints (funções `update_profile` e `change_password`) e remover `PasswordChangeRequest`, `ProfileUpdateRequest` do import.

---

### 5. `app/main.py`

**ANTES:**
```python
@app.get("/health", tags=["health"])
async def health() -> dict:
    from app.ml.embedder import embedder
    return {"status": "ok", "embedder_ready": embedder.ready}
```

**DEPOIS:**
```python
@app.get("/health", tags=["health"])
async def health() -> dict:
    from app.ml.embedder import embedder
    from app.core.database import async_session_factory
    from sqlalchemy import text

    db_ok = False
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    status = "ok" if db_ok else "degraded"
    return {"status": status, "embedder_ready": embedder.ready, "database_connected": db_ok}
```

**REVERTER:** Substituir o bloco inteiro do health check pela versão anterior (3 linhas).

---

### 6. `frontend/src/shared/types/contracts/auth.ts`

**ANTES:** Terminava com `MeResponse`.

**DEPOIS:** Adicionadas ao final:
```typescript
export interface ProfileUpdateRequest { nome: string; }
export interface PasswordChangeRequest { current_password: string; new_password: string; }
```

**REVERTER:** Remover as duas interfaces.

---

### 7. `frontend/src/shared/services/api/authApi.ts`

**ANTES:** 5 métodos (login, refresh, getMe, logout, createUsuario).

**DEPOIS:** 7 métodos (+2):
```typescript
async updateProfile(payload: ProfileUpdateRequest) { ... }
async changePassword(payload: PasswordChangeRequest) { ... }
```

**REVERTER:** Remover os dois métodos e os imports `PasswordChangeRequest`, `ProfileUpdateRequest`.

---

### 8. `frontend/src/features/profile/ProfilePage.tsx`

**ANTES:** Componente read-only exibindo dados do usuário + `ContractNotice` listando endpoints faltantes.

**DEPOIS:** Reescrito completamente com:
- Seção "Identidade" (read-only, mantida)
- Seção "Perfis por cliente" (mantida)
- Formulário "Editar perfil" (react-hook-form + zod, campo nome)
- Formulário "Trocar senha" (react-hook-form + zod, 3 campos com confirmação)
- `ContractNotice` removido (não é mais necessário)

**REVERTER:** Restaurar o arquivo inteiro para a versão anterior (79 linhas, imports de `Chip, Paper, Stack, Typography` + `ContractNotice`).

---

### 9. `frontend/src/shared/components/FeedbackMessages.ts`

**ANTES:** Sem mensagens para perfil/senha.

**DEPOIS:** Adicionados:
- `successMessages.profileUpdated` e `successMessages.passwordChanged`
- `errorMessages.profileUpdate` e `errorMessages.passwordChange`

**REVERTER:** Remover as 4 linhas adicionadas.

---

### 10. `docs/ANALISE_PENDENCIAS_PROJETO.md`

**Correções:**
1. Seção 4 (ML): `compute_all_embeddings()` marcado como `[x]` COMPLETO (antes dizia "parcialmente stubbed" — validação provou que está 100% implementado)
2. Seção 6 (Backend): 3 endpoints faltantes marcados como `[x]` IMPLEMENTADOS (PATCH /me e POST /trocar-senha). GET/PATCH /preferencias marcado como adiado.
3. Seção 6: Health check expandido marcado como `[x]` IMPLEMENTADO
4. Seção 7 (Frontend): Perfil do Usuário marcado como `[x]` IMPLEMENTADO

---

## Validações Realizadas

### Itens do documento que foram CONFIRMADOS como VERDADEIROS:
- 3 endpoints realmente faltavam (PATCH /me, POST /trocar-senha, preferências)
- ProfilePage era realmente read-only
- Health check não verificava DB
- `compute_all_embeddings()` estava **COMPLETO** (documento tinha erro — dizia que era stub)
- Todas as queries raw (pg_trgm, pgvector) usam parâmetros — **seguras contra SQL injection**
- Rate limiting é in-memory (slowapi) — adequado para servidor único
- JWT usa HS256 — adequado para intranet

### Itens que NÃO precisaram de mudança:
- `/perfil/preferencias`: Adiado — sem necessidade imediata de preferências por usuário
- Migration nova: Não necessária (sem mudança de schema DB)
- Path aliases (tsconfig/vite): Melhoria de DX, não bloqueante — adiado
