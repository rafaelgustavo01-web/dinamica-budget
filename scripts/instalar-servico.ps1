# ──────────────────────────────────────────────────────────────────────────────
# instalar-servico.ps1 — Registrar Dinamica Budget como servico Windows via NSSM
#
# Uso (executar como Administrador UMA VEZ):
#   .\instalar-servico.ps1
#   .\instalar-servico.ps1 -NssmPath "D:\tools\nssm.exe"
#   .\instalar-servico.ps1 -Workers 2
#
# Pre-requisitos:
#   - NSSM (https://nssm.cc) copiado para o servidor
#   - Virtualenv criado: python -m venv C:\apps\dinamica-budget\venv
#   - .env configurado em C:\apps\dinamica-budget\.env
# ──────────────────────────────────────────────────────────────────────────────

param(
    [string]$NssmPath = "C:\tools\nssm.exe",
    [int]$Workers = 1,
    [int]$Port = 8000,
    [string]$ServiceName = "DinamicaBudget"
)

$ErrorActionPreference = "Stop"
$appRoot = "C:\apps\dinamica-budget"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALAR SERVICO DINAMICA BUDGET"       -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Validacoes ────────────────────────────────────────────────────────────────
if (-not (Test-Path $NssmPath)) {
    throw "NSSM nao encontrado em $NssmPath. Baixe de https://nssm.cc e copie para o servidor."
}
if (-not (Test-Path "$appRoot\venv\Scripts\python.exe")) {
    throw "Virtualenv nao encontrado em $appRoot\venv"
}
if (-not (Test-Path "$appRoot\.env")) {
    throw ".env nao encontrado em $appRoot\.env"
}

# ── Verificar se ja existe ────────────────────────────────────────────────────
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Servico '$ServiceName' ja existe. Remover primeiro?" -ForegroundColor Yellow
    $resp = Read-Host "Remover e recriar? (S/N)"
    if ($resp -ne "S" -and $resp -ne "s") {
        Write-Host "Cancelado." -ForegroundColor Red
        exit 0
    }
    if ($existing.Status -eq "Running") {
        Stop-Service -Name $ServiceName -Force
    }
    & $NssmPath remove $ServiceName confirm
    Write-Host "  Servico removido." -ForegroundColor Green
}

# ── Criar pastas obrigatorias ─────────────────────────────────────────────────
foreach ($dir in @("logs")) {
    $path = Join-Path $appRoot $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

# ── Registrar servico ────────────────────────────────────────────────────────
$python = "$appRoot\venv\Scripts\python.exe"
$uvicornArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port $Port --workers $Workers"

Write-Host "Registrando servico '$ServiceName'..." -ForegroundColor Yellow
& $NssmPath install $ServiceName $python $uvicornArgs

# Diretorio de trabalho
& $NssmPath set $ServiceName AppDirectory "$appRoot\backend"

# Descricao
& $NssmPath set $ServiceName Description "Dinamica Budget API - FastAPI/Uvicorn"
& $NssmPath set $ServiceName DisplayName "Dinamica Budget API"

# Variavel de ambiente: carregar .env
& $NssmPath set $ServiceName AppEnvironmentExtra "DOTENV_PATH=$appRoot\.env"

# Logs — stdout e stderr para arquivos com rotacao
& $NssmPath set $ServiceName AppStdout "$appRoot\logs\service-stdout.log"
& $NssmPath set $ServiceName AppStderr "$appRoot\logs\service-stderr.log"
& $NssmPath set $ServiceName AppStdoutCreationDisposition 4
& $NssmPath set $ServiceName AppStderrCreationDisposition 4
& $NssmPath set $ServiceName AppRotateFiles 1
& $NssmPath set $ServiceName AppRotateOnline 1
& $NssmPath set $ServiceName AppRotateBytes 10485760  # 10 MB

# Restart automatico em falha
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 5000  # 5 segundos

# Inicio automatico
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

Write-Host ""
Write-Host "Servico registrado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "Configuracao:" -ForegroundColor Cyan
Write-Host "  Nome:      $ServiceName"
Write-Host "  Python:    $python"
Write-Host "  Args:      $uvicornArgs"
Write-Host "  WorkDir:   $appRoot\backend"
Write-Host "  Logs:      $appRoot\logs\"
Write-Host "  Porta:     $Port"
Write-Host "  Workers:   $Workers"
Write-Host ""
Write-Host "Comandos uteis:" -ForegroundColor Cyan
Write-Host "  Iniciar:   net start $ServiceName"
Write-Host "  Parar:     net stop $ServiceName"
Write-Host "  Status:    Get-Service $ServiceName"
Write-Host "  Remover:   nssm remove $ServiceName confirm"
Write-Host "  Editar:    nssm edit $ServiceName"
Write-Host ""
