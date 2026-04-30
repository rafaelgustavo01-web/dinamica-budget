# Mudanças — Ajustes no servidor (Yuri)

Resumo especialista das alterações enviadas nos commits `f5fbd35` e `3088089`.

Versão: 2026-04-29
Autor principal das mudanças: Yuri Geovane <yuri.martiniano@hotmail.com>

Objetivo deste documento
- Registrar, explicar e justificar as alterações aplicadas no repositório que visam preparar e estabilizar o servidor para o deploy; detalhar impactos, verificações, riscos e passos de rollback.

---

## Sumário rápido
- Commit `f5fbd35` — mensagem: "ajustes dentro do servidor realizado para o deploy" — alterações operacionais e de código para suportar deploy/execução em ambiente Windows/IIS/NSSM e para robustecer serviços backend.
- Commit `3088089` — merge contendo `f5fbd35` + outra branch; mensagem: "feat: Add architectural decision and brainstorm documents for Milestone 7 - Purchases and Negotiation" — agrega documentação de decisão arquitetural (M7), updates de testes e limpeza de configs locais.

---

## Metadados dos commits

- f5fbd35ddbd2c837a90342e42208f2ad614439d2
  - Autor: Yuri Geovane
  - Date: Wed Apr 29 17:15:20 2026 -0700
  - Mensagem: ajustes dentro do servidor realizado para o deploy
  - Estatísticas: 28 arquivos modificados, 840 inserções, 78 deleções

- 3088089043d7c2333c24e30365934c4c37fd1f91
  - Autor: Yuri Geovane (merge)
  - Date: Wed Apr 29 17:29:11 2026 -0700
  - Mensagem: feat: Add architectural decision and brainstorm documents for Milestone 7 - Purchases and Negotiation
  - Estatísticas: 76 arquivos modificados, 3345 inserções, 891 deleções

---

## Lista completa de arquivos alterados

### Commit `f5fbd35` (lista gerada de `git show --stat`)
- app/alembic/versions/021_proposta_acl.py
- app/backend/api/v1/endpoints/admin.py
- app/backend/api/v1/endpoints/servicos.py
- app/backend/core/dependencies.py
- app/backend/main.py
- app/backend/services/bcu_service.py
- app/deploy-dinamica.bat
- app/frontend/src/features/search/SearchPage.tsx
- app/frontend/src/shared/components/StatusBadge.tsx
- app/frontend/src/shared/services/api/apiClient.ts
- app/main.py
- app/scripts/api_test_8001.py
- app/scripts/api_test_auth.py
- app/scripts/check_db.py
- app/scripts/check_openapi_root.py
- app/scripts/db_inspect.py
- app/scripts/fix_iis.ps1
- app/scripts/import_test.py
- app/scripts/list_routes.py
- app/scripts/load_db.ps1
- app/scripts/servicos_check_noauth.py
- app/scripts/servicos_req.py
- openapi.json
- scripts/fix_nssm_dinamica.ps1
- scripts/restart_and_check.ps1
- scripts/test_search_endpoints.ps1
- start
- stop

Resumo do foco: migração leve, ajustes de dependências/initialization (`main.py`, `core/dependencies.py`), grande trabalho em `bcu_service.py`, e inclusão/ajuste de scripts operacionais e testes automáticos; atualização do `openapi.json`.

### Commit `3088089` (merge — lista parcial / highlights gerados de `git show --stat`)
- .agents/rules/graphify.md
- .agents/skills/semantic-memory/AGENTS.md
- .agents/workflows/graphify.md
- .claude/settings.local.json (ajuste)
- .gitignore (ajuste)
- app/backend/api/v1/endpoints/bcu.py
- app/backend/services/bcu_service.py
- app/backend/services/etl_service.py
- app/backend/services/histograma_service.py
- app/backend/services/proposta_export_service.py
- app/backend/services/proposta_versionamento_service.py
- app/backend/services/servico_catalog_service.py
- app/frontend/src/features/admin/AdminPage.tsx (alterado/limpeza)
- app/frontend/src/features/admin/UploadTcpoPage.tsx
- app/frontend/src/...(vários testes adicionados, pages e components)
- docs/shared/... (múltiplos arquivos de papéis, políticas e revisões técnicas)
- docs/sprints/multi/REVIEW-F2-multi-2026-04-29.md
- docs/sprints/multi/brainstorm-m7-claude-2026-04-29.md
- docs/sprints/multi/brainstorm-m7-codex-2026-04-29.md
- docs/sprints/multi/brainstorm-m7-synthesis-2026-04-29.md

