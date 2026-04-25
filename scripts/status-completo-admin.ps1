#Requires -RunAsAdministrator
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$HostUrl = "http://dinamica-budget.local",
    [string]$AppDir = "C:\DinamicaBudget",
    [string]$EnvFile = "C:\DinamicaBudget\.env"
)

$ErrorActionPreference = "Continue"

function Ok([string]$m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail([string]$m) { Write-Host "[FAIL] $m" -ForegroundColor Red }

function Parse-Env([string]$path) {
    $map = @{}
    if (!(Test-Path $path)) { return $map }
    foreach ($raw in Get-Content -Path $path -Encoding UTF8) {
        $line = $raw.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { continue }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }
        $map[$line.Substring(0, $idx).Trim()] = $line.Substring($idx + 1).Trim()
    }
    return $map
}

Write-Host ""
Write-Host "=== DINAMICA BUDGET - STATUS COMPLETO ===" -ForegroundColor Cyan
Write-Host ("Data: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))

Write-Host "`n[1] Servicos"
$svcNames = @("postgresql-x64-16", "DinamicaBudgetAPI", "W3SVC")
foreach ($name in $svcNames) {
    $s = Get-Service -Name $name -ErrorAction SilentlyContinue
    if (-not $s) { Warn "$name nao encontrado"; continue }
    if ($s.Status -eq "Running") { Ok "$name = Running" } else { Fail "$name = $($s.Status)" }
}

Write-Host "`n[2] Portas"
foreach ($p in @(80, 443, 8000, 5432)) {
    $listen = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listen) { Ok "Porta $p em LISTEN" } else { Fail "Porta $p sem LISTEN" }
}

Write-Host "`n[3] API Health"
try {
    $h = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 8
    if ($h.status -eq "ok" -or $h.status -eq "degraded") { Ok "status=$($h.status)" } else { Fail "status=$($h.status)" }
    if ($h.database_connected) { Ok "database_connected=True" } else { Fail "database_connected=False" }
    if ($h.embedder_ready) { Ok "embedder_ready=True" } else { Warn "embedder_ready=False" }
} catch {
    Fail "Falha ao chamar $BaseUrl/health"
}

Write-Host "`n[4] app/frontend/IIS"
try {
    $r = Invoke-WebRequest -Uri "$HostUrl/" -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -eq 200) { Ok "Homepage HTTP 200" } else { Warn "Homepage HTTP $($r.StatusCode)" }
} catch {
    Fail "Homepage indisponivel"
}

try {
    $r = Invoke-WebRequest -Uri "$HostUrl/login" -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -eq 200) { Ok "SPA /login HTTP 200" } else { Warn "SPA /login HTTP $($r.StatusCode)" }
} catch {
    Fail "SPA /login indisponivel"
}

Write-Host "`n[5] Modelo de IA"
$envMap = Parse-Env $EnvFile
$modelName = $envMap["EMBEDDING_MODEL_NAME"]
if (-not $modelName) { $modelName = "all-MiniLM-L6-v2" }
$modelDir = Join-Path $AppDir "ml_models"
if (Test-Path $modelDir) {
    Ok "Diretorio de modelos: $modelDir"
    $hit = Get-ChildItem -Path $modelDir -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match [regex]::Escape($modelName) } | Select-Object -First 1
    if ($hit) { Ok "Modelo encontrado: $modelName" } else { Warn "Modelo nao encontrado por nome: $modelName" }
} else {
    Fail "Diretorio de modelos ausente: $modelDir"
}

Write-Host "`n[6] Logs"
$apiErr = "C:\Dinamica-Budget\logs\api-stderr.log"
$apiOut = "C:\Dinamica-Budget\logs\api-stdout.log"
if (Test-Path $apiErr) {
    $tail = Get-Content $apiErr -Tail 5 -ErrorAction SilentlyContinue
    Ok "api-stderr.log (ultimas 5 linhas)"
    $tail | ForEach-Object { Write-Host ("  " + $_) }
} else {
    Warn "api-stderr.log nao encontrado"
}
if (Test-Path $apiOut) {
    $tail = Get-Content $apiOut -Tail 5 -ErrorAction SilentlyContinue
    Ok "api-stdout.log (ultimas 5 linhas)"
    $tail | ForEach-Object { Write-Host ("  " + $_) }
} else {
    Warn "api-stdout.log nao encontrado"
}

Write-Host "`nStatus completo concluido." -ForegroundColor Cyan

