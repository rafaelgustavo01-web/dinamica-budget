#Requires -Version 5.1
<#
.SYNOPSIS
    Pipeline Control — Start, Stop, and Configure the Dinamica Budget sprint pipeline.

.DESCRIPTION
    Provides three commands:
      start   — Creates Windows Task Scheduler tasks for all active roles.
      stop    — Disables all pipeline tasks and pauses the pipeline.
      time_set— Updates the polling interval and reconfigures tasks.

.PARAMETER Command
    start | stop | time_set

.PARAMETER Interval
    Polling interval in minutes (only used with time_set). Defaults to current config.

.PARAMETER DispatchMode
    Agent dispatch mode passed to pipeline-agent.ps1: emit | dry-run | run.
    Defaults to dry-run so scheduled polling proves the resolved CLI without executing it.

.PARAMETER ProjectRoot
    Absolute or relative path to project root. Defaults to parent of scripts/.

.EXAMPLE
    .\scripts\pipeline-control.ps1 -Command start
    .\scripts\pipeline-control.ps1 -Command stop
    .\scripts\pipeline-control.ps1 -Command time_set -Interval 15
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("start", "stop", "time_set")]
    [string]$Command,

    [int]$Interval = 0,

    [ValidateSet("emit", "dry-run", "run")]
    [string]$DispatchMode = "dry-run",

    [string]$ProjectRoot = $null
)

# ── Resolve project root ────────────────────────────────────────────────────
if (-not $ProjectRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path
}

$configPath = Join-Path $ProjectRoot "docs\shared\pipeline\config.md"
$taskNamePrefix = "Dinamica-Pipeline"
$agentScript = Join-Path $ProjectRoot "scripts\pa.ps1"

# ── Helper: read config value ───────────────────────────────────────────────
function Get-ConfigValue($content, $key) {
    $pattern = "(?m)^- ${key}:\s*(.+)$"
    $m = [regex]::Match($content, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
    return $null
}

# ── Helper: read active roles list ──────────────────────────────────────────
function Get-ActiveRoles($content) {
    $roles = @()
    $inBlock = $false
    foreach ($line in $content -split "`r?`n") {
        if ($line -match "^## Roles Active") {
            $inBlock = $true
            continue
        }
        if ($inBlock -and $line -match "^## ") {
            break
        }
        if ($inBlock -and $line -match "^-\s*(\w+):\s*true") {
            $roles += $matches[1]
        }
    }
    return $roles
}

# ── Helper: set config value ────────────────────────────────────────────────
function Set-ConfigValue($content, $key, $value) {
    $pattern = "(?m)(^- ${key}:\s*)(.+)$"
    # Use ${1} to avoid ambiguity when value starts with a digit (e.g., $110 = group 110)
    $replacement = '${1}' + $value
    return [regex]::Replace($content, $pattern, $replacement)
}

# ── Helper: ensure config exists ────────────────────────────────────────────
if (-not (Test-Path $configPath)) {
    Write-Error "Config not found: $configPath"
    exit 1
}

$configContent = Get-Content $configPath -Raw -Encoding UTF8

# ── Command: START ──────────────────────────────────────────────────────────
if ($Command -eq "start") {
    $currentStatus = Get-ConfigValue $configContent "status"
    if ($currentStatus -eq "RUNNING") {
        Write-Host "Pipeline is already RUNNING."
        Write-Host "To restart, run: pipeline-control.ps1 -Command stop; pipeline-control.ps1 -Command start"
        exit 0
    }

    $interval = [int](Get-ConfigValue $configContent "interval_minutes")
    $roles = Get-ActiveRoles $configContent

    if ($roles.Count -eq 0) {
        Write-Error "No active roles found in config."
        exit 1
    }

    Write-Host "========================================"
    Write-Host "STARTING Dinamica Budget Pipeline"
    Write-Host "Project: $ProjectRoot"
    Write-Host "Interval: ${interval} minutes"
    Write-Host "Active roles: $($roles -join ', ')"
    Write-Host "========================================"

    foreach ($role in $roles) {
        $taskName = "${taskNamePrefix}-${role}"
        $action = "powershell.exe"
        $arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"${agentScript}`" ${role}"

        # Remove existing task if present
        $existing = schtasks /Query /TN $taskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            schtasks /Delete /TN $taskName /F | Out-Null
            Write-Host "Removed old task: $taskName"
        }

        # Create new task
        schtasks /Create /TN $taskName /TR "$action $arguments" /SC MINUTE /MO $interval /RL HIGHEST /F | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Created task: $taskName (every ${interval} min)"
        } else {
            Write-Error "Failed to create task: $taskName"
        }
    }

    # Update config
    $now = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    $configContent = Set-ConfigValue $configContent "status" "RUNNING"
    $configContent = Set-ConfigValue $configContent "started_at" $now
    $configContent = Set-ConfigValue $configContent "stopped_at" "null"
    $configContent | Set-Content $configPath -Encoding UTF8 -NoNewline

    Write-Host ""
    Write-Host "Pipeline is now RUNNING."
    Write-Host "Verify with: schtasks /Query /TN ${taskNamePrefix}-*"
    exit 0
}

# ── Command: STOP ───────────────────────────────────────────────────────────
if ($Command -eq "stop") {
    $currentStatus = Get-ConfigValue $configContent "status"
    if ($currentStatus -eq "STOPPED") {
        Write-Host "Pipeline is already STOPPED."
        exit 0
    }

    Write-Host "========================================"
    Write-Host "STOPPING Dinamica Budget Pipeline"
    Write-Host "========================================"

    # Find and delete all pipeline tasks
    $tasks = schtasks /Query /FO CSV /TN "${taskNamePrefix}-*" 2>$null | ConvertFrom-Csv
    foreach ($task in $tasks) {
        $tn = $task.TaskName
        if ($tn -and $tn -match [regex]::Escape($taskNamePrefix)) {
            schtasks /Delete /TN $tn /F | Out-Null
            Write-Host "Stopped task: $tn"
        }
    }

    # Update config
    $now = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    $configContent = Set-ConfigValue $configContent "status" "STOPPED"
    $configContent = Set-ConfigValue $configContent "stopped_at" $now
    $configContent | Set-Content $configPath -Encoding UTF8 -NoNewline

    Write-Host ""
    Write-Host "Pipeline is now STOPPED."
    exit 0
}

# ── Command: TIME_SET ───────────────────────────────────────────────────────
if ($Command -eq "time_set") {
    if ($Interval -le 0) {
        Write-Error "Interval must be a positive integer (minutes). Example: -Interval 15"
        exit 1
    }

    $currentStatus = Get-ConfigValue $configContent "status"

    Write-Host "========================================"
    Write-Host "SETTING Polling Interval"
    Write-Host "New interval: ${Interval} minutes"
    Write-Host "Current pipeline status: $currentStatus"
    Write-Host "========================================"

    # Update config
    $configContent = Set-ConfigValue $configContent "interval_minutes" $Interval
    $configContent | Set-Content $configPath -Encoding UTF8 -NoNewline
    Write-Host "Updated config: $configPath"

    # If running, recreate tasks with new interval
    if ($currentStatus -eq "RUNNING") {
        Write-Host "Pipeline is RUNNING. Recreating tasks with new interval..."
        & $MyInvocation.MyCommand.Definition -Command stop -ProjectRoot $ProjectRoot
        & $MyInvocation.MyCommand.Definition -Command start -ProjectRoot $ProjectRoot -DispatchMode $DispatchMode
    } else {
        Write-Host "Pipeline is STOPPED. New interval will take effect on next start."
    }

    exit 0
}
