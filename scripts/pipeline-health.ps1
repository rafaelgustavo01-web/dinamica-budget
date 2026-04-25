#Requires -Version 5.1
<#
.SYNOPSIS
    Pipeline Health Check -- Observability dashboard for Dinamica Budget pipeline.

.DESCRIPTION
    Shows current pipeline status, last execution times per role,
    pending messages count, and recent log entries.

.PARAMETER ProjectRoot
    Absolute or relative path to project root.

.EXAMPLE
    .\scripts\pipeline-health.ps1
    .\scripts\pipeline-health.ps1 -ProjectRoot "C:\dinamica-budget"
#>
param(
    [string]$ProjectRoot = $null
)

# -- Resolve project root ---------------------------------------------------
if (-not $ProjectRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path
}

# -- Read config ------------------------------------------------------------
$configPath = Join-Path $ProjectRoot "docs\shared\pipeline\config.md"
$pipelineStatus = "UNKNOWN"
$intervalMinutes = "?"
if (Test-Path $configPath) {
    $cfg = Get-Content $configPath -Raw -Encoding UTF8
    if ($cfg -match "status:\s*(RUNNING|STOPPED)") { $pipelineStatus = $matches[1] }
    if ($cfg -match "interval_minutes:\s*(\d+)") { $intervalMinutes = $matches[1] }
}

# -- Header -----------------------------------------------------------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DINAMICA BUDGET PIPELINE HEALTH" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project:  $ProjectRoot"
Write-Host "Status:   $pipelineStatus"
Write-Host "Interval: ${intervalMinutes} minutes"
Write-Host ""

# -- Check Windows Task Scheduler tasks -------------------------------------
Write-Host "--- Task Scheduler Status ---" -ForegroundColor Yellow
$taskPrefix = "Dinamica-Pipeline"

$taskList = schtasks /Query /FO CSV /NH 2>$null | ConvertFrom-Csv -Header @("HostName","TaskName","Next Run Time","Status","Last Run Time","Last Result","Creator","Schedule","Task To Run","Start In","Comment","State","Batch File","Run As User") | Where-Object { $_.TaskName -match $taskPrefix }

if ($taskList) {
    foreach ($t in $taskList) {
        $role = ($t.TaskName -split "-")[-1]
        $state = $t.Status
        $lastRun = $t."Last Run Time"
        $lastResult = $t."Last Result"
        $nextRun = $t."Next Run Time"

        $resultColor = "White"
        if ($lastResult -eq "0") { $resultColor = "Green" }
        elseif ($lastResult -ne "") { $resultColor = "Red" }

        Write-Host "  [$role]" -NoNewline
        Write-Host " State=$state" -NoNewline
        Write-Host " | LastRun=$lastRun" -NoNewline
        Write-Host " | Result=$lastResult" -NoNewline -ForegroundColor $resultColor
        Write-Host " | Next=$nextRun"
    }
} else {
    Write-Host "  (no tasks found -- pipeline may be STOPPED)" -ForegroundColor DarkGray
}
Write-Host ""

# -- Check log files --------------------------------------------------------
Write-Host "--- Recent Agent Logs ---" -ForegroundColor Yellow
$logDir = Join-Path $ProjectRoot "docs\shared\pipeline\logs"
if (Test-Path $logDir) {
    $logFiles = Get-ChildItem $logDir -Filter "pipeline-*.log" | Sort-Object LastWriteTime -Descending
    if ($logFiles) {
        foreach ($lf in $logFiles) {
            $role = ($lf.BaseName -split "-")[-1]
            $lastWrite = $lf.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            $sizeKB = [math]::Round($lf.Length / 1KB, 1)

            $lastLines = Get-Content $lf.FullName -Tail 3 -ErrorAction SilentlyContinue
            $hasAction = $lastLines | Select-String "STATUS=ACTION_REQUIRED"
            $statusIndicator = if ($hasAction) { "[ACTION REQUIRED]" } else { "[IDLE]" }

            Write-Host "  [$role]" -NoNewline
            Write-Host " LastWrite=$lastWrite" -NoNewline
            Write-Host " Size=${sizeKB}KB" -NoNewline
            Write-Host " $statusIndicator"
        }
    } else {
        Write-Host "  (no log files yet)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  (log directory not found)" -ForegroundColor DarkGray
}
Write-Host ""

# -- Check inboxes for PENDING ----------------------------------------------
Write-Host "--- Inbox PENDING Summary ---" -ForegroundColor Yellow
$rolesDir = Join-Path $ProjectRoot "docs\shared\roles"
$roleFiles = Get-ChildItem $rolesDir -Filter "*-readme.md" -ErrorAction SilentlyContinue

$totalPending = 0
foreach ($rf in $roleFiles) {
    $content = Get-Content $rf.FullName -Raw -Encoding UTF8
    $roleName = $rf.BaseName -replace "-readme$", ""
    $pendingCount = ([regex]::Matches($content, "### \[PENDING\]")).Count
    $totalPending += $pendingCount

    if ($pendingCount -gt 0) {
        Write-Host "  [$roleName]" -NoNewline -ForegroundColor Red
        Write-Host " PENDING=$pendingCount" -ForegroundColor Red
    } else {
        Write-Host "  [$roleName] PENDING=0" -ForegroundColor DarkGray
    }
}
Write-Host ""
Write-Host "TOTAL PENDING across all roles: $totalPending" -ForegroundColor $(if ($totalPending -gt 0) { "Red" } else { "Green" })
Write-Host ""

# -- WIP Check --------------------------------------------------------------
Write-Host "--- WIP Check ---" -ForegroundColor Yellow
$backlogPath = Join-Path $ProjectRoot "docs\shared\governance\BACKLOG.md"
if (Test-Path $backlogPath) {
    $backlog = Get-Content $backlogPath -Raw
    $activeStates = @("INICIADA", "PLAN", "TODO", "TESTED")
    $activeCount = 0
    foreach ($state in $activeStates) {
        $matches = [regex]::Matches($backlog, "\|\s*`?S-\d+`?\s*\|\s*$state")
        $activeCount += $matches.Count
    }
    $maxWip = 4
    if ($backlog -match "max_active_sprints:\s*(\d+)") { $maxWip = [int]$matches[1] }

    $wipColor = if ($activeCount -le $maxWip) { "Green" } else { "Red" }
    Write-Host "  Active sprints: $activeCount / $maxWip" -ForegroundColor $wipColor
} else {
    Write-Host "  (BACKLOG.md not found)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  End of Health Report" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commands:"
Write-Host "  Start pipeline:  .\scripts\pipeline-control.ps1 -Command start"
Write-Host "  Stop pipeline:   .\scripts\pipeline-control.ps1 -Command stop"
Write-Host "  View worker log: Get-Content docs\shared\pipeline\logs\pipeline-worker.log -Tail 20"
Write-Host "  Task Scheduler:  taskschd.msc"
Write-Host ""
