# ──────────────────────────────────────────────────────────────────────────────
# backup-db.ps1 — Backup do PostgreSQL com retencao de 30 dias
#
# Uso:
#   .\backup-db.ps1
#   .\backup-db.ps1 -RetentionDays 15
#
# Recomendacao: Agendar via Task Scheduler para rodar diariamente
#   schtasks /create /tn "DinamicaBudget-Backup" /tr "powershell -File C:\apps\dinamica-budget\scripts\backup-db.ps1" /sc daily /st 02:00
# ──────────────────────────────────────────────────────────────────────────────

param(
    [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"
$appRoot = "C:\apps\dinamica-budget"
$backupDir = "$appRoot\backups"
$logFile = "$appRoot\logs\backup.log"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

function Log($msg) {
    $entry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Write-Host $entry
    Add-Content -Path $logFile -Value $entry -ErrorAction SilentlyContinue
}

# ── Criar pastas ──────────────────────────────────────────────────────────────
foreach ($dir in @($backupDir, "$appRoot\logs")) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# ── Carregar .env para pegar DATABASE_URL ─────────────────────────────────────
$envFile = "$appRoot\.env"
if (-not (Test-Path $envFile)) {
    Log "ERRO: .env nao encontrado em $envFile"
    exit 1
}

$dbHost = "localhost"
$dbPort = "5432"
$dbName = "dinamica_budget"
$dbUser = "postgres"

$envContent = Get-Content $envFile
foreach ($line in $envContent) {
    if ($line -match "^\s*DATABASE_URL\s*=\s*postgresql.*?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(\w+)") {
        $dbUser = $Matches[1]
        # Password via PGPASSWORD env var
        [System.Environment]::SetEnvironmentVariable("PGPASSWORD", $Matches[2], "Process")
        $dbHost = $Matches[3]
        if ($Matches[4]) { $dbPort = $Matches[4] }
        $dbName = $Matches[5]
    }
}

$backupFile = "$backupDir\${dbName}_${timestamp}.sql"

Log "=== BACKUP INICIADO ==="
Log "Database: $dbName@$dbHost:$dbPort"
Log "Arquivo:  $backupFile"

# ── Executar pg_dump ──────────────────────────────────────────────────────────
$pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDump) {
    # Tentar caminho padrao PostgreSQL 16
    $pgDump = "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"
    if (-not (Test-Path $pgDump)) {
        Log "ERRO: pg_dump nao encontrado. Adicione ao PATH ou instale PostgreSQL client tools."
        exit 1
    }
} else {
    $pgDump = $pgDump.Source
}

& $pgDump -h $dbHost -p $dbPort -U $dbUser -d $dbName -F p -f $backupFile
if ($LASTEXITCODE -ne 0) {
    Log "ERRO: pg_dump falhou (exit code: $LASTEXITCODE)"
    # Limpar PGPASSWORD
    [System.Environment]::SetEnvironmentVariable("PGPASSWORD", $null, "Process")
    exit 1
}

# Limpar PGPASSWORD da memoria do processo
[System.Environment]::SetEnvironmentVariable("PGPASSWORD", $null, "Process")

$size = (Get-Item $backupFile).Length / 1MB
Log "Backup concluido: $([math]::Round($size, 2)) MB"

# ── Limpar backups antigos ────────────────────────────────────────────────────
Log "Removendo backups com mais de $RetentionDays dias..."
$cutoff = (Get-Date).AddDays(-$RetentionDays)
$removed = 0
Get-ChildItem -Path $backupDir -Filter "*.sql" | Where-Object { $_.LastWriteTime -lt $cutoff } | ForEach-Object {
    Remove-Item $_.FullName -Force
    $removed++
}
Log "Backups removidos: $removed"

Log "=== BACKUP FINALIZADO ==="