Resumo do foco: merge que adiciona documentação de decisão arquitetural (M7), grande refatoração/ajustes em serviços backend (bcu/etl/histograma), remoção/limpeza de configurações locais sensíveis (`.claude/settings.json` removido), e adição/ampliação de testes de frontend e infraestrutura de documentação e regras de agentes.

---

## Análise técnica por área

1) Backend — inicialização, dependências e endpoints
- O commit `f5fbd35` atualiza `app/backend/main.py` e `app/backend/core/dependencies.py` — indica mudanças na forma como a aplicação é inicializada e em injeção de dependências/objetos compartilhados.
- Alterações em endpoints administrativos (`app/backend/api/v1/endpoints/admin.py`) sinalizam adição de rotinas de administração/diagnóstico para uso durante deploy.
- Impacto/Por que: permitir health-checks, rotinas de verificação/seed, simplificar autenticação de admin durante deploy e facilitar automação.
- Verificação: iniciar a API localmente e validar rotas admin; executar `python -m app.main` (ou o entrypoint usado) e checar `/openapi.json` e endpoints de saúde.

2) Serviços críticos e ETL
- `app/backend/services/bcu_service.py` recebeu alteração substancial (203 linhas no f5fbd35; total maior no merge). Espera-se: correções de fluxo, tratamento de erros, e compatibilidade com novos formatos do OpenAPI.
- `etl_service.py` e `histograma_service.py` também foram alterados no merge — normalmente sinaliza ajustes de performance, limpeza de dados e/ou preparação de payloads para exportação/importação.
- Impacto/Por que: garantir que transformações de dados rodem sem falhas no ambiente de produção e permitir reprocessamento em caso de inconsistência; compatibilizar exportadores e CPU tables.
- Verificação: rodar scripts de inspeção/ETL (`app/scripts/db_inspect.py`, `app/scripts/load_db.ps1`), checar logs e executar testes unitários (ver seção de verificação automática abaixo).

3) Migrations / Schema
- Pequena alteração em `app/alembic/versions/021_proposta_acl.py` — provavelmente ajuste de permissões/ACLs ou correção de migração menor.
- Impacto: migrar banco (ou aplicar patch) pode ser necessário antes do deploy; sempre rodar as migrations em staging antes de produção.

4) Scripts de operações e Windows/IIS support
- Novos/ajustados scripts: `app/scripts/fix_iis.ps1`, `scripts/fix_nssm_dinamica.ps1`, `scripts/restart_and_check.ps1`, `app/deploy-dinamica.bat`, `start`, `stop`.
- Motivo: tornar o deploy reproducível em servidores Windows (IIS/NSSM), automatizar reinstalação/serviço de background e checks pós-restart.
- Impacto: scripts alteram a forma de instalar/run do serviço — exigir permissão admin; recomendamos revisar `fix_iis.ps1` e `fix_nssm_dinamica.ps1` antes de executar em produção.

5) OpenAPI e Client
- `openapi.json` foi atualizado — contrato da API mudou; `app/frontend/src/shared/services/api/apiClient.ts` também sofreu ajustes.
- Motivo: nova/alterada surface API; clientes e automações precisam sincronizar com o novo `openapi.json`.
- Impacto: consumidores externos devem regenerar clients se usam geração automática; checar breaking changes.

6) Frontend e testes
- Pequenas correções de UI (`SearchPage.tsx`, `StatusBadge.tsx`) e adição/ajuste de testes (merge adicionou muitos testes `__tests__` no frontend).
- Motivo: garantir estabilidade do build frontend e aumentar cobertura de regressão.

7) Documentação e governança
- Commit `3088089` adicionou documentação arquitetural e materiais de decisão para Milestone 7 (`docs/sprints/multi/*`) e regras/skills em `.agents/`.
- Motivo: registrar decisão de abrir M7-0 para limpeza operacional antes de progredir; formalizar recomendações e sequência de sprints.

