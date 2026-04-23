#Requires -Version 5.1
<#
.SYNOPSIS
    Pipeline Agent - Role Inbox Checker for Dinamica Budget Sprint Orchestration.

.DESCRIPTION
    This script is invoked by the Windows Task Scheduler (or cron/MCP) every N minutes.
    It reads the role file's ## INBOX section, checks for [PENDING] messages,
    and outputs actionable instructions for the agent CLI.

    Logs ALL executions to docs/pipeline/logs/ for observability.

.PARAMETER Role
    The role name to check: po, supervisor, sm, worker, qa, git-controller, research

.PARAMETER ProjectRoot
    Absolute or relative path to the project root. Defaults to parent of scripts/.

.EXAMPLE
    .\scripts\pipeline-agent.ps1 -Role worker
    .\scripts\pipeline-agent.ps1 -Role qa -ProjectRoot "C:\dinamica-budget"
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("po", "supervisor", "sm", "worker", "qa", "git-controller", "research")]
    [string]$Role,

    [string]$ProjectRoot = $null
)

# ── Resolve project root ────────────────────────────────────────────────────
if (-not $ProjectRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path
}

# ── Logging setup ───────────────────────────────────────────────────────────
$logDir = Join-Path $ProjectRoot "docs\pipeline\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logFile = Join-Path $logDir "pipeline-${Role}.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Log($Level, $Message) {
    $line = "$timestamp [$Level] [$Role] $Message"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    # Also output to console so Task Scheduler captures it if not hidden
    Write-Host $line
}

# ── Read config ─────────────────────────────────────────────────────────────
$configPath = Join-Path $ProjectRoot "docs\pipeline\config.md"
$intervalMinutes = 10
$pipelineStatus = "UNKNOWN"
if (Test-Path $configPath) {
    $configContent = Get-Content $configPath -Raw -Encoding UTF8
    if ($configContent -match "interval_minutes:\s*(\d+)") {
        $intervalMinutes = [int]$matches[1]
    }
    if ($configContent -match "status:\s*(RUNNING|STOPPED)") {
        $pipelineStatus = $matches[1]
    }
}

# ── Early exit if STOPPED ───────────────────────────────────────────────────
if ($pipelineStatus -eq "STOPPED") {
    Write-Log "INFO" "Pipeline STOPPED. Exiting."
    exit 0
}

# ── Resolve role file ───────────────────────────────────────────────────────
$roleFileName = switch ($Role) {
    "po"            { "po-readme.md" }
    "supervisor"    { "supervisor-readme.md" }
    "sm"            { "sm-readme.md" }
    "worker"        { "worker-readme.md" }
    "qa"            { "qa-readme.md" }
    "git-controller"{ "git-controller.md" }
    "research"      { "research-readme.md" }
}
$roleFilePath = Join-Path (Join-Path $ProjectRoot "docs\roles") $roleFileName

if (-not (Test-Path $roleFilePath)) {
    Write-Log "ERROR" "Role file not found: $roleFilePath"
    exit 1
}

# ── Read role file and extract INBOX ────────────────────────────────────────
$roleContent = Get-Content $roleFilePath -Raw -Encoding UTF8

# Extract ## INBOX section (everything after "## INBOX" until end or next ##)
$inboxMatch = [regex]::Match($roleContent, "(?ms)## INBOX\s*\n(.*)$")
$inboxSection = ""
if ($inboxMatch.Success) {
    $inboxSection = $inboxMatch.Groups[1].Value
}

# ── Parse [PENDING] messages ────────────────────────────────────────────────
$pendingMessages = @()
$allMessages = @()
$messagePattern = "(?ms)### \[(PENDING|DONE|BLOCKED)\]\s+(\S+)\s+--\s+(.*?)\n(?=### \[(PENDING|DONE|BLOCKED)\]|\z)"
$matches = [regex]::Matches($inboxSection, $messagePattern)

foreach ($m in $matches) {
    $status = $m.Groups[1].Value
    $msgTimestamp = $m.Groups[2].Value
    $body = $m.Groups[3].Value.Trim()

    $msgObj = [PSCustomObject]@{
        Status    = $status
        Timestamp = $msgTimestamp
        Body      = $body
        FullText  = $m.Value.Trim()
    }
    $allMessages += $msgObj
    if ($status -eq "PENDING") {
        $pendingMessages += $msgObj
    }
}

# ── Log execution summary ───────────────────────────────────────────────────
Write-Log "INFO" "=== AGENT CYCLE === Role:$Role Interval:${intervalMinutes}min Pipeline:$pipelineStatus"
Write-Log "INFO" "Total messages in inbox: $($allMessages.Count) | PENDING: $($pendingMessages.Count) | DONE: $(($allMessages | Where-Object { $_.Status -eq 'DONE' }).Count) | BLOCKED: $(($allMessages | Where-Object { $_.Status -eq 'BLOCKED' }).Count)"

# ── Output for agent CLI ────────────────────────────────────────────────────
Write-Host "========================================"
Write-Host "PIPELINE AGENT - Role: $Role"
Write-Host "Project: $ProjectRoot"
Write-Host "Config interval: ${intervalMinutes}min"
Write-Host "Role file: $roleFilePath"
Write-Host "========================================"

if ($pendingMessages.Count -eq 0) {
    Write-Host ""
    Write-Host "STATUS: IDLE"
    Write-Host "No [PENDING] messages in inbox."
    Write-Host "Next check in ${intervalMinutes} minutes."
    Write-Host ""
    Write-Log "INFO" "STATUS=IDLE | No action required"
    exit 0
}

Write-Host ""
Write-Host "STATUS: ACTION REQUIRED"
Write-Host "Pending messages: $($pendingMessages.Count)"
Write-Host ""

for ($i = 0; $i -lt $pendingMessages.Count; $i++) {
    $msg = $pendingMessages[$i]
    Write-Host "----------------------------------------"
    Write-Host "[$($i + 1)/$($pendingMessages.Count)] PENDING"
    Write-Host "Timestamp: $($msg.Timestamp)"
    Write-Host "Body:"
    Write-Host $msg.Body
    Write-Host ""
    Write-Log "ACTION" "PENDING msg [$($i + 1)/$($pendingMessages.Count)] ts=$($msg.Timestamp)"
}

Write-Host "========================================"
Write-Host "INSTRUCTION: Process the above pending message(s), then mark them as [DONE] in:"
Write-Host "  $roleFilePath"
Write-Host "========================================"
Write-Log "ACTION" "STATUS=ACTION_REQUIRED | Pending=$($pendingMessages.Count)"

exit 0
