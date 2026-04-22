#Requires -RunAsAdministrator
param(
    [string]$DatabaseUrl = "",
    [string]$TcpoFile = "C:\Dinamica-Budget\tabelas\Composições TCPO - PINI.xlsx",
    [string]$PcFile = "C:\Dinamica-Budget\tabelas\PC tabelas.xlsx",
    [switch]$OnlyTcpo,
    [switch]$OnlyPc
)

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Dinamica-Budget"
$pythonExe = "C:\DinamicaBudget\venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Set-Location $repoRoot

$scriptPath = Join-Path $repoRoot "scripts\etl_popular_base_consulta.py"
if (!(Test-Path $scriptPath)) {
    throw "Script ETL nao encontrado: $scriptPath"
}

$args = @($scriptPath, "--tcpo-file", $TcpoFile, "--pc-file", $PcFile)
if ($DatabaseUrl -ne "") {
    $args += @("--database-url", $DatabaseUrl)
}
if ($OnlyTcpo) {
    $args += "--only-tcpo"
}
if ($OnlyPc) {
    $args += "--only-pc"
}

Write-Host "[INFO] Executando ETL de base de consulta (TCPO + PC)..."
& $pythonExe @args
Write-Host "[OK] ETL finalizado."