8) Configs sensíveis
- `.claude/settings.json` foi removido no merge e `.claude/settings.local.json` ajustado — isso é positivo (remoção de configs locais sensíveis do repositório).

---

## Motivações 
- Preparar o servidor e a aplicação para deploy ambiente Windows/IIS: scripts e ajustes no `main` e serviços para garantir a aplicação rode como serviço e recupere automaticamente.
- Robustez operacional: inclusão de scripts de checagem, inspeção de DB e testes de endpoint automatizados para diminuir intervenção manual.
- Compatibilidade com contrato API: atualização de `openapi.json` para refletir mudanças de contrato; ajuste do `apiClient` no frontend.
- Limpeza e governança: remoção de configurações locais comprometedoras e adição de documentação de decisão arquitetural para M7.

---
## Trechos de código implementado

Abaixo estão trechos representativos do código alterado/implementado nos commits indicados. Use-os como referência técnica rápida; cada bloco mostra a parte central aplicada para suportar deploy e operação.

- `app/backend/main.py` (startup / lifespan / health):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
  logger.info("startup_begin")

  # 0. Security: reject insecure SECRET_KEY before anything else starts
  from backend.core.config import validate_startup_config
  validate_startup_config(settings.SECRET_KEY)

  # 1. Register SQLAlchemy audit hooks (price + homologacao status changes)
  from backend.core.audit_hooks import register_audit_hooks
  register_audit_hooks()

  # 2. Load embedding model (blocks until ready — ~2-5s on first run)
  from backend.ml.embedder import embedder
  try:
    embedder.load(settings.EMBEDDING_MODEL_NAME)
  except Exception as exc:
    logger.error("embedding_model_load_failed", error=str(exc))

  # 3. Auto-create root user if configured and not already present
  if settings.ROOT_USER_EMAIL and settings.ROOT_USER_PASSWORD:
    from backend.core.database import async_session_factory
    from backend.core.security import hash_password
    from backend.models.usuario import Usuario
    import uuid as _uuid

    try:
      async with async_session_factory() as session:
        # check existing and create root user if missing
        ...
    except Exception as exc:
      logger.error("root_user_seed_failed", error=str(exc))

  logger.info("startup_complete")
  yield

  logger.info("shutdown")


@app.get("/health", tags=["health"])
async def health() -> dict:
  from backend.ml.embedder import embedder
  from backend.core.database import async_session_factory
  from sqlalchemy import text

  db_ok = False
  try:
    async with async_session_factory() as session:
      await session.execute(text("SELECT 1"))
      db_ok = True
  except Exception:
    pass

  return {
    "status": "ok" if db_ok else "degraded",
    "embedder_ready": embedder.ready,
    "database_connected": db_ok,
  }
```

- `app/backend/core/dependencies.py` (autenticação / current user):

```python
async def get_current_user(
  token: str = Depends(oauth2_scheme),
  db: AsyncSession = Depends(get_db),
):
  from backend.repositories.usuario_repository import UsuarioRepository

  try:
    payload = decode_token(token)
  except ValueError as exc:
    raise AuthenticationError(str(exc)) from exc

  if payload.get("type") != "access":
    raise AuthenticationError("Tipo de token inválido.")

  user_id_str = payload.get("sub")
  if not user_id_str:
    raise AuthenticationError("Token sem identificador de usuário.")

  repo = UsuarioRepository(db)
  user = await repo.get_by_id(UUID(user_id_str))
  if not user:
    raise AuthenticationError("Usuário não encontrado.")
  return user
```

- `app/backend/services/bcu_service.py` (parsing BCU — exemplo `_parse_mao_obra`):

```python
def _parse_mao_obra(ws, cabecalho_id: uuid.UUID, seq_counter: dict[str, int]) -> tuple[list[BcuMaoObraItem], list[BaseTcpo]]:
  # detect header row
  header_row_idx = 3
  for row_num, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True), start=1):
    if any(cell and "DESCRI" in str(cell).upper() for cell in row):
      header_row_idx = row_num
      break

  header_vals = next(ws.iter_rows(min_row=header_row_idx, max_row=header_row_idx, values_only=True))
  col_map = {str(c).strip().upper(): i for i, c in enumerate(header_vals) if c}

  # map and extract required columns, then build models
  items: list[BcuMaoObraItem] = []
  base_tcpo_items: list[BaseTcpo] = []
  for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
    desc = row[0] if row else None
    if not desc:
      continue
    seq_counter["MO"] = seq_counter.get("MO", 0) + 1
    codigo_origem = f"BCU-MO-{seq_counter['MO']:03d}"
    items.append(BcuMaoObraItem(...))
    base_tcpo_items.append(BaseTcpo(...))
  return items, base_tcpo_items
