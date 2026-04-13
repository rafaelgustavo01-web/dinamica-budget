# ──────────────────────────────────────────────────────────────────────────────
# preparar-deploy.ps1 — Instalador inteligente: monta pacote de deploy
#
# Uso:  duplo-clique ou terminal:
#   .\scripts\preparar-deploy.ps1
#   .\scripts\preparar-deploy.ps1 -DeployDir "D:\deploy-package"
#   .\scripts\preparar-deploy.ps1 -SkipFrontendBuild
#
# O script detecta pre-requisitos, instala dependencias, e nunca fecha a janela.
# ──────────────────────────────────────────────────────────────────────────────

param(
    [string]$DeployDir = "C:\deploy-package",
    [switch]$SkipFrontendBuild
)

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

function Test-Command { param([string]$cmd) return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# ── Inicio ────────────────────────────────────────────────────────────────────
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

Write-Banner "PREPARAR PACOTE DE DEPLOY — Dinamica Budget"
Write-Host "  Projeto : $projectRoot"
Write-Host "  Destino : $DeployDir"
Write-Host "  Data    : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 0 — Verificar pre-requisitos
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 0/5 — Verificar pre-requisitos"

# Node.js
if (Test-Command "node") {
    $nodeVer = (node --version 2>$null)
    Write-Ok "Node.js encontrado: $nodeVer"
} else {
    Write-Fail "Node.js NAO encontrado. Instale em https://nodejs.org"
}

# npm
if (Test-Command "npm") {
    $npmVer = (npm --version 2>$null)
    Write-Ok "npm encontrado: v$npmVer"
} else {
    Write-Fail "npm NAO encontrado."
}

# Python
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    if (Test-Command $cmd) { $pythonCmd = $cmd; break }
}
if ($pythonCmd) {
    $pyVer = & $pythonCmd --version 2>&1
    Write-Ok "Python encontrado: $pyVer (cmd: $pythonCmd)"
} else {
    Write-Fail "Python NAO encontrado. Instale Python 3.12+ em https://python.org"
}

# pip
if ($pythonCmd) {
    $pipCheck = & $pythonCmd -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "pip encontrado: $($pipCheck -replace 'pip\s+([\d.]+).*','v$1')"
    } else {
        Write-Fail "pip NAO encontrado. Execute: $pythonCmd -m ensurepip --upgrade"
    }
} else {
    Write-Fail "pip NAO pode ser verificado (Python ausente)."
}

# Projeto
if (Test-Path "$projectRoot\app\main.py") {
    Write-Ok "Backend encontrado: app\main.py"
} else {
    Write-Fail "Backend NAO encontrado em $projectRoot\app\"
}
if (Test-Path "$projectRoot\frontend\package.json") {
    Write-Ok "Frontend encontrado: frontend\package.json"
} else {
    Write-Fail "Frontend NAO encontrado em $projectRoot\frontend\"
}
if (Test-Path "$projectRoot\requirements.txt") {
    Write-Ok "requirements.txt encontrado"
} else {
    Write-Fail "requirements.txt NAO encontrado"
}

