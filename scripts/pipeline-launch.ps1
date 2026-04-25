#Requires -Version 5.1
<#
.SYNOPSIS
    Auto-launcher — lê o log do pipeline e abre um terminal com o comando do worker.

.DESCRIPTION
    Lê o último `CLI_COMMAND` do log do worker (ou role especificada) e abre
    um novo terminal PowerShell já posicionado no projeto, pronto para executar.

    Útil quando o pipeline (modo emit) montou o comando mas você precisa de
    um terminal interativo para rodar o CLI (kimi, codex, etc.).

.PARAMETER Role
    Role a monitorar. Padrão: worker.

.PARAMETER ProjectRoot
    Raiz do projeto. Padrão: pasta pai de scripts/.

.EXAMPLE
    .\scripts\pipeline-launch.ps1
    .\scripts\pipeline-launch.ps1 -Role qa
#>
param(
    [string]$Role = "worker",
    [string]$ProjectRoot = $null
)

# Resolve project root
if (-not $ProjectRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path
}

$logFile = Join-Path $ProjectRoot "docs\shared\pipeline\logs\pipeline-${Role}.log"

if (-not (Test-Path $logFile)) {
    Write-Error "Log not found: $logFile"
    Write-Host "Hint: run the pipeline first so the agent produces a log entry."
    exit 1
}

# Read last 50 lines and find the most recent CLI_COMMAND
$lines = Get-Content $logFile -Tail 50
$commandLine = $null

foreach ($line in ($lines | Select-Object -Last 50)) {
    if ($line -match "CLI_COMMAND=([^\s].*?)$") {
        $commandLine = $matches[1].Trim()
    }
}

if (-not $commandLine) {
    Write-Error "No CLI_COMMAND found in recent log entries."
    Write-Host "The pipeline may not have detected a [PENDING] message yet."
    exit 1
}

Write-Host "========================================"
Write-Host "PIPELINE AUTO-LAUNCHER"
Write-Host "Role: $Role"
Write-Host "Project: $ProjectRoot"
Write-Host "========================================"
Write-Host ""
Write-Host "Resolved command:"
Write-Host $commandLine -ForegroundColor Cyan
Write-Host ""

# Load user + machine PATH so the new terminal finds CLIs
$machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
$fullPath = ($machinePath, $userPath, $env:Path) -join ";"

# Build a tiny startup script for the new terminal
$startupScript = @"
Set-Location -LiteralPath '$ProjectRoot'
`$env:Path = '$fullPath'
Write-Host '========================================' -ForegroundColor Green
Write-Host 'Pipeline Auto-Launcher Terminal' -ForegroundColor Green
Write-Host 'Role: $Role' -ForegroundColor Green
Write-Host '========================================'
Write-Host ''
Write-Host 'Command ready to execute:' -ForegroundColor Yellow
Write-Host '$commandLine' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Press ENTER to run, or Ctrl+C to cancel.' -ForegroundColor DarkGray
`$null = Read-Host
Invoke-Expression '$commandLine'
"@

$tempFile = [System.IO.Path]::GetTempFileName() + ".ps1"
$startupScript | Set-Content $tempFile -Encoding UTF8

# Open new PowerShell window with the startup script
Start-Process powershell.exe -ArgumentList "-NoExit","-ExecutionPolicy Bypass","-File `"$tempFile`""

Write-Host "New terminal launched. Close this window or keep it for monitoring."