```

- `app/scripts/fix_iis.ps1` (trecho):

```powershell
# Disable WebDAV Publishing feature if installed
try {
  $feature = Get-WindowsFeature Web-DAV-Publishing -ErrorAction Stop
  if ($feature.Installed) {
    Remove-WindowsFeature Web-DAV-Publishing -Restart:$false -ErrorAction Stop
  }
} catch {
  Write-Warn "Could not check/remove Web-DAV: $_"
}

# Ensure Request Filtering does not deny PATCH/PUT verbs
& $appcmd set config "Default Web Site" -section:system.webServer/security/requestFiltering /-"verbs[@verb='PATCH']"
& $appcmd set config "Default Web Site" -section:system.webServer/security/requestFiltering /-"verbs[@verb='PUT']"

# Restart IIS
iisreset /restart
```

- `scripts/fix_nssm_dinamica.ps1` (trecho):

```powershell
$service = 'dinamica-backend'
$venvPython = 'C:\Dinamica-Budget\app\venv\Scripts\python.exe'
$appDir = 'C:\Dinamica-Budget\app'
$appParams = '-m uvicorn backend.main:app --host 127.0.0.1 --port 8000'

& $nssmCmd set $service Application $venvPython
& $nssmCmd set $service AppDirectory $appDir
& $nssmCmd set $service AppParameters $appParams
& $nssmCmd restart $service
```

- `app/deploy-dinamica.bat` (preflight excerpt):

```bat
REM Admin check
net session >nul 2>&1
if errorlevel 1 (
  echo Execute este script como Administrador.
  exit /b 1
)

REM Python check — instala 3.12 automaticamente se ausente ou versao incorreta
where python >nul 2>&1
if not errorlevel 1 (
  for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
)
```

- `app/frontend/src/shared/services/api/apiClient.ts` (client interceptors / token refresh):

```ts
// Normaliza trailing slash para GET /servicos
if (method === 'get') {
  if (/^\/?servicos($|\?|$)/.test(url) && !url.endsWith('/')) {
  config.url = url.replace(/^(\/)?servicos/, '/servicos/');
  }
}

async function refreshAccessToken() {
  const currentSession = readSessionTokens();
  if (!currentSession?.refreshToken) {
  clearSessionTokens();
  window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
  return null;
  }
  // POST /auth/refresh -> persist new tokens
}
```

- `app/alembic/versions/021_proposta_acl.py` (migração — criação de tabela + backfill):

```python
op.create_table(
  "proposta_acl",
  sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
  sa.Column("proposta_id", postgresql.UUID(as_uuid=True), nullable=False),
  sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
  sa.Column("papel", postgresql.ENUM("OWNER", "EDITOR", "APROVADOR", name="proposta_papel_enum"), nullable=False),
  schema="operacional",
)

# Backfill: criador de cada proposta vira OWNER
op.execute("""
  INSERT INTO operacional.proposta_acl (id, proposta_id, usuario_id, papel, created_by, created_at, updated_at)
  SELECT gen_random_uuid(), id, criado_por_id, 'OWNER'::proposta_papel_enum, criado_por_id, NOW(), NOW()
  FROM operacional.propostas
  WHERE criado_por_id IS NOT NULL
""")
```

---

## Riscos conhecidos e mitigação
- Execução de scripts PowerShell com permissões elevadas: risco de alteração do IIS/NSSM — mitigação: revisar scripts linha-a-linha em ambiente staging e ter snapshot/backup do servidor.
- Mudanças em `openapi.json`: breaking changes para clientes — mitigação: versionamento da API, comunicar consumidores e regenerar clients.
- Alterações em serviços ETL/histograma: risco de perda de dados se mal configurado — mitigação: rodar em modo dry-run, logs verbose e checar consistência antes de habilitar processamento em produção.

---