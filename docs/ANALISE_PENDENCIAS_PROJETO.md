# Dinâmica Budget — O que Falta para Finalizar o Projeto

> **Data da Análise:** Abril 2026  
> **Escopo:** Levantamento completo de tudo que falta para o sistema ir para produção  
> **Estado Atual:** ~95% backend, ~85% frontend, infraestrutura de produção inexistente  
> **Ambiente de Produção:** **Windows Server** na intranet — sem Docker, servidor com recursos limitados, **firewall bloqueia internet** (GitHub, etc.)  
> **Estratégia de Deploy:** Scripts `.bat` / PowerShell — cópia local de arquivos, sem dependência de internet

---

## Resumo Executivo

O **Dinâmica Budget** é um sistema corporativo de **intranet** para orçamentação inteligente na construção civil, com busca semântica (pgvector + SentenceTransformers), governança RBAC, workflow de homologação e catálogo TCPO. O backend FastAPI + PostgreSQL 16 está **praticamente completo**. O frontend React 19 + MUI 7 está ~85% implementado.

**O que falta:**
- Backend: **3 endpoints faltantes** (editar perfil, trocar senha, preferências) — todo o resto está 100% implementado
- Frontend: **perfil é read-only** (falta form de edição e troca de senha), **permissões é placeholder**
- Infraestrutura: zero — nada configurado no Windows Server de produção
- Testes: infraestrutura existe mas quase sem cobertura
- ML: modelo funcional mas precisa de otimização (modelo em inglês, alto consumo de RAM)
- Documentação: parcial, falta guia de operação e manual do usuário

> **⚠️ Contexto Real:** Servidor Windows na intranet, recursos limitados, sem equipe de infra dedicada. **Firewall bloqueia internet (GitHub, ChatGPT, etc.)** — todo deploy é feito por cópia local de arquivos. Observabilidade mínima.

---

## 1. INFRAESTRUTURA E DEPLOY (Windows Server)

### Criticidade: 🔴 BLOQUEADOR — nada funciona sem isso

O Windows Server está vazio. Tudo precisa ser instalado e configurado.

### Instalação do Servidor

#### Software necessário:
- [ ] **PostgreSQL 16 para Windows** — instalar via installer oficial (postgresql.org/download/windows/)
  - Extensões necessárias: `pgvector` e `pg_trgm`
  - pgvector para Windows: baixar binário pré-compilado em máquina com internet → trazer via pendrive/rede
  - pg_trgm já vem embutido no PostgreSQL
- [ ] **Python 3.12 para Windows** — instalar via installer offline (trazer via pendrive), marcar "Add to PATH"
  - Criar virtualenv para o projeto: `python -m venv C:\apps\dinamica-budget\venv`
- [ ] ~~Node.js~~ — **NÃO precisa no servidor**. Build do frontend é feito na máquina de dev e copiado pronto
- [ ] **NSSM** (Non-Sucking Service Manager) — para rodar o FastAPI como Windows Service
  - Baixar de https://nssm.cc — **trazer o .zip via pendrive/rede** (servidor sem internet)
  - Alternativa: `sc.exe create` com wrapper, ou PowerShell `New-Service`

#### Configuração de rede:
- [ ] IP fixo na rede interna
- [ ] Hostname/DNS interno (ex: `budget.empresa.local` no DNS da rede)
- [ ] Windows Firewall: liberar porta 443 (HTTPS) e 5432 (PostgreSQL, apenas localhost)
- [ ] Certificado TLS auto-assinado para HTTPS (protege JWT tokens na rede)
  - Gerar via PowerShell: `New-SelfSignedCertificate` ou via OpenSSL para Windows

#### Estrutura de diretórios no servidor:
```
C:\apps\dinamica-budget\
├── backend\           ← código Python (copiado da máquina de dev)
├── frontend\          ← build estático do React (build feito na máquina de dev, copiado pronto)
├── venv\              ← virtualenv Python
├── logs\              ← logs da aplicação
├── backups\           ← dumps do PostgreSQL
├── scripts\           ← scripts .bat e .ps1 de deploy/manutenção
└── .env               ← variáveis de ambiente (permissão restrita via NTFS)
```

### Deploy via Scripts (.bat / PowerShell)

#### Script principal de deploy (`deploy.ps1`):

> **IMPORTANTE:** O servidor NÃO tem acesso à internet. O código e o build do frontend devem ser preparados na máquina de desenvolvimento e copiados para o servidor via rede interna ou pendrive.