if ($HasError) {
    Write-Banner "PRE-REQUISITOS FALTANDO — Corrija os erros acima" "Red"
    Wait-AndExit 1
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 1 — Build do frontend
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 1/5 — Build do frontend"

if ($SkipFrontendBuild) {
    Write-Warn "Build do frontend IGNORADO (-SkipFrontendBuild)."
    if (-not (Test-Path "$projectRoot\frontend\dist\index.html")) {
        Write-Fail "frontend\dist\index.html nao encontrado. Rode sem -SkipFrontendBuild."
        Wait-AndExit 1
    }
    Write-Ok "dist\index.html existente encontrado"
} else {
    try {
        Set-Location "$projectRoot\frontend"

        # npm install (sempre se node_modules ausente)
        if (-not (Test-Path "node_modules")) {
            Write-Info "Instalando dependencias do frontend (npm install)..."
            npm install 2>&1 | ForEach-Object { Write-Info $_ }
            if ($LASTEXITCODE -ne 0) {
                Write-Fail "npm install falhou (exit code: $LASTEXITCODE)"
                Write-Info "Tente manualmente: cd frontend && npm install"
                Wait-AndExit 1
            }
            Write-Ok "npm install concluido"
        } else {
            Write-Ok "node_modules ja existe — pulando npm install"
        }

        # npm run build
        Write-Info "Executando: npm run build (tsc + vite)..."
        npm run build 2>&1 | ForEach-Object { Write-Host "   $_" }
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "npm run build falhou (exit code: $LASTEXITCODE)"
            Write-Info "Corrija os erros TypeScript acima e rode novamente."
            Wait-AndExit 1
        }

        if (-not (Test-Path "dist\index.html")) {
            Write-Fail "Build nao gerou dist\index.html"
            Wait-AndExit 1
        }
        Write-Ok "Frontend buildado com sucesso"
    } catch {
        Write-Fail "Excecao no build do frontend: $_"
        Wait-AndExit 1
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 2 — Limpar e criar estrutura de pastas
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 2/5 — Montar estrutura do pacote em $DeployDir"

try {
    if (Test-Path $DeployDir) {
        Write-Info "Removendo pacote anterior..."
        Remove-Item -Recurse -Force $DeployDir
    }

    foreach ($sub in @("backend", "frontend", "wheels", "scripts")) {
        New-Item -ItemType Directory -Path "$DeployDir\$sub" -Force | Out-Null
    }
    Write-Ok "Estrutura criada: backend, frontend, wheels, scripts"
} catch {
    Write-Fail "Falha ao criar estrutura: $_"
    Wait-AndExit 1
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 3 — Copiar arquivos
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 3/5 — Copiar arquivos do projeto"

try {
    # Backend
    Copy-Item -Path "$projectRoot\app"             -Destination "$DeployDir\backend\app"     -Recurse -Force
    Copy-Item -Path "$projectRoot\alembic"         -Destination "$DeployDir\backend\alembic" -Recurse -Force
    Copy-Item -Path "$projectRoot\alembic.ini"     -Destination "$DeployDir\backend\"        -Force
    Copy-Item -Path "$projectRoot\requirements.txt" -Destination "$DeployDir\backend\"       -Force
    Copy-Item -Path "$projectRoot\pytest.ini"       -Destination "$DeployDir\backend\"       -Force -ErrorAction SilentlyContinue
    Write-Ok "Backend copiado (app, alembic, configs)"

    # Frontend
    Copy-Item -Path "$projectRoot\frontend\dist\*" -Destination "$DeployDir\frontend\"      -Recurse -Force
    Write-Ok "Frontend copiado (dist/)"

    # Scripts
    $scriptsCopied = 0
    foreach ($f in @("deploy.ps1","deploy.bat","preparar-deploy.ps1","preparar-deploy.bat","backup-db.ps1","health-check.ps1","instalar-servico.ps1")) {
        $src = "$projectRoot\scripts\$f"
        if (Test-Path $src) {
            Copy-Item -Path $src -Destination "$DeployDir\scripts\" -Force
            $scriptsCopied++
        }
    }
    Write-Ok "Scripts copiados ($scriptsCopied arquivos)"

    # .env.example (se existir)
    if (Test-Path "$projectRoot\.env.example") {
        Copy-Item -Path "$projectRoot\.env.example" -Destination "$DeployDir\" -Force
        Write-Ok ".env.example copiado"
    }
    # docker-compose.yml e Dockerfile
    foreach ($f in @("docker-compose.yml","Dockerfile")) {
        if (Test-Path "$projectRoot\$f") {
            Copy-Item -Path "$projectRoot\$f" -Destination "$DeployDir\" -Force
        }
    }
    Write-Ok "Arquivos Docker copiados"
} catch {
    Write-Fail "Falha ao copiar arquivos: $_"
    Wait-AndExit 1
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 4 — Baixar wheels Python (offline install)
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 4/5 — Baixar wheels Python para install offline"

try {
    Write-Info "Executando: pip download -r requirements.txt ..."
    & $pythonCmd -m pip download -r "$projectRoot\requirements.txt" -d "$DeployDir\wheels" 2>&1 | ForEach-Object { Write-Info $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "pip download falhou (exit code: $LASTEXITCODE)"
        Write-Info "Verifique sua conexao com a internet e tente novamente."
        Wait-AndExit 1
    }
    $wheelCount = (Get-ChildItem "$DeployDir\wheels" -File | Measure-Object).Count
    Write-Ok "Wheels baixados: $wheelCount pacotes em wheels\"
} catch {
    Write-Fail "Excecao ao baixar wheels: $_"
    Wait-AndExit 1
}

# ══════════════════════════════════════════════════════════════════════════════
# ETAPA 5 — Resumo final
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "ETAPA 5/5 — Resumo do pacote"

$totalFiles = (Get-ChildItem -Recurse -File $DeployDir | Measure-Object).Count
$totalSize  = "{0:N1} MB" -f ((Get-ChildItem -Recurse -File $DeployDir | Measure-Object -Property Length -Sum).Sum / 1MB)

Write-Host ""
Write-Host "  Conteudo do pacote:" -ForegroundColor White
foreach ($sub in @("backend","frontend","wheels","scripts")) {
    $subPath = "$DeployDir\$sub"
    if (Test-Path $subPath) {
        $c = (Get-ChildItem -Recurse -File $subPath | Measure-Object).Count
        Write-Host "    $sub\ — $c arquivos" -ForegroundColor Gray
    }
}

Write-Banner "PACOTE PRONTO — $totalFiles arquivos ($totalSize)" "Green"
Write-Host "  Local: $DeployDir"
Write-Host ""
Write-Host "  Proximo passo:" -ForegroundColor Cyan
Write-Host "  1. Copie '$DeployDir' para o servidor (rede interna ou pendrive)"
Write-Host "  2. No servidor, execute:" -ForegroundColor White
Write-Host "     .\scripts\deploy.ps1 -PackagePath '$DeployDir'" -ForegroundColor Yellow
Write-Host "     ou: deploy.bat $DeployDir" -ForegroundColor Yellow
Write-Host ""

Set-Location $projectRoot
Wait-AndExit 0
