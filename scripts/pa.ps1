#Requires -Version 5.1
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Role,

    [Parameter(Position = 1)]
    [ValidateSet("emit", "dry-run", "run")]
    [string]$DispatchMode = "run"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Resolve-Path (Join-Path $scriptDir "..") | Select-Object -ExpandProperty Path

# Load user + machine PATH so CLIs (kimi, codex, etc.) are found when invoked by Task Scheduler
$machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = ($machinePath, $userPath, $env:Path) -join ";"

Set-Location -LiteralPath $projectRoot
& (Join-Path $scriptDir "pipeline-agent.ps1") -Role $Role -ProjectRoot $projectRoot -DispatchMode $DispatchMode