**Na máquina de dev (com internet):**
```powershell
# preparar-deploy.ps1 — Rodar na máquina do desenvolvedor
$source = "C:\GIT\Dinamica-Budget"
$deployPkg = "C:\deploy-package"

# 1. Build do frontend
Set-Location "$source\frontend"
npm install
npm run build

# 2. Montar pacote de deploy
New-Item -ItemType Directory -Path $deployPkg -Force
Copy-Item -Path "$source\app" -Destination "$deployPkg\backend\app" -Recurse -Force
Copy-Item -Path "$source\alembic" -Destination "$deployPkg\backend\alembic" -Recurse -Force
Copy-Item -Path "$source\alembic.ini" -Destination "$deployPkg\backend\" -Force
Copy-Item -Path "$source\requirements.txt" -Destination "$deployPkg\backend\" -Force
Copy-Item -Path "$source\frontend\dist\*" -Destination "$deployPkg\frontend\" -Recurse -Force

Write-Host "Pacote pronto em $deployPkg — copiar para o servidor via rede/pendrive" -ForegroundColor Green
```

**No servidor (sem internet):**
```powershell
# deploy.ps1 — Rodar no Windows Server
param(
    [string]$PackagePath = "D:\deploy-package",  # pendrive ou pasta de rede
    [switch]$SkipMigrations
)

$ErrorActionPreference = "Stop"
$appRoot = "C:\apps\dinamica-budget"

Write-Host "=== DEPLOY DINAMICA BUDGET ===" -ForegroundColor Cyan

# 1. Copiar backend
Write-Host "Copiando backend..." -ForegroundColor Yellow
Copy-Item -Path "$PackagePath\backend\*" -Destination "$appRoot\backend\" -Recurse -Force

# 2. Copiar frontend (já buildado)
Write-Host "Copiando frontend..." -ForegroundColor Yellow
Copy-Item -Path "$PackagePath\frontend\*" -Destination "$appRoot\frontend\" -Recurse -Force

# 3. Instalar/atualizar dependências Python (offline — ver nota abaixo)
& "$appRoot\venv\Scripts\pip.exe" install -r "$appRoot\backend\requirements.txt" --no-index --find-links "$PackagePath\wheels" --quiet
if ($LASTEXITCODE -ne 0) { throw "pip install falhou" }

# 4. Rodar migrations
if (-not $SkipMigrations) {
    Set-Location "$appRoot\backend"
    & "$appRoot\venv\Scripts\alembic.exe" upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Alembic migrations falharam" }
}

# 5. Reiniciar serviço
Restart-Service -Name "DinamicaBudget" -Force
Write-Host "=== DEPLOY CONCLUIDO ===" -ForegroundColor Green
```

> **pip offline:** Na máquina de dev, gerar pacotes wheel: `pip download -r requirements.txt -d C:\deploy-package\wheels`. Copiar a pasta `wheels` junto com o pacote de deploy. O script usa `--no-index --find-links` para instalar sem internet.

#### Alternativa .bat (`deploy.bat`):
```batch
@echo off
echo === DEPLOY DINAMICA BUDGET ===

set PACKAGE=D:\deploy-package
set APPROOT=C:\apps\dinamica-budget

echo Copiando backend...
xcopy /s /y "%PACKAGE%\backend\*" "%APPROOT%\backend\"
if errorlevel 1 (echo ERRO: copia backend falhou & pause & exit /b 1)

echo Copiando frontend...
xcopy /s /y "%PACKAGE%\frontend\*" "%APPROOT%\frontend\"
if errorlevel 1 (echo ERRO: copia frontend falhou & pause & exit /b 1)

echo Instalando dependencias Python (offline)...
call %APPROOT%\venv\Scripts\pip.exe install -r %APPROOT%\backend\requirements.txt --no-index --find-links "%PACKAGE%\wheels" --quiet
if errorlevel 1 (echo ERRO: pip install falhou & pause & exit /b 1)

echo Rodando migrations...
cd /d %APPROOT%\backend
call %APPROOT%\venv\Scripts\alembic.exe upgrade head
if errorlevel 1 (echo ERRO: migrations falharam & pause & exit /b 1)

net stop DinamicaBudget
net start DinamicaBudget

echo === DEPLOY CONCLUIDO ===
pause
```

