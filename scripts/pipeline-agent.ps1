#Requires -Version 5.1
<#
.SYNOPSIS
    Pipeline Agent - Role Inbox Checker for Dinamica Budget Sprint Orchestration.

.DESCRIPTION
    This script is invoked by the Windows Task Scheduler (or cron/MCP) every N minutes.
    It reads the role file's ## INBOX section, checks for [PENDING] messages,
    and outputs actionable instructions for the agent CLI.

    Logs ALL executions to docs/shared/pipeline/logs/ for observability.

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
    [ValidateSet("po", "supervisor", "sm", "worker", "qa", "git-controller", "git_controller", "research")]
    [string]$Role,

    [string]$ProjectRoot = $null,

    [ValidateSet("run", "emit", "dry-run")]
    [string]$DispatchMode = "emit"
)

# ── Resolve project root ────────────────────────────────────────────────────
if (-not $ProjectRoot) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path
}

# ── Logging setup ───────────────────────────────────────────────────────────
$logDir = Join-Path $ProjectRoot "docs\shared\pipeline\logs"
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

function Normalize-RoleName([string]$InputRole) {
    if (-not $InputRole) { return $InputRole }
    return ($InputRole -replace "_", "-").ToLowerInvariant()
}

function Get-MessageField([string]$Body, [string]$FieldName) {
    $pattern = "(?mi)^- ${FieldName}:\s*(.+)$"
    $match = [regex]::Match($Body, $pattern)
    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

function Get-SprintId([string]$FullText, [string]$Body) {
    $sources = @($FullText, $Body)
    foreach ($source in $sources) {
        if ($source -match "\bSprint\s+(S-\d+)\b") {
            return $matches[1]
        }
    }
    return $null
}

function Resolve-RepoPath([string]$ProjectRoot, [string]$ReferencePath) {
    if (-not $ReferencePath) { return $null }
    $cleanPath = $ReferencePath.Trim()
    if ($cleanPath.StartsWith("@")) {
        $cleanPath = $cleanPath.Substring(1)
    }
    if ([System.IO.Path]::IsPathRooted($cleanPath)) {
        return $cleanPath
    }
    return Join-Path $ProjectRoot $cleanPath
}

function Get-AssignedWorkerIdFromBriefing([string]$ProjectRoot, [string]$BriefingReference) {
    $briefingPath = Resolve-RepoPath -ProjectRoot $ProjectRoot -ReferencePath $BriefingReference
    if (-not $briefingPath -or -not (Test-Path $briefingPath)) {
        return $null
    }

    try {
        $briefingContent = Get-Content $briefingPath -Raw -Encoding UTF8
    } catch {
        return $null
    }

    $patterns = @(
        '(?mi)^- Assigned worker:\s*(.+)$',
        '(?mi)^> \*\*Assigned worker:\*\*\s*(.+)$',
        '(?mi)^- Worker ID:\s*(.+)$',
        '(?mi)^> \*\*Worker ID:\*\*\s*(.+)$'
    )

    foreach ($pattern in $patterns) {
        $match = [regex]::Match($briefingContent, $pattern)
        if ($match.Success) {
            return $match.Groups[1].Value.Trim()
        }
    }

    return $null
}

function Get-WorkerRecord([string]$RegistryPath, [string]$SprintId, [string]$AssignedWorkerId) {
    if (-not (Test-Path $RegistryPath)) { return $null }

    try {
        $registry = Get-Content $RegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        return $null
    }

    if (-not $registry.workers) { return $null }

    if ($AssignedWorkerId) {
        $assigned = $registry.workers | Where-Object { $_.worker_id -eq $AssignedWorkerId } | Select-Object -First 1
        if ($assigned) { return $assigned }
    }

    if ($SprintId) {
        $reserved = $registry.workers | Where-Object { $_.reserved_for_sprint -eq $SprintId } | Select-Object -First 1
        if ($reserved) { return $reserved }
    }

    if (@($registry.workers).Count -eq 1) {
        return $registry.workers | Select-Object -First 1
    }

    return $null
}

function Get-AgentCommandSpec($WorkerRecord) {
    if (-not $WorkerRecord) { return $null }

    $workerId = [string]$WorkerRecord.worker_id
    $provider = [string]$WorkerRecord.provider

    if ($workerId -match "^codex\b" -or $provider -match "OpenAI") {
        return @{
            Executable = "codex"
            PrefixArgs = @()
            Display = "codex"
        }
    }

    if ($workerId -match "^kimi\b" -or $provider -match "Kimi") {
        return @{
            Executable = "kimi-cli"
            PrefixArgs = @()
            Display = "kimi-cli"
        }
    }

    if ($workerId -match "^opencode\b" -or $provider -match "OpenCode") {
        return @{
            Executable = "opencode"
            PrefixArgs = @("--no-interactive")
            Display = "opencode --no-interactive"
        }
    }

    if ($workerId -match "^gemini\b" -or $provider -match "Google") {
        return @{
            Executable = "gemini"
            PrefixArgs = @()
            Display = "gemini"
        }
    }

    return $null
}

function New-AgentPrompt([string]$RoleName, $Message, [string]$RoleFilePath) {
    $action = Get-MessageField $Message.Body "Action"
    $briefing = Get-MessageField $Message.Body "Briefing"
    $plan = Get-MessageField $Message.Body "Plan"
    $sprintId = Get-SprintId $Message.FullText $Message.Body

    # Role-specific friendly names for the prompt introduction
    $roleDisplay = switch ($RoleName) {
        "worker"        { "Worker de execução" }
        "qa"            { "QA" }
        "supervisor"    { "Supervisor técnico" }
        "sm"            { "Scrum Master" }
        "research"      { "Researcher (Analista de Dados/ML)" }
        "po"            { "Product Owner" }
        "git-controller"{ "Git Controller" }
        default         { $RoleName }
    }

    $parts = @(
        "Você é o $roleDisplay deste projeto. Leia sua introdução em $RoleFilePath e processe apenas as mensagens [PENDING]."
    )

    if ($sprintId) { $parts += "Sprint: $sprintId." }
    if ($action)   { $parts += "Action: $action." }
    if ($briefing) { $parts += "Briefing: $briefing." }
    if ($plan)     { $parts += "Plan: $plan." }

    $parts += "Siga o protocolo da role, execute apenas o escopo aprovado e atualize inbox/artefatos ao concluir."

    return ($parts -join " ")
}

function Format-CommandLine([string]$Executable, [string[]]$Arguments) {
    $escapedArgs = foreach ($arg in $Arguments) {
        '"' + ($arg -replace '"', '\"') + '"'
    }
    return (($Executable) + " " + ($escapedArgs -join " ")).Trim()
}

function Invoke-AgentCommand([string]$Executable, [string[]]$Arguments, [string]$WorkingDirectory) {
    Push-Location $WorkingDirectory
    try {
        & $Executable @Arguments
        if ($null -ne $LASTEXITCODE) { return $LASTEXITCODE }
        return 0
    } finally {
        Pop-Location
    }
}

# ── Read config ─────────────────────────────────────────────────────────────
$configPath = Join-Path $ProjectRoot "docs\shared\pipeline\config.md"
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
$normalizedRole = Normalize-RoleName $Role
$roleFileName = switch ($normalizedRole) {
    "po"            { "po-readme.md" }
    "supervisor"    { "supervisor-readme.md" }
    "sm"            { "sm-readme.md" }
    "worker"        { "worker-readme.md" }
    "qa"            { "qa-readme.md" }
    "git-controller"{ "git-controller.md" }
    "research"      { "research-readme.md" }
}
$roleFilePath = Join-Path (Join-Path $ProjectRoot "docs\shared\roles") $roleFileName

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
$normalizedInboxSection = $inboxSection -replace ([string][char]0x2014), "--"
$messagePattern = '(?ms)^### \[(PENDING|DONE|BLOCKED)\]\s+([^\r\n]+?)\s+--\s+(.*?)\r?\n(?=^### \[(PENDING|DONE|BLOCKED)\]|\z)'
$matches = [regex]::Matches($normalizedInboxSection, $messagePattern)

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
Write-Log "INFO" "Total messages in inbox: $($allMessages.Count) | PENDING: $($pendingMessages.Count) | DONE: $(@($allMessages | Where-Object { $_.Status -eq 'DONE' }).Count) | BLOCKED: $(@($allMessages | Where-Object { $_.Status -eq 'BLOCKED' }).Count)"

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

$registryPath = Join-Path $ProjectRoot "templates\workers.json"

for ($i = 0; $i -lt $pendingMessages.Count; $i++) {
    $msg = $pendingMessages[$i]
    $action = Get-MessageField $msg.Body "Action"
    $briefing = Get-MessageField $msg.Body "Briefing"
    $plan = Get-MessageField $msg.Body "Plan"
    $sprintId = Get-SprintId $msg.FullText $msg.Body

    Write-Host "----------------------------------------"
    Write-Host "[$($i + 1)/$($pendingMessages.Count)] PENDING"
    Write-Host "Timestamp: $($msg.Timestamp)"
    Write-Host "Body:"
    Write-Host $msg.Body
    Write-Host ""
    Write-Log "ACTION" "PENDING msg [$($i + 1)/$($pendingMessages.Count)] ts=$($msg.Timestamp)"

    if ($action) { Write-Host "ACTION: $action" }
    if ($sprintId) { Write-Host "SPRINT: $sprintId" }
    if ($briefing) { Write-Host "BRIEFING: $briefing" }
    if ($plan) { Write-Host "PLAN: $plan" }

    if ($normalizedRole -eq "worker") {
        $assignedWorkerId = Get-AssignedWorkerIdFromBriefing -ProjectRoot $ProjectRoot -BriefingReference $briefing
        $workerRecord = Get-WorkerRecord -RegistryPath $registryPath -SprintId $sprintId -AssignedWorkerId $assignedWorkerId
        $commandSpec = Get-AgentCommandSpec $workerRecord
        $agentPrompt = New-AgentPrompt -RoleName $normalizedRole -Message $msg -RoleFilePath $roleFilePath

        if ($workerRecord) {
            Write-Host "CLI_TARGET: $($workerRecord.worker_id) [$($workerRecord.provider)]"
        } else {
            Write-Host "CLI_TARGET: unresolved"
        }

        if ($commandSpec) {
            $commandArgs = @($commandSpec.PrefixArgs + @($agentPrompt))
            $commandLine = Format-CommandLine -Executable $commandSpec.Executable -Arguments $commandArgs

            Write-Host "CLI_WORKDIR: $ProjectRoot"
            Write-Host "CLI_COMMAND: $commandLine"
            Write-Log "ACTION" "CLI_TARGET=$($workerRecord.worker_id) CLI_WORKDIR=$ProjectRoot CLI_COMMAND=$commandLine"

            if ($DispatchMode -eq "run") {
                $commandExists = Get-Command $commandSpec.Executable -ErrorAction SilentlyContinue
                if ($commandExists) {
                    $exitCode = Invoke-AgentCommand -Executable $commandSpec.Executable -Arguments $commandArgs -WorkingDirectory $ProjectRoot
                    Write-Log "ACTION" "CLI_EXIT_CODE=$exitCode"
                } else {
                    Write-Host "CLI_STATUS: executable not found"
                    Write-Log "WARN" "CLI executable not found: $($commandSpec.Executable)"
                }
            } elseif ($DispatchMode -eq "dry-run") {
                Write-Host "CLI_STATUS: dry-run"
                Write-Log "INFO" "CLI dry-run only"
            } else {
                Write-Host "CLI_STATUS: emit-only"
                Write-Log "INFO" "CLI emit-only"
            }
        } else {
            Write-Host "CLI_STATUS: no command mapping for assigned worker"
            Write-Log "WARN" "No CLI mapping found for assigned worker"
        }
        Write-Host ""
    }
}

Write-Host "========================================"
Write-Host "INSTRUCTION: Process the above pending message(s), then mark them as [DONE] in:"
Write-Host "  $roleFilePath"
Write-Host "========================================"
Write-Log "ACTION" "STATUS=ACTION_REQUIRED | Pending=$($pendingMessages.Count)"

exit 0
