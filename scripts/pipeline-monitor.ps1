#Requires -Version 5.1
<#
.SYNOPSIS
    Pipeline Monitor - Real-time monitoring every 90 seconds.

.DESCRIPTION
    Runs continuously, checking pipeline status and project health.
    Outputs to console and logs to docs/pipeline/logs/pipeline-monitor.log.

.PARAMETER Interval
    Seconds between checks. Default: 90

.PARAMETER ProjectRoot
    Project root path.

.EXAMPLE
    .\scripts\pipeline-monitor.ps1
    .\scripts\pipeline-monitor.ps1 -Interval 60
#>
param(
    [int]$Interval = 90,

    [string]$ProjectRoot = $null
)

# Resolve project root
if (-not $ProjectRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path
}

# Setup
$logDir = Join-Path $ProjectRoot "docs\pipeline\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logFile = Join-Path $logDir "pipeline-monitor.log"

function Write-Monitor($Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$timestamp [MONITOR] $Message"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

function Get-PipelineStatus {
    $configFile = Join-Path $ProjectRoot "docs\pipeline\config.md"
    $backlogFile = Join-Path $ProjectRoot "docs\BACKLOG.md"

    $status = @{
        Pipeline = "UNKNOWN"
        Interval = 0
        ActiveRoles = @()
        Sprints = @{}
    }

    if (Test-Path $configFile) {
        $content = Get-Content $configFile -Raw
        if ($content -match '- status: (\w+)') { $status.Pipeline = $matches[1] }
        if ($content -match '- interval_minutes: (\d+)') { $status.Interval = [int]$matches[1] }
    }

    if (Test-Path $backlogFile) {
        $lines = Get-Content $backlogFile
        foreach ($line in $lines) {
            if ($line -match '^\| [SC]-(\d+)` \| \s*(\w+)') {
                $status.Sprints[$matches[1]] = $matches[2]
            }
        }
    }

    return $status
}

function Get-RoleInboxStatus {
    $inboxDir = Join-Path $ProjectRoot "docs\roles\inbox"
    $roles = @("po", "supervisor", "sm", "worker", "qa", "git-controller", "research")
    $result = @{}

    foreach ($role in $roles) {
        $inboxFile = Join-Path $inboxDir "${role}-pending.md"
        if (Test-Path $inboxFile) {
            $content = Get-Content $inboxFile -Raw
            $result[$role] = @{
                Pending = ($content -match '\[PENDING\]')
                LastUpdate = (Get-Item $inboxFile).LastWriteTime
            }
        } else {
            $result[$role] = @{
                Pending = $false
                LastUpdate = $null
            }
        }
    }

    return $result
}

function Get-RecentLogs {
    $logs = @()
    $logFiles = Get-ChildItem $logDir -Filter "pipeline-*.log" -ErrorAction SilentlyContinue

    foreach ($file in $logFiles) {
        $lastLines = Get-Content $file.FullName -Tail 5 -ErrorAction SilentlyContinue
        if ($lastLines) {
            $logs += @{
                Role = $file.BaseName -replace 'pipeline-', ''
                LastLines = $lastLines
            }
        }
    }

    return $logs
}

# Main monitoring loop
Write-Monitor "=== PIPELINE MONITOR STARTED (Interval: ${Interval}s) ==="

$runCount = 0
while ($true) {
    $runCount++
    $runTime = Get-Date -Format "HH:mm:ss"

    Write-Monitor "=== RUN #$runCount at $runTime ==="

    # Pipeline status
    $pStatus = Get-PipelineStatus

    Write-Monitor "Pipeline: $($pStatus.Pipeline) | Interval: $($pStatus.Interval)min"

    # Sprint summary
    $done = @()
    $active = @()
    $backlog = @()

    foreach ($sprint in $pStatus.Sprints.GetEnumerator()) {
        $state = $sprint.Value
        if ($state -eq "DONE") { $done += $sprint.Key }
        elseif ($state -in @("INICIADA", "PLAN", "TODO", "TESTED")) { $active += $sprint.Key }
        else { $backlog += $sprint.Key }
    }

    Write-Monitor "Sprints: DONE($($done -join ',')) | ATIVE($($active -join ',')) | BACKLOG($($backlog -join ','))"

    # Role inboxes
    $inboxes = Get-RoleInboxStatus
    $withWork = @()
    foreach ($role in $inboxes.GetEnumerator()) {
        if ($role.Value.Pending) { $withWork += $role.Key }
    }
    if ($withWork.Count -gt 0) {
        Write-Monitor "INBOXES WITH WORK: $($withWork -join ', ')"
    }

    # Quick health check
    $logs = Get-RecentLogs
    $stale = @()
    foreach ($log in $logs) {
        $lastLine = $log.LastLines | Select-Object -Last 1
        if ($lastLine -match '(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})') {
            $logTime = [DateTime]::ParseExact($matches[1], "yyyy-MM-dd HH:mm:ss", $null)
            if ((New-TimeSpan -Start $logTime -End (Get-Date)).TotalMinutes -gt 15) {
                $stale += $log.Role
            }
        }
    }
    if ($stale.Count -gt 0) {
        Write-Monitor "STALE: $($stale -join ', ')"
    }

    Write-Monitor "---"

    Start-Sleep -Seconds $Interval
}