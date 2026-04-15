<#
.SYNOPSIS
    Dinamica Budget - Configura banco PostgreSQL.
    Le o .env diretamente (suporta senhas com !, @, # etc).
    Se nenhuma senha funcionar, reseta via pg_hba.conf automaticamente.
#>
param(
    [string]$EnvFile = "C:\DinamicaBudget\.env",
    [string]$PsqlBin = "",
    [string]$DbName  = "dinamica_budget",
    [string]$SvcName = ""
)

$ErrorActionPreference = 'Continue'

# ─────────────────────────────────────────────────────────────────────────────
# Funcoes auxiliares (definidas no topo, fora de qualquer bloco)
# ─────────────────────────────────────────────────────────────────────────────

function Write-NoBOM {
    param([string]$Path, [string]$Content)
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

function Read-NoBOM {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function Wait-Port {
    param([string]$H, [int]$P, [int]$Sec = 30)
    $deadline = (Get-Date).AddSeconds($Sec)
    while ((Get-Date) -lt $deadline) {
        $tc = New-Object System.Net.Sockets.TcpClient
        try   { $tc.Connect($H, $P); $tc.Close(); return $true  }
        catch { Start-Sleep -Seconds 2 }
    }
    return $false
}

function Reload-Pg {
    param([string]$PgCtl, [string]$DataDir, [string]$Svc, [int]$Port)
    if ($PgCtl -and (Test-Path $PgCtl)) {
        & $PgCtl reload -D $DataDir 2>&1 | Out-Null
        Start-Sleep -Seconds 3
    } elseif ($Svc) {
        Write-Host "[INFO] Reiniciando $Svc..."
        Restart-Service $Svc -Force -ErrorAction SilentlyContinue
        $null = Wait-Port '127.0.0.1' $Port 45
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Localiza psql
# ─────────────────────────────────────────────────────────────────────────────
if (-not $PsqlBin -or -not (Test-Path $PsqlBin)) {
    foreach ($v in 17, 16, 15, 14) {
        $c = "C:\Program Files\PostgreSQL\$v\bin\psql.exe"
        if (Test-Path $c) { $PsqlBin = $c; break }
    }
}
if (-not $PsqlBin -or -not (Test-Path $PsqlBin)) {
    $f = Get-Command psql -ErrorAction SilentlyContinue
    if ($f) { $PsqlBin = $f.Source }
}
if (-not (Test-Path $PsqlBin)) {
    Write-Host "[FAIL] psql nao encontrado"
    exit 1
}

# Pg bin dir para pg_ctl
$pgBinDir = Split-Path $PsqlBin -Parent
$pgCtlExe = Join-Path $pgBinDir "pg_ctl.exe"

# ─────────────────────────────────────────────────────────────────────────────
# Detecta servico PostgreSQL se nao informado
# ─────────────────────────────────────────────────────────────────────────────
if (-not $SvcName) {
    foreach ($s in 'postgresql-x64-16','postgresql-x64-17','postgresql-x64-15','postgresql-x64-14','postgresql') {
        if (Get-Service $s -ErrorAction SilentlyContinue) { $SvcName = $s; break }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Le e valida o .env
# ─────────────────────────────────────────────────────────────────────────────
if (-not (Test-Path $EnvFile)) {
    Write-Host "[FAIL] .env nao encontrado: $EnvFile"
    exit 1
}

$envLines = Get-Content $EnvFile -Encoding UTF8
$dbUrlLine = $envLines | Where-Object { $_ -match '^DATABASE_URL=' }
if (-not $dbUrlLine) {
    Write-Host "[FAIL] DATABASE_URL nao encontrado em $EnvFile"
    exit 1
}

$dbUrl = ($dbUrlLine -split '=', 2)[1].Trim()

# Valida campos obrigatorios
foreach ($k in @('DATABASE_URL','SECRET_KEY','ROOT_USER_EMAIL','ROOT_USER_PASSWORD')) {
    $kl = $envLines | Where-Object { $_ -match "^$k=" }
    if (-not $kl) {
        Write-Host "[WARN] Campo ausente no .env: $k"
    } elseif (($kl -split '=',2)[1] -match '^(password|CHANGE_ME|your_password|placeholder|changeme)$') {
        Write-Host "[WARN] $k contem valor placeholder"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Parse DATABASE_URL
# ─────────────────────────────────────────────────────────────────────────────
if ($dbUrl -notmatch 'postgresql(?:\+\w+)?://([^:@]+):(.+)@([^:/]+):(\d+)/([^/?]+)') {
    Write-Host "[FAIL] Nao foi possivel interpretar DATABASE_URL: $dbUrl"
    exit 1
}
$pgUser = $Matches[1]
$pgPass = $Matches[2]
$pgHost = $Matches[3]
$pgPort = [int]$Matches[4]

Write-Host "[INFO] Testando conexao: $pgUser@${pgHost}:${pgPort}..."

# ─────────────────────────────────────────────────────────────────────────────
# Tenta lista de senhas conhecidas em hosts possiveis
# ─────────────────────────────────────────────────────────────────────────────
$candidates = @($pgPass, 'PostgresSetup123!', 'postgres', 'Postgres',
                'Dinamica!123', 'Dinamica123', 'Dinamica@2024',
                'Postgres@2024', 'admin', 'Admin@123', '') | Select-Object -Unique

$hosts = @($pgHost)
if ($pgHost -eq 'localhost') { $hosts = @('localhost','127.0.0.1') }

$okPass = $null
$okHost = $pgHost

foreach ($tryPass in $candidates) {
    $env:PGPASSWORD = $tryPass
    foreach ($tryHost in $hosts) {
        $out = & $PsqlBin -U $pgUser -h $tryHost -p $pgPort -tAc 'SELECT 1' 2>&1
        if ($LASTEXITCODE -eq 0) {
            $okPass = $tryPass
            $okHost = $tryHost
            break
        }
    }
    if ($null -ne $okPass) { break }
}

# ─────────────────────────────────────────────────────────────────────────────
# Se nenhuma senha funcionou: reset via pg_hba.conf (ultimo recurso)
# ─────────────────────────────────────────────────────────────────────────────
if ($null -eq $okPass) {
    Write-Host "[WARN] Nenhuma senha conhecida funcionou. Iniciando reset via pg_hba.conf..."

    # Localiza pasta de dados
    $pgData = $null
    foreach ($v in 17, 16, 15, 14) {
        $d = "C:\Program Files\PostgreSQL\$v\data"
        if (Test-Path "$d\pg_hba.conf") { $pgData = $d; break }
    }
    if (-not $pgData) {
        foreach ($v in 17, 16, 15, 14) {
            $rk = "HKLM:\SOFTWARE\PostgreSQL\Installations\postgresql-x64-$v"
            if (Test-Path $rk) {
                $dd = (Get-ItemProperty $rk -ErrorAction SilentlyContinue).DataDirectory
                if ($dd -and (Test-Path "$dd\pg_hba.conf")) { $pgData = $dd; break }
            }
        }
    }
    if (-not $pgData) {
        Write-Host "[FAIL] Pasta de dados do PostgreSQL nao encontrada. Reset impossivel."
        Write-Host "[FAIL] Corrija manualmente a senha em DATABASE_URL no .env"
        exit 1
    }

    $hbaPath = Join-Path $pgData "pg_hba.conf"
    Write-Host "[INFO] pg_hba.conf: $hbaPath"

    # Salva backup e injeta regras trust (sem BOM)
    $hbaOriginal = Read-NoBOM $hbaPath
    $trustBlock  = "# TEMP deploy trust`r`n" +
                   "host all all 127.0.0.1/32 trust`r`n" +
                   "host all all ::1/128 trust`r`n"
    Write-NoBOM $hbaPath ($trustBlock + $hbaOriginal)

    Write-Host "[INFO] Recarregando pg_hba.conf..."
    Reload-Pg $pgCtlExe $pgData $SvcName $pgPort

    # Testa trust
    $env:PGPASSWORD = ""
    $ok = & $PsqlBin -U $pgUser -h 127.0.0.1 -p $pgPort -tAc 'SELECT 1' 2>&1
    if ($LASTEXITCODE -ne 0) {
        # Restaura e sai
        Write-NoBOM $hbaPath $hbaOriginal
        Reload-Pg $pgCtlExe $pgData $SvcName $pgPort
        Write-Host "[FAIL] Conexao trust falhou. Verifique se postgresql esta rodando."
        Write-Host "[FAIL] sc query $SvcName"
        exit 1
    }

    # Define nova senha
    $newPass = 'PostgresSetup123!'
    $null = & $PsqlBin -U $pgUser -h 127.0.0.1 -p $pgPort -c "ALTER USER $pgUser WITH PASSWORD '$newPass'" 2>&1
    Write-Host "[OK] Senha redefinida para: PostgresSetup123!"

    # Restaura pg_hba.conf
    Write-NoBOM $hbaPath $hbaOriginal
    Write-Host "[INFO] pg_hba.conf restaurado. Recarregando..."
    Reload-Pg $pgCtlExe $pgData $SvcName $pgPort

    # Confirma nova senha
    $env:PGPASSWORD = $newPass
    $null = Wait-Port '127.0.0.1' $pgPort 25
    $null = & $PsqlBin -U $pgUser -h 127.0.0.1 -p $pgPort -tAc 'SELECT 1' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Senha redefinida mas conexao ainda falhou."
        exit 1
    }

    # Atualiza .env
    $escapedOldPass = [regex]::Escape($pgPass)
    $escapedOldHost = [regex]::Escape($pgHost)
    $newUrl  = $dbUrl -replace "(?<=://[^:]+:)$escapedOldPass(?=@)", $newPass
    $newUrl  = $newUrl -replace "(?<=@)$escapedOldHost(?=:)", "127.0.0.1"
    Set-Content $EnvFile ($envLines -replace [regex]::Escape($dbUrlLine), "DATABASE_URL=$newUrl") -Encoding UTF8
    Write-Host "[OK] DATABASE_URL atualizado no .env"

    $okPass = $newPass
    $okHost = '127.0.0.1'
    $pgPass = $newPass
    $pgHost = '127.0.0.1'
}

# Atualiza .env se senha/host mudou
if ($okPass -ne $pgPass -or $okHost -ne $pgHost) {
    $escapedOldPass = [regex]::Escape($pgPass)
    $escapedOldHost = [regex]::Escape($pgHost)
    $newUrl  = $dbUrl -replace "(?<=://[^:]+:)$escapedOldPass(?=@)", $okPass
    $newUrl  = $newUrl -replace "(?<=@)$escapedOldHost(?=:)", $okHost
    Set-Content $EnvFile ($envLines -replace [regex]::Escape($dbUrlLine), "DATABASE_URL=$newUrl") -Encoding UTF8
    Write-Host "[OK] DATABASE_URL atualizado no .env (senha/host corrigidos)"
    $pgPass = $okPass
    $pgHost = $okHost
}

Write-Host "[OK] Conexao PostgreSQL estabelecida como $pgUser@${pgHost}:${pgPort}"
$env:PGPASSWORD = $pgPass

# ─────────────────────────────────────────────────────────────────────────────
# Cria banco se nao existir
# ─────────────────────────────────────────────────────────────────────────────
# Converte output para string unica para evitar false positive com arrays
$dbChkRaw = & $PsqlBin -U $pgUser -h $pgHost -p $pgPort -tAc "SELECT 1 FROM pg_database WHERE datname='$DbName'" 2>&1
$dbChk = ($dbChkRaw | Where-Object { $_ -match '^\s*\d+\s*$' } | Select-Object -First 1) -replace '\s',''
if ($dbChk -ne '1') {
    Write-Host "[INFO] Criando banco $DbName..."
    $r = & $PsqlBin -U $pgUser -h $pgHost -p $pgPort -c "CREATE DATABASE $DbName" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] Falha ao criar banco: $r"
        exit 1
    }
    Write-Host "[OK] Banco $DbName criado"
} else {
    Write-Host "[SKIP] Banco $DbName ja existe"
}

# ─────────────────────────────────────────────────────────────────────────────
# Cria extensoes
# ─────────────────────────────────────────────────────────────────────────────
Write-Host "[INFO] Configurando extensoes no banco $DbName..."

$r = & $PsqlBin -U $pgUser -h $pgHost -p $pgPort -d $DbName -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] pgvector nao disponivel: $r"
    Write-Host "[PEND] Instalar pgvector: https://github.com/pgvector/pgvector/releases"
} else {
    Write-Host "[OK] Extensao vector ativa"
}

$r = & $PsqlBin -U $pgUser -h $pgHost -p $pgPort -d $DbName -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] pg_trgm falhou: $r"
} else {
    Write-Host "[OK] Extensao pg_trgm ativa"
}

$env:PGPASSWORD = ""
Write-Host "[OK] PostgreSQL: banco e extensoes configurados"
exit 0
