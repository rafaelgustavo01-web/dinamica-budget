# ──────────────────────────────────────────────────────────────────────────────
# deploy.ps1 — Instalador inteligente: deploy no Windows Server (sem internet)
#
# Uso:
#   .\deploy.ps1 -PackagePath "D:\deploy-package"
#   .\deploy.ps1 -PackagePath "\\servidor\share\deploy-package"
#   .\deploy.ps1 -PackagePath "D:\deploy-package" -SkipMigrations
#   .\deploy.ps1 -PackagePath "D:\deploy-package" -SkipPip
#
# O script valida tudo, executa etapa por etapa, e nunca fecha a janela.
# ──────────────────────────────────────────────────────────────────────────────

param(
    [Parameter(Mandatory = $true)]
    [string]$PackagePath,
    [switch]$SkipMigrations,
    [switch]$SkipPip
)

$appRoot = "C:\apps\dinamica-budget"

# ── Helpers ───────────────────────────────────────────────────────────────────
$HasError = $false

function Write-Step  { param([string]$msg) Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-Ok    { param([string]$msg) Write-Host "   [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param([string]$msg) Write-Host "   [AVISO] $msg" -ForegroundColor Yellow }
function Write-Fail  { param([string]$msg) Write-Host "   [ERRO] $msg" -ForegroundColor Red; $script:HasError = $true }
function Write-Info  { param([string]$msg) Write-Host "   $msg" -ForegroundColor Gray }

function Write-Banner {
    param([string]$title, [ConsoleColor]$color = "Cyan")
    $line = "=" * 60
    Write-Host ""
    Write-Host $line -ForegroundColor $color
    Write-Host "  $title" -ForegroundColor $color
    Write-Host $line -ForegroundColor $color
    Write-Host ""
}

function Wait-AndExit {
    param([int]$code = 0)
    Write-Host ""
    Write-Host "Pressione qualquer tecla para fechar..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit $code
}

# ── Inicio ────────────────────────────────────────────────────────────────────
Write-Banner "DEPLOY DINAMICA BUDGET — Windows Server"
Write-Host "  Pacote  : $PackagePath"
Write-Host "  Destino : $appRoot"
Write-Host "  Data    : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 0 — Validar pacote e ambiente
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 0/6 — Validar pacote e ambiente do servidor"

# Pacote
if (Test-Path $PackagePath) {
    Write-Ok "Pacote encontrado: $PackagePath"
} else {
    Write-Fail "Pacote NAO encontrado: $PackagePath"
}
if (Test-Path "$PackagePath\backend\app") {
    Write-Ok "backend\app encontrado no pacote"
} else {
    Write-Fail "backend\app NAO encontrado no pacote"
}
if (Test-Path "$PackagePath\frontend\index.html") {
    Write-Ok "frontend\index.html encontrado no pacote"
} else {
    Write-Fail "frontend\index.html NAO encontrado no pacote"
}

# Servidor
if (Test-Path "$appRoot\venv\Scripts\python.exe") {
    Write-Ok "Virtualenv encontrado: $appRoot\venv"
} else {
    Write-Fail "Virtualenv NAO encontrado em $appRoot\venv"
    Write-Info "Crie com: python -m venv $appRoot\venv"
}
if (Test-Path "$appRoot\.env") {
    Write-Ok ".env encontrado em $appRoot\"
} else {
    Write-Fail ".env NAO encontrado em $appRoot\ — configure antes do deploy"
}

if (-not $SkipPip) {
    if (Test-Path "$PackagePath\wheels") {
        $wc = (Get-ChildItem "$PackagePath\wheels" -File | Measure-Object).Count
        Write-Ok "Pasta wheels encontrada ($wc pacotes)"
    } else {
        Write-Fail "Pasta wheels NAO encontrada em $PackagePath\wheels"
    }
}

if ($HasError) {
    Write-Banner "PRE-REQUISITOS FALTANDO — Corrija os erros acima" "Red"
    Wait-AndExit 1
}

# ── Criar estrutura se nao existir ────────────────────────────────────────────
foreach ($dir in @("backend", "frontend", "logs", "backups", "scripts")) {
    $path = Join-Path $appRoot $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}
Write-Ok "Estrutura de pastas verificada"

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Parar servico
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 1/6 — Parar servico DinamicaBudget"

$svc = Get-Service -Name "DinamicaBudget" -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq "Running") {
    try {
        Stop-Service -Name "DinamicaBudget" -Force -ErrorAction Stop
        Write-Ok "Servico parado"
    } catch {
        Write-Warn "Nao conseguiu parar o servico: $_"
        Write-Info "Continuando o deploy mesmo assim..."
    }
} elseif ($svc) {
    Write-Ok "Servico existe mas nao esta rodando (status: $($svc.Status))"
} else {
    Write-Warn "Servico DinamicaBudget nao registrado (primeira instalacao?)"
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 2 — Copiar backend
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 2/6 — Copiar backend"

try {
    Copy-Item -Path "$PackagePath\backend\*" -Destination "$appRoot\backend\" -Recurse -Force
    Write-Ok "Backend copiado para $appRoot\backend\"
} catch {
    Write-Fail "Falha ao copiar backend: $_"
    Wait-AndExit 1
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 3 — Copiar frontend
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 3/6 — Copiar frontend (build estatico)"

try {
    Copy-Item -Path "$PackagePath\frontend\*" -Destination "$appRoot\frontend\" -Recurse -Force
    Write-Ok "Frontend copiado para $appRoot\frontend\"
} catch {
    Write-Fail "Falha ao copiar frontend: $_"
    Wait-AndExit 1
}

# Copiar scripts se existirem
if (Test-Path "$PackagePath\scripts") {
    Copy-Item -Path "$PackagePath\scripts\*" -Destination "$appRoot\scripts\" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Ok "Scripts atualizados"
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 4 — Instalar dependencias Python (offline)
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 4/6 — Instalar dependencias Python (offline)"

if ($SkipPip) {
    Write-Warn "pip install IGNORADO (-SkipPip)"
} else {
    try {
        Write-Info "Executando: pip install --no-index --find-links wheels ..."
        & "$appRoot\venv\Scripts\pip.exe" install `
            -r "$appRoot\backend\requirements.txt" `
            --no-index `
            --find-links "$PackagePath\wheels" `
            2>&1 | ForEach-Object { Write-Info $_ }
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "pip install falhou (exit code: $LASTEXITCODE)"
            Wait-AndExit 1
        }
        Write-Ok "Dependencias Python instaladas"
    } catch {
        Write-Fail "Excecao ao instalar dependencias: $_"
        Wait-AndExit 1
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Rodar migrations
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 5/6 — Rodar Alembic migrations"

if ($SkipMigrations) {
    Write-Warn "Migrations IGNORADAS (-SkipMigrations)"
} else {
    try {
        # Carregar .env para DATABASE_URL
        $envFile = Get-Content "$appRoot\.env" -ErrorAction SilentlyContinue
        foreach ($line in $envFile) {
            if ($line -match "^\s*([^#][^=]+)=(.*)$") {
                [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
            }
        }
        Write-Info "Variaveis de ambiente carregadas do .env"

        Set-Location "$appRoot\backend"
        Write-Info "Executando: alembic upgrade head ..."
        & "$appRoot\venv\Scripts\alembic.exe" upgrade head 2>&1 | ForEach-Object { Write-Info $_ }
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Alembic migrations falharam (exit code: $LASTEXITCODE)"
            Write-Info "Verifique se o PostgreSQL esta rodando e a DATABASE_URL esta correta."
            Wait-AndExit 1
        }
        Write-Ok "Migrations aplicadas com sucesso"
    } catch {
        Write-Fail "Excecao nas migrations: $_"
        Wait-AndExit 1
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 6 — Iniciar servico e health check
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 6/6 — Iniciar servico e health check"

$svc = Get-Service -Name "DinamicaBudget" -ErrorAction SilentlyContinue
if ($svc) {
    try {
        Start-Service -Name "DinamicaBudget" -ErrorAction Stop
        Write-Ok "Servico DinamicaBudget iniciado"

        # Aguardar um pouco para a app subir
        Write-Info "Aguardando aplicacao inicializar (5s)..."
        Start-Sleep -Seconds 5

        # Health check
        Write-Info "Verificando health check em http://localhost:8000/health ..."
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 15 -UseBasicParsing
            $health = $response.Content | ConvertFrom-Json
            Write-Ok "Health check OK — status: $($health.status)"
            if ($health.PSObject.Properties["database_connected"]) {
                $dbColor = if ($health.database_connected) { "Green" } else { "Red" }
                Write-Host "   DB conectado: $($health.database_connected)" -ForegroundColor $dbColor
            }
            if ($health.PSObject.Properties["embedder_ready"]) {
                $emColor = if ($health.embedder_ready) { "Green" } else { "Yellow" }
                Write-Host "   Embedder ready: $($health.embedder_ready)" -ForegroundColor $emColor
            }
        } catch {
            Write-Warn "Health check falhou — a aplicacao pode levar mais tempo para iniciar."
            Write-Info "Tente manualmente: Invoke-WebRequest http://localhost:8000/health"
        }
    } catch {
        Write-Warn "Nao conseguiu iniciar o servico: $_"
        Write-Info "Inicie manualmente: Start-Service DinamicaBudget"
    }
} else {
    Write-Warn "Servico DinamicaBudget nao registrado."
    Write-Info "Execute primeiro: .\scripts\instalar-servico.ps1"
    Write-Info "Ou inicie manualmente:"
    Write-Info "  cd $appRoot\backend"
    Write-Info "  $appRoot\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000"
}

# ── Resultado final ───────────────────────────────────────────────────────────
Write-Banner "DEPLOY CONCLUIDO COM SUCESSO" "Green"
Write-Host "  Aplicacao: $appRoot"
Write-Host "  URL:       http://localhost:8000"
Write-Host "  Health:    http://localhost:8000/health"
Write-Host "  Logs:      $appRoot\logs\"
Write-Host ""

Wait-AndExit 0