#### Registrar FastAPI como Windows Service (NSSM):
```powershell
# Instalar NSSM e registrar serviço (executar uma vez)
nssm install DinamicaBudget "C:\apps\dinamica-budget\venv\Scripts\uvicorn.exe"
nssm set DinamicaBudget AppParameters "app.main:app --host 0.0.0.0 --port 8000 --workers 1"
nssm set DinamicaBudget AppDirectory "C:\apps\dinamica-budget\backend"
nssm set DinamicaBudget AppEnvironmentExtra "PYTHONPATH=C:\apps\dinamica-budget\backend"
nssm set DinamicaBudget AppStdout "C:\apps\dinamica-budget\logs\app.log"
nssm set DinamicaBudget AppStderr "C:\apps\dinamica-budget\logs\error.log"
nssm set DinamicaBudget AppRotateFiles 1
nssm set DinamicaBudget AppRotateBytes 10485760
nssm start DinamicaBudget
```

### Servir o Frontend (opções)

- **Opção A — IIS (já vem no Windows Server):**
  - Configurar site IIS apontando para `C:\apps\dinamica-budget\frontend\`
  - Configurar URL Rewrite para proxy reverso da API (`/api/*` → `http://localhost:8000`)
  - HTTPS via certificado auto-assinado no IIS

- **Opção B — Uvicorn serve tudo:**
  - Montar frontend estático via FastAPI `StaticFiles` middleware
  - Mais simples, mas menos performante para arquivos estáticos

- **Opção C — Nginx para Windows:**
  - Nginx for Windows funciona, mas IIS é mais natural em Windows Server

### Backup do Banco de Dados

#### Script de backup (`backup-db.ps1`):
```powershell
$date = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupDir = "C:\apps\dinamica-budget\backups"
$pgDump = "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"

& $pgDump -U postgres -d dinamica_budget -F c -f "$backupDir\dinamica_$date.dump"

# Manter apenas últimos 30 backups
Get-ChildItem "$backupDir\*.dump" | Sort-Object CreationTime -Descending | Select-Object -Skip 30 | Remove-Item -Force

Write-Host "Backup concluído: dinamica_$date.dump"
```

#### Agendar backup diário (Task Scheduler):
```powershell
# Registrar tarefa agendada para backup diário às 2h
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\apps\dinamica-budget\scripts\backup-db.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "DinamicaBudget-Backup" -Action $action -Trigger $trigger -RunLevel Highest -User "SYSTEM"
```

### Observabilidade (Mínima — servidor com recursos limitados)

> ⚠️ Stack de monitoramento pesada (ELK, Prometheus+Grafana) **NÃO recomendada** para este cenário.

- [ ] **Logs**: NSSM já redireciona stdout/stderr para arquivos com rotation automática
  - structlog já gera JSON — basta consultar os arquivos quando necessário
  - `Get-Content C:\apps\dinamica-budget\logs\app.log -Tail 100` para ver últimas linhas
- [ ] **Health check**: Task Scheduler rodando script a cada 5 min:
  ```powershell
  # health-check.ps1
  try {
      $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10
      if ($response.StatusCode -ne 200) { throw "Status: $($response.StatusCode)" }
  } catch {
      Restart-Service DinamicaBudget
      Add-Content "C:\apps\dinamica-budget\logs\health.log" "$(Get-Date) - RESTART: $_"
  }
  ```
- [ ] **Monitoramento de disco**: `Get-PSDrive C | Select-Object Used, Free` via Task Scheduler + alerta se disco > 85%
- [ ] **pg_stat_statements** no PostgreSQL para queries lentas (embutido, sem custo extra)

---

## 2. BANCO DE DADOS (PostgreSQL)

### Criticidade: 🟡 ALTA

O sistema tem 11 migrations, modelos complexos com pgvector, pg_trgm e relações multi-tenant.

### Performance e Tuning
- [ ] Analisar e otimizar queries — especialmente `fuzzy_search_scoped()` (raw SQL com pg_trgm)
- [ ] Verificar e ajustar índices GIN para busca textual
- [ ] Otimizar índice IVFFlat/HNSW para pgvector (atualmente sem índice vetorial — scan sequencial)
- [ ] Ajustar `shared_buffers`, `work_mem`, `effective_cache_size` para o workload
- [ ] Query plan analysis nas buscas mais frequentes
- [ ] Configurar `pg_stat_statements` para tracking de queries lentas

### Integridade e Modelagem
- [ ] Revisar modelagem de dados vs regras de negócio (documento `Prompt Modelagem.md` aponta conflitos)
- [ ] Resolver dual FK na `composicao_tcpo` (servico_pai_id legacy + versao_id novo)
- [ ] Validar constraints de integridade referencial
- [ ] Revisar soft-delete strategy (deleted_at em servico_tcpo)
- [ ] Planejar migration 012+ para cleanup da estrutura legada

### Operações
- [ ] Plano de migração de dados (se existir base legada de orçamentos)
- [ ] Seed data: categorias, serviços TCPO base
- [ ] Anonimização de dados para ambiente de testes
- [ ] Monitorar crescimento de tabelas (especialmente `tcpo_embeddings` com Vector(384))

---

## 3. SEGURANÇA DA APLICAÇÃO

### Criticidade: 🟡 ALTA

O sistema lida com **dados de orçamento corporativo, CNPJ de clientes, credenciais de usuários**. Segurança básica está razoável, mas falta hardening de produção.

### Auditoria Necessária
- [ ] Penetration testing na API (OWASP Top 10)
- [ ] Revisão de code security (SAST — Bandit para Python, ESLint security rules)
- [ ] Análise de dependências vulneráveis (`pip audit`, `npm audit`)
- [ ] Validar escape de SQL nas queries raw (pg_trgm e pgvector usam SQL parcialmente raw)
- [ ] Testar CSRF, XSS, injection vectors no frontend

### Melhorias de Segurança Pendentes
- [ ] **Token blacklist/revocation**: Atualmente usa hash de refresh token — adequado para intranet
- [ ] **Secret rotation**: Documentar procedimento manual (trocar SECRET_KEY no `.env` + reiniciar serviço — aceitável em intranet com janela de manutenção)
- [ ] **JWT HS256**: Adequado para sistema de intranet
- [ ] **Audit log**: Implementado no service layer — verificar completude em todas as operações sensíveis
- [ ] **`.env` protegido**: Permissão NTFS restrita (apenas conta do serviço pode ler)

---

## 4. MACHINE LEARNING / BUSCA SEMÂNTICA

### Criticidade: 🟡 ALTA

O sistema usa ML para busca semântica, mas a implementação atual é básica e precisa de otimização.

### Otimização do Modelo
- [ ] Avaliar se `all-MiniLM-L6-v2` (384 dims) é o melhor modelo para textos em **português** de construção civil
  - Modelos alternativos: `paraphrase-multilingual-MiniLM-L12-v2`, `sentence-transformers/LaBSE`
  - Ou fine-tuning de modelo com corpus TCPO
- [ ] Benchmark de precision/recall da busca semântica vs fuzzy
- [ ] Otimizar thresholds (semantic: 0.65, fuzzy: 0.85) com base em dados reais de uso
- [ ] Implementar índice HNSW no pgvector (atualmente sem índice — scan O(n))

### Pipeline de Embeddings
- [x] ~~`compute_all_embeddings()` está parcialmente stubbed no service~~ — **COMPLETO** (compute_all_missing com batch processing implementado)
- [ ] Estratégia de re-embedding quando modelo atualizar
- [ ] Batch processing otimizado para carga inicial de catálogo TCPO

### Busca Inteligente — Evolução
- [ ] Implementar **re-ranking** (cross-encoder) nos top-K resultados
- [ ] Avaliar hybrid search (combinar score fuzzy + semântico com pesos ajustáveis)
- [ ] Feedback loop: usar dados de `associacao_inteligente.frequencia_uso` para melhorar ranking

### Recursos Computacionais (servidor limitado)
- [ ] Modelo torch CPU roda em ~2-5s para carga, inference ~50-200ms
- [ ] **Prioridade**: Converter modelo para ONNX Runtime (reduz RAM de ~2GB para ~500MB, inference 2-5x mais rápida)
  - ONNX Runtime funciona nativamente em Windows sem problemas
- [ ] Cache de embeddings frequentes (dicionário em memória, sem Redis)

---

## 5. TESTES E QUALIDADE

### Criticidade: 🟡 ALTA

**Não existem testes automatizados funcionando**. Há infraestrutura de teste (conftest.py, pytest.ini) mas falta cobertura.

### Backend — Testes
- [ ] Testes unitários para todos os services (auth, busca, homologacao, catalog, embedding_sync)
- [ ] Testes unitários para repositories (mocking de session)
- [ ] Testes de integração end-to-end (API endpoints com banco de testes)
- [ ] Testes do fluxo de busca 4-fases completo
- [ ] Testes de RBAC: verificar que cada endpoint rejeita acessos indevidos
- [ ] Testes de edge cases: dados nulos, unicode, SQL injection attempts
- [ ] Cobertura mínima target: **80%** nos services e endpoints
- [ ] Fixtures de dados: catálogo TCPO mock, clientes, usuários com perfis variados

### Frontend — Testes
- [ ] Configurar Vitest + React Testing Library
- [ ] Testes de componentes (DataTable, StatusBadge, ConfirmationDialog)
- [ ] Testes de hooks (useAuth, useFeedback)
- [ ] Testes de fluxos (login, busca, homologação)
- [ ] Testes de permissão (ProtectedRoute, PermissionGuard)

### E2E / Integração
- [ ] Configurar Playwright (já existe pasta `output/playwright/`)
- [ ] Fluxos críticos: Login → Busca → Associação → Homologação → Aprovação
- [ ] Teste de responsividade (desktop, tablet)
- [ ] Teste de acessibilidade automatizado (axe-core)

### Testes de Performance
- [ ] Load testing da API (Locust, k6)
- [ ] Benchmark da busca semântica com catálogo grande (10K+, 100K+ serviços)
- [ ] Stress test do PostgreSQL com queries concorrentes

---

## 6. BACKEND — IMPLEMENTAÇÕES PENDENTES

### Criticidade: � MÉDIA — Quase tudo pronto

> **Estado real:** Backend está ~95% completo. Todos os services, repositories e endpoints principais estão **100% implementados**. Não há stubs ou placeholders. O que falta são 3 endpoints menores.

### ✅ Já Implementado e Funcional
- `criar_associacao()` em `busca_service.py` — **COMPLETO**
- `get_versao_ativa()` em `servico_tcpo_repository.py` — **COMPLETO**
- `compute_all_embeddings()` em `servico_catalog_service.py` — **COMPLETO** (delega para embedding_sync_service)
- `create_servico()` em `servico_catalog_service.py` — **COMPLETO**
- `embedding_sync_service.py` — **COMPLETO** (sync_create_or_update, sync_delete, compute_all_missing)
- Todos os 8 arquivos de endpoints — **ZERO stubs/placeholders**

### Endpoints Faltantes (3 endpoints) — ✅ IMPLEMENTADOS
- [x] `PATCH /auth/me` — editar perfil próprio (nome)
- [x] `POST /auth/trocar-senha` — alterar senha (exige senha atual, revoga refresh tokens)
- [ ] `GET/PATCH /perfil/preferencias` — preferências do usuário (adiado — sem necessidade imediata)

### Melhorias Técnicas
- [ ] Completar transição de versionamento de composições (migration 012+ para remover FK legado)
- [ ] Implementar paginação cursor-based para tabelas grandes
- [ ] Cache in-memory (`lru_cache` / `cachetools`) para catálogo TCPO em vez de Redis
- [ ] Background tasks com **FastAPI BackgroundTasks** (nativo, sem Celery):
  - Re-cálculo de embeddings em batch
  - Exportação de relatórios pesados
- [x] ~~Health check expandido (verificar DB, modelo ML, disk space)~~ — **IMPLEMENTADO**: /health agora verifica DB + embedder

---

## 7. FRONTEND — IMPLEMENTAÇÕES PENDENTES

### Criticidade: 🟡 MÉDIA

Frontend está ~85% completo. A maioria dos módulos está funcional.

### ✅ Módulos Completos e Funcionais
- **Admin** — painel de embeddings + status do sistema
- **Associações** — CRUD completo, filtragem por cliente, paginação
- **Auth** — LoginPage + AuthProvider
- **Clientes** — operações administrativas completas
- **Composições** — gestão de composições
- **Dashboard** — métricas (contagem de serviços, homologações pendentes)
- **Homologação** — workflow de aprovação
- **Relatórios** — relatórios tabulados (serviços + homologação), export CSV
- **Busca** — UI completa com validação, resultados, fluxo de associação
- **Serviços** — catálogo com listagem/filtro
- **Usuários** — gestão de usuários com RBAC

### Features Incompletas (1 módulo)
- [x] ~~**Perfil do Usuário**: Atualmente read-only~~ — **IMPLEMENTADO**: formulário de edição de nome + troca de senha com validação
- [ ] **Permissões**: **Placeholder** — mostra aviso que RBAC está centralizado em Usuários (pode permanecer assim se a decisão de negócio confirmar)

### Melhorias de UX
- [ ] Skeleton loaders em vez de spinners (melhor perceived performance)
- [ ] Highlight de termos buscados nos resultados de busca
- [ ] Tree view para composições (em vez de tabela plana)
- [ ] Ordenação de colunas nas tabelas
- [ ] Filtros avançados em todas as listagens (data, status, tipo)
- [ ] Ações em batch (aprovar múltiplos itens, deletar múltiplos)
- [ ] Undo em ações destrutivas (rejeitar, deletar)
- [ ] Notificações in-app (badge no sidebar para itens pendentes)

### Qualidade
- [ ] Configurar path aliases (`@/` → `src/`)
- [ ] Configurar Vitest + testes de componentes
- [ ] Acessibilidade: ARIA labels, keyboard navigation completa
- [ ] PWA support (service worker para uso offline parcial — consulta de catálogo)

---

## 8. UX/UI — DESIGN PENDENTE

### Criticidade: 🟡 MÉDIA

O design system existe e é bem documentado, mas há gaps de UX.

### Design de Funcionalidades Novas
- [ ] Fluxo de relatórios customizados (wireframes + protótipos)
- [ ] Visualização de composições em árvore (BOM tree)
- [ ] Dashboard avançado com gráficos e analytics
- [ ] Onboarding de novos usuários (tutorial / walkthrough)

### Revisão de UX
- [ ] Teste de usabilidade com usuários reais (construção civil — perfil não-técnico)
- [ ] Simplificar fluxo de busca → associação → homologação (workflow principal)
- [ ] Melhorar feedback visual do sistema de busca 4-fases
- [ ] Revisão para telas menores (tablet — intranet geralmente desktop, mas tablets são usados em obra)

### Acessibilidade
- [ ] Audit de contraste (WCAG AA já documentado, mas precisa validação real)
- [ ] Focus states visíveis
- [ ] Navegação por teclado em todos os fluxos

---

## 9. DECISÕES DE NEGÓCIO PENDENTES

### Criticidade: 🟡 MÉDIA-ALTA — Bloqueiam implementação de features

O documento `docs/Prompt Modelagem.md` aponta **conflitos entre regras de negócio e a modelagem implementada valide esse ponto com foco na regra ne negocio oque der para seguir adiante que não comprometa muito a modelage msiga oque precisar informa crie perguntas aqui, deixe um super usuario para poder adicionar permição a usuarios para poder editar o banco de dados**.

### Decisões Necessárias
- [ ] **Relacionamento Usuário ↔ Cliente**: Modelo atual tem vínculo direto via RBAC (`permissao_operacional`), mas regra de negócio diz "sem relação direta" — qual é correto?
- [ ] **Página de Permissões**: Manter centralizada em Usuários ou criar módulo separado?
- [ ] **Workflow de homologação**: Validar se fluxo PENDENTE → APROVADO/REPROVADO está completo ou precisa de estados intermediários
- [ ] **Relatórios**: Definir quais relatórios são necessários (tipos, métricas, periodicidade)
- [ ] **Catálogo TCPO base**: De onde vem a carga inicial? Qual a fonte de dados?

### Documentação de Produto
- [ ] User stories para features incompletas
- [ ] Critérios de aceitação para cada funcionalidade
- [ ] Mapeamento de personas (admin, aprovador, usuário operacional)
- [ ] Fluxos de negócio documentados (BPMN ou similar)
- [ ] Priorização de backlog para finalização

### Validação
- [ ] Validar com stakeholders se RBAC atual (USUARIO, APROVADOR, ADMIN) cobre todos os casos
- [ ] Validar regras de multi-tenancy (isolamento de dados entre clientes)
- [ ] Definir política de versionamento de composições (quando criar nova versão? quem autoriza?)

---

## 10. CARGA E QUALIDADE DE DADOS

### Criticidade: 🟡 MÉDIA

O sistema precisa de carga de dados iniciais para funcionar.

### Carga Inicial
- [ ] ETL para importação do catálogo TCPO (fonte: PINI / Editora PINI)
- [ ] Normalização de descrições para busca textual (descricao_tokens)
- [ ] Geração de embeddings em batch para todo catálogo (~50K+ serviços TCPO)
- [ ] Carga de categorias de recurso

### Qualidade de Dados
- [ ] Validação de CNPJs na base de clientes
- [ ] Deduplicação de serviços (fuzzy matching no catálogo)
- [ ] Monitoramento de qualidade dos dados ao longo do tempo

### Analytics (Futuro — manter simples)
- [ ] Queries SQL sob demanda no PostgreSQL (serviços mais buscados, taxa de aprovação, tempo médio de homologação)
- [ ] Se necessário dashboards: exportar CSV para Excel/Power BI local

---

## 11. DOCUMENTAÇÃO FALTANTE

### Criticidade: 🟡 MÉDIA

README.md e README_FRONT.MD são bons mas incompletos para produção.

- [ ] **Documentação de API**: OpenAPI/Swagger completa com exemplos (FastAPI gera automaticamente, mas precisa de enrichment)
- [ ] **Guia de instalação no Windows Server**: Passo-a-passo completo (PostgreSQL, Python, Node, NSSM, IIS)
- [ ] **Guia de operação**: Backup, restore, monitoramento, troubleshooting
- [ ] **Guia do usuário**: Manual para cada perfil (admin, aprovador, usuário)
- [ ] **Runbook de incidentes**: Procedimentos para problemas comuns (serviço caiu, disco cheio, banco travou)
- [ ] **Changelog**: Histórico de versões

---

## MATRIZ DE PRIORIDADE E SEQUENCIAMENTO

```
┌──────────────────────────────────┬─────────────┬────────────┬────────────────────────┐
│ O que falta                      │ Prioridade  │ Quando     │ Depende de             │
├──────────────────────────────────┼─────────────┼────────────┼────────────────────────┤
│ Decisões de negócio              │ 🔴 CRÍTICA  │ IMEDIATO   │ —                      │
│ Setup do Windows Server          │ 🔴 CRÍTICA  │ IMEDIATO   │ —                      │
│ Scripts de deploy (.bat/.ps1)    │ 🔴 CRÍTICA  │ IMEDIATO   │ Servidor configurado   │
│ Backup automático do banco       │ 🔴 CRÍTICA  │ Semana 1   │ PostgreSQL instalado   │
│ 3 endpoints backend faltantes    │ 🟡 ALTA     │ Sprint 1   │ Decisões de negócio    │
│ Perfil frontend (edit/senha)     │ 🟡 ALTA     │ Sprint 1   │ Endpoints backend      │
│ Tuning do PostgreSQL             │ 🟡 ALTA     │ Sprint 1-2 │ Servidor pronto        │
│ Testes automatizados             │ 🟡 ALTA     │ Sprint 1-3 │ —                      │
│ Otimização ML (modelo pt-BR)     │ 🟡 ALTA     │ Sprint 2-4 │ Dados TCPO carregados  │
│ Conversão para ONNX Runtime      │ 🟡 ALTA     │ Sprint 2-3 │ Modelo definido        │
│ Auditoria de segurança           │ 🟡 MÉDIA    │ Sprint 3-4 │ App funcional          │
│ Design UX de features novas      │ 🟡 MÉDIA    │ Sprint 2-4 │ Decisões de negócio    │
│ Carga de dados TCPO              │ 🟡 MÉDIA    │ Sprint 1-3 │ Fonte TCPO definida    │
│ Documentação de operação         │ 🟡 MÉDIA    │ Sprint 4+  │ Deploy funcionando     │
│ Guia do usuário                  │ 🟡 MÉDIA    │ Sprint 4+  │ Features finalizadas   │
└──────────────────────────────────┴─────────────┴────────────┴────────────────────────┘
```

---

## SEQUÊNCIA DE EXECUÇÃO RECOMENDADA

```
SEMANA 1-2 (Setup):
├── Decisões de negócio pendentes
├── Instalar PostgreSQL 16 no Windows Server (installer offline)
├── Instalar pgvector (binário trazido por pendrive)
├── Instalar Python 3.12 (installer offline)
├── Configurar NSSM (FastAPI como Windows Service)
├── Configurar IIS como proxy reverso
├── Script de backup do banco (Task Scheduler)
└── Testar deploy.ps1 / deploy.bat (cópia local)

SPRINT 1 (Backend + Frontend finais):
├── Implementar 3 endpoints faltantes (/perfil PATCH, /trocar-senha, /preferencias)
├── Frontend: formulário de edição de perfil + troca de senha
├── Tuning do PostgreSQL (índices, pg_stat_statements)
├── Testes unitários dos services
└── Carga inicial de dados TCPO

SPRINT 2-3 (ML + Testes):
├── Converter modelo ML para ONNX Runtime
├── Avaliar modelo multilingual (pt-BR)
├── Testes de integração e E2E
└── Melhorias de UX (skeleton loaders, filtros, etc.)

SPRINT 4+ (Polish):
├── Auditoria de segurança
├── Load testing
├── Documentação de operação
├── Guia do usuário
└── Testes de acessibilidade
```

---

## O QUE JÁ ESTÁ BEM FEITO (PONTOS FORTES)

| Área                    | Status     | Nota                                                        |
|-------------------------|------------|-------------------------------------------------------------|
| Arquitetura Backend     | ✅ Sólida  | Camadas bem definidas (API → Service → Repository → Model)  |
| Segurança básica        | ✅ Boa     | JWT, bcrypt, RBAC, rate limiting, CORS, audit logging       |
| Frontend Architecture   | ✅ Sólida  | React Query, typed APIs, lazy loading, providers            |
| Design System           | ✅ Completo| Tokens, tema, dark mode, brand guide documentado            |
| Database Migrations     | ✅ Sólidas | 11 migrations sequenciais, Alembic async configurado        |
| API Contracts           | ✅ 28 endpoints| Frontend e backend alinhados em quase todos os contratos|
| Multi-tenancy           | ✅ Implementado| Isolamento por cliente em queries e endpoints            |
| Busca 4-fases           | ✅ Funcional| Associação → Fuzzy → Semântica com cascade inteligente     |
| Structured Logging      | ✅ Pronto  | structlog JSON, pronto para redirect para arquivo           |
| Docker Dev Environment  | ✅ Funcional| docker-compose com pgvector, healthchecks, volumes         |

---

## RISCOS PRINCIPAIS

| Risco                                          | Impacto | Mitigação                                              |
|------------------------------------------------|---------|--------------------------------------------------------|
| Deploy manual leva a erros em produção         | � Médio| Scripts .bat/.ps1 testados antes do go-live             |
| Modelo ML em inglês para textos em português   | 🟡 Médio| Avaliar modelo multilingual                            |
| Sem testes automatizados = regressões          | 🔴 Alto | Implementar testes antes de ir para produção           |
| Sem backup = perda de dados irrecuperável      | 🔴 Alto | Configurar backup via Task Scheduler na semana 1       |
| torch CPU = alto consumo de RAM (~2GB)         | 🟡 Médio| Converter para ONNX (reduz para ~500MB)                |
| Servidor único = sem redundância               | 🟡 Médio| Backup diário + restart automático (aceitável p/ intranet)|
| pgvector no Windows pode ser difícil de instalar| 🟡 Médio| Baixar binário pré-compilado; fallback: Docker só p/ PostgreSQL|
| **Servidor sem internet** / firewall bloqueando | 🟡 Médio| Tudo offline: installers, wheels, build feito na dev    |
| Decisões de negócio indefinidas bloqueiam dev  | 🟡 Médio| Resolver decisões pendentes antes de começar sprints   |

---

## NOTA SOBRE O AMBIENTE

Este documento reflete a realidade da empresa:

- **Windows Server na intranet** → Deploy nativo com Python + PostgreSQL instalados diretamente, sem dependência de Docker/Linux
- **Servidor SEM INTERNET** → Firewall bloqueia GitHub, ChatGPT e afins. Todo software, dependências e builds devem ser preparados na máquina de dev (com internet) e levados ao servidor via **rede interna ou pendrive**
- **Deploy via scripts .bat/.ps1** → Copia arquivos da máquina de dev, instala dependências offline (wheels), roda migrations, reinicia serviço
- **Sem equipe de infra** → Tudo que precisa de infraestrutura está documentado passo-a-passo nos scripts
- **Servidor com recursos limitados** → Observabilidade mínima (logs em arquivo, Task Scheduler para health check), sem stacks pesadas
- **Intranet only** → Sem CDN, WAF externo, VPN, alta disponibilidade, cloud
- **Segurança simplificada** → Sem exposição à internet; foco em HTTPS interno, backup e RBAC
- **Docker** → Não é pré-requisito. Só considerá-lo se a instalação do pgvector nativo no Windows for problemática
- **IIS** → Já vem no Windows Server, pode servir como reverse proxy sem instalar nada extra

A abordagem é **pragmática**: instalar PostgreSQL e Python nativamente, rodar Uvicorn como Windows Service via NSSM, servir frontend via IIS, backup via Task Scheduler, deploy via script.

---

*Documento gerado a partir de análise automatizada do repositório completo em Abril 2026.*