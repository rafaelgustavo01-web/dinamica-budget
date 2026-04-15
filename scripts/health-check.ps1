# ──────────────────────────────────────────────────────────────────────────────
# health-check.ps1 — Verificacao de saude da aplicacao
#
# Uso:
#   .\health-check.ps1
#   .\health-check.ps1 -AutoRestart
#   .\health-check.ps1 -AutoRestart -MaxRetries 5
#
# Recomendacao: Agendar via Task Scheduler a cada 5 minutos
#   schtasks /create /tn "DinamicaBudget-HealthCheck" /tr "powershell -File C:\apps\dinamica-budget\scripts\health-check.ps1 -AutoRestart" /sc minute /mo 5
# ──────────────────────────────────────────────────────────────────────────────

param(
    [switch]$AutoRestart,
    [int]$MaxRetries = 3,
    [string]$Url = "http://localhost:8000/health",
    [string]$ServiceName = "DinamicaBudget"
)

$ErrorActionPreference = "Stop"
$appRoot = "C:\apps\dinamica-budget"
$logFile = "$appRoot\logs\health-check.log"

if (-not (Test-Path "$appRoot\logs")) {
    New-Item -ItemType Directory -Path "$appRoot\logs" -Force | Out-Null
}

function Log($msg) {
    $entry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Write-Host $entry
    Add-Content -Path $logFile -Value $entry -ErrorAction SilentlyContinue
}

# ── Health check ──────────────────────────────────────────────────────────────
$healthy = $false
$dbConnected = $false
$statusText = "unreachable"

try {
    $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
    $health = $response.Content | ConvertFrom-Json
    $statusText = $health.status
    $dbConnected = $health.database_connected

    if ($statusText -eq "ok" -and $dbConnected -eq $true) {
        $healthy = $true
    }
} catch {
    $statusText = "unreachable ($_)"
}

# ── Resultado ─────────────────────────────────────────────────────────────────
if ($healthy) {
    Log "OK — status=$statusText db=$dbConnected"
    exit 0
}

Log "FALHA — status=$statusText db=$dbConnected"

# ── Auto-restart se habilitado ────────────────────────────────────────────────
if (-not $AutoRestart) {
    Write-Host "Use -AutoRestart para tentar recuperar automaticamente." -ForegroundColor Yellow
    exit 1
}

Log "Tentando restart do servico $ServiceName..."

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Log "ERRO: Servico $ServiceName nao encontrado"
    exit 1
}

if ($svc.Status -eq "Running") {
    Stop-Service -Name $ServiceName -Force
    Log "Servico parado."
}

Start-Service -Name $ServiceName
Log "Servico reiniciado. Aguardando estabilizacao..."

# Aguardar e verificar novamente
$attempt = 0
$recovered = $false

while ($attempt -lt $MaxRetries) {
    $attempt++
    Start-Sleep -Seconds 5

    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
        $health = $response.Content | ConvertFrom-Json
        if ($health.status -eq "ok" -and $health.database_connected -eq $true) {
            $recovered = $true
            break
        }
    } catch {
        # Ainda nao respondeu
    }

    Log "Tentativa $attempt/$MaxRetries — ainda nao respondeu."
}

if ($recovered) {
    Log "RECUPERADO — servico voltou ao normal apos restart."
    exit 0
} else {
    Log "CRITICO — servico nao recuperou apos $MaxRetries tentativas. Verificar manualmente!"
    exit 2
}
