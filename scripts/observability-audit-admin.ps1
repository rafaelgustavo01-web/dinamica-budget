#Requires -RunAsAdministrator
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$HostUrl = "http://dinamica-budget.local",
    [string]$OutJson = "C:\Dinamica-Budget\logs\observability-audit.json",
    [string]$OutLog = "C:\Dinamica-Budget\logs\observability-audit.log"
)

$ErrorActionPreference = "Continue"

$outDir = Split-Path -Parent $OutJson
if (!(Test-Path $outDir)) {
    New-Item -Path $outDir -ItemType Directory -Force | Out-Null
}

Set-Content -Path $OutLog -Value "" -Encoding UTF8

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Add-Content -Path $OutLog -Value $line
}

$checks = New-Object System.Collections.Generic.List[object]
function Add-Check([string]$name, [bool]$ok, [string]$detail) {
    $checks.Add([pscustomobject]@{ name = $name; ok = $ok; detail = $detail })
    if ($ok) { Log("OK   " + $name + " - " + $detail) } else { Log("FAIL " + $name + " - " + $detail) }
}

# Services
foreach ($svcName in @("postgresql-x64-16", "DinamicaBudgetAPI", "W3SVC")) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -eq "Running") {
        Add-Check "service:$svcName" $true "Running"
    } elseif ($svc) {
        Add-Check "service:$svcName" $false ("Status=" + $svc.Status)
    } else {
        Add-Check "service:$svcName" $false "not found"
    }
}

# Health endpoint
try {
    $h = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 8
    Add-Check "api:health" $true ("status=" + $h.status + ", db=" + $h.database_connected + ", embedder=" + $h.embedder_ready)
    if (-not $h.database_connected) {
        Add-Check "api:database_connected" $false "health reports database_connected=False"
    }
    if (-not $h.embedder_ready) {
        Add-Check "api:embedder_ready" $false "health reports embedder_ready=False"
    }
} catch {
    Add-Check "api:health" $false "request failed"
}

# Frontend and proxy
try {
    $r = Invoke-WebRequest -Uri "$HostUrl/" -UseBasicParsing -TimeoutSec 8
    Add-Check "frontend:root" ($r.StatusCode -eq 200) ("HTTP " + $r.StatusCode)
} catch {
    Add-Check "frontend:root" $false "request failed"
}

try {
    $r = Invoke-WebRequest -Uri "$HostUrl/login" -UseBasicParsing -TimeoutSec 8
    Add-Check "frontend:spa_login" ($r.StatusCode -eq 200) ("HTTP " + $r.StatusCode)
} catch {
    Add-Check "frontend:spa_login" $false "request failed"
}

# Login endpoint reachability (invalid credentials must not 5xx)
$loginCode = 0
try {
    $payload = '{"email":"invalid@example.com","password":"invalid123"}'
    $r = Invoke-WebRequest -Uri "$HostUrl/api/v1/auth/login" -Method Post -Body $payload -ContentType "application/json" -UseBasicParsing -TimeoutSec 8
    $loginCode = [int]$r.StatusCode
} catch {
    if ($_.Exception.Response) {
        $loginCode = [int]$_.Exception.Response.StatusCode
    }
}
Add-Check "api:login_reachability" (($loginCode -gt 0) -and ($loginCode -lt 500)) ("HTTP " + $loginCode)

# Route validation script integration
$routeValidator = "C:\Dinamica-Budget\scripts\validate-all-routes-admin.ps1"
if (Test-Path $routeValidator) {
    powershell -NoProfile -ExecutionPolicy Bypass -File $routeValidator *> $null
    if ($LASTEXITCODE -eq 0) {
        Add-Check "api:all_routes" $true "all OpenAPI routes reachable without critical failures"
    } else {
        Add-Check "api:all_routes" $false "critical failures in OpenAPI route validation"
    }
} else {
    Add-Check "api:all_routes" $false "validator script not found"
}

# Error signal scan in logs
$errorPatterns = @("Traceback", "CRITICAL", "Unhandled", "ConnectionDoesNotExistError", "UnicodeDecodeError")
$logTargets = @(
    "C:\Dinamica-Budget\logs\api-stderr.log",
    "C:\Dinamica-Budget\logs\api-stdout.log"
)
$errorHits = 0
foreach ($target in $logTargets) {
    Get-ChildItem -Path $target -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 2 | ForEach-Object {
        $tail = Get-Content $_.FullName -Tail 150 -ErrorAction SilentlyContinue
        foreach ($pat in $errorPatterns) {
            $hits = @($tail | Select-String -Pattern $pat -SimpleMatch)
            $errorHits += $hits.Count
        }
    }
}
if ($errorHits -gt 0) {
    Add-Check "logs:error_signals" $true ("warning: severe runtime error patterns found=" + $errorHits)
} else {
    Add-Check "logs:error_signals" $true "no critical error patterns in recent tails"
}

$failed = @($checks | Where-Object { -not $_.ok })
$summary = [pscustomobject]@{
    checked_at = (Get-Date).ToString("o")
    total_checks = $checks.Count
    failed_checks = $failed.Count
    healthy = ($failed.Count -eq 0)
    checks = $checks
}

$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $OutJson -Encoding UTF8

if ($failed.Count -eq 0) {
    Log "Observability audit PASS"
    exit 0
}

Log ("Observability audit FAIL - failed checks: " + $failed.Count)
exit 1
