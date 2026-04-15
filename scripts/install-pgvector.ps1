<#
.SYNOPSIS
    Instala pgvector para PostgreSQL 16 no Windows.
    Requer execucao como Administrador.
    Uso: powershell -ExecutionPolicy Bypass -File install-pgvector.ps1
#>
param(
    [string]$PgRoot    = 'C:\Program Files\PostgreSQL\16',
    [string]$DbName    = 'dinamica_budget',
    [string]$EnvFile   = 'C:\DinamicaBudget\.env',
    [string]$DeployDir = 'C:\DinamicaBudget'
)

$ErrorActionPreference = 'Continue'
$log = 'C:\Dinamica-Budget\logs\install-pgvector.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
"=== install-pgvector.ps1 $(Get-Date) ===" | Out-File $log -Encoding utf8

function Log {
    param([string]$msg)
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content $log $line -Encoding utf8
}

function Die {
    param([string]$msg)
    Log "[FATAL] $msg"
    exit 1
}

function RunPsql {
    param([string]$sql)
    return (& $psql -U postgres -h 127.0.0.1 -d $DbName -t -c $sql 2>&1)
}

# ── Ler senha do .env ────────────────────────────────────────────────────────
$pgPass = 'PostgresSetup123!'
if (Test-Path $EnvFile) {
    $urlLine = Get-Content $EnvFile | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
    if ($urlLine -match '://[^:]+:([^@]+)@') {
        $pgPass = $Matches[1]
    }
}
$env:PGPASSWORD = $pgPass
$psql     = "$PgRoot\bin\psql.exe"
$ctrlFile = "$PgRoot\share\extension\vector.control"
Log "PG password length: $($pgPass.Length)"

# ── Etapa 1: verificar se ja ativo ──────────────────────────────────────────
Log "[1] Verificando extensao vector no banco..."
$extRow = RunPsql "SELECT count(*) FROM pg_extension WHERE extname='vector';"
$extCount = ($extRow | Where-Object { $_ -match '^\s*\d' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)

if ($extCount -eq '1') {
    Log "[1] Extensao vector ja ativa."
} elseif (Test-Path $ctrlFile) {
    Log "[1] Binario ja existe, ativando extensao..."
    $out = (& $psql -U postgres -h 127.0.0.1 -d $DbName -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1)
    foreach ($l in $out) { Log "  psql>> $l" }
} else {
    Log "[1] pgvector nao instalado. Iniciando processo de instalacao completa..."

    # ── Etapa 2: localizar compilador C ──────────────────────────────────────
    Log "[2] Procurando compilador C (vcvars64.bat)..."
    $vcvarsList = @(
        'C:\BuildTools\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat',
        'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat'
    )
    $buildPath = ''
    foreach ($p in $vcvarsList) {
        if (Test-Path $p) { $buildPath = $p ; break }
    }

    if (-not $buildPath) {
        Log "[2] Nenhum compilador encontrado. Baixando VS Build Tools (~2.5 GB)..."
        Log "[2] Isso pode levar 15-30 minutos..."
        $vsExe = Join-Path $env:TEMP 'vs_BuildTools.exe'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        try {
            (New-Object System.Net.WebClient).DownloadFile(
                'https://aka.ms/vs/17/release/vs_BuildTools.exe', $vsExe)
            Log "[2] Bootstrapper: $((Get-Item $vsExe).Length) bytes"
        } catch {
            Die "Falha ao baixar VS Build Tools: $_"
        }

        $vsArgStr = '--quiet --wait --norestart --nocache --installPath "C:\BuildTools" --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'
        Log "[2] Instalando VS Build Tools..."
        $proc = Start-Process -FilePath $vsExe -ArgumentList $vsArgStr -Wait -PassThru
        Log "[2] VS Build Tools exit code: $($proc.ExitCode)"

        foreach ($p in $vcvarsList) {
            if (Test-Path $p) { $buildPath = $p ; break }
        }
        if (-not $buildPath) {
            Die "vcvars64.bat nao encontrado apos instalacao."
        }
    }
    Log "[2] Compilador: $buildPath"

    # ── Etapa 3: baixar fonte do pgvector ─────────────────────────────────────
    Log "[3] Baixando pgvector v0.8.0 (fonte)..."
    $pgvZip = Join-Path $env:TEMP 'pgvector-src.zip'
    $pgvDir = Join-Path $env:TEMP 'pgvector-src'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    try {
        (New-Object System.Net.WebClient).DownloadFile(
            'https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.0.zip',
            $pgvZip)
        Log "[3] Fonte baixado: $((Get-Item $pgvZip).Length) bytes"
    } catch {
        Die "Falha ao baixar fonte: $_"
    }
    if (Test-Path $pgvDir) { Remove-Item $pgvDir -Recurse -Force }
    Expand-Archive -Path $pgvZip -DestinationPath $pgvDir -Force

    $makefileItem = Get-ChildItem $pgvDir -Filter 'Makefile.win' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $makefileItem) { Die "Makefile.win nao encontrado no zip." }
    $pgvSrcDir = $makefileItem.DirectoryName
    Log "[3] Fonte em: $pgvSrcDir"

    # ── Etapa 4: compilar usando arquivo .bat intermediario ──────────────────
    Log "[4] Compilando pgvector..."
    $buildBat = Join-Path $env:TEMP 'build_pgvector.bat'

    # Escrever script de build usando StreamWriter (sem problemas de encoding)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('@echo off')
    [void]$sb.AppendLine('call "' + $buildPath + '"')
    [void]$sb.AppendLine('if errorlevel 1 echo [WARN] vcvars retornou erro, tentando continuar...')
    [void]$sb.AppendLine('cd /d "' + $pgvSrcDir + '"')
    [void]$sb.AppendLine('set "PGROOT=' + $PgRoot + '"')
    [void]$sb.AppendLine('nmake /F Makefile.win 2>&1')
    [void]$sb.AppendLine('echo BUILD_DONE=%ERRORLEVEL%')
    [System.IO.File]::WriteAllText($buildBat, $sb.ToString(), [System.Text.ASCIIEncoding]::new())

    $buildOut = & cmd.exe /c $buildBat 2>&1
    foreach ($l in $buildOut) { Log "  build>> $l" }
    $buildExit = ($buildOut | Where-Object { $_ -match 'BUILD_DONE=' } | Select-Object -Last 1) -replace '.*BUILD_DONE=',''
    Log "[4] Build exit: $buildExit"

    $dllItem = Get-ChildItem $pgvSrcDir -Filter '*.dll' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $dllItem) {
        Die "DLL nao gerada. Build falhou. Ver log: $log"
    }
    Log "[4] DLL gerada: $($dllItem.Name)"

    # ── Etapa 5: instalar binarios no PostgreSQL ─────────────────────────────
    Log "[5] Instalando binarios em $PgRoot..."
    $installBat = Join-Path $env:TEMP 'install_pgvector.bat'
    $si = New-Object System.Text.StringBuilder
    [void]$si.AppendLine('@echo off')
    [void]$si.AppendLine('call "' + $buildPath + '"')
    [void]$si.AppendLine('cd /d "' + $pgvSrcDir + '"')
    [void]$si.AppendLine('set "PGROOT=' + $PgRoot + '"')
    [void]$si.AppendLine('nmake /F Makefile.win install 2>&1')
    [void]$si.AppendLine('echo INSTALL_DONE=%ERRORLEVEL%')
    [System.IO.File]::WriteAllText($installBat, $si.ToString(), [System.Text.ASCIIEncoding]::new())

    $installOut = & cmd.exe /c $installBat 2>&1
    foreach ($l in $installOut) { Log "  install>> $l" }

    if (-not (Test-Path $ctrlFile)) {
        Log "[5] nmake install nao copiou. Tentando copia manual..."
        $pgShare = "$PgRoot\share\extension"
        $pgLib   = "$PgRoot\lib"
        Get-ChildItem $pgvSrcDir -Filter '*.control' | ForEach-Object {
            Copy-Item $_.FullName $pgShare -Force
            Log "  copiado>> $($_.Name)"
        }
        Get-ChildItem $pgvSrcDir -Filter '*.sql' | ForEach-Object {
            Copy-Item $_.FullName $pgShare -Force
        }
        Get-ChildItem $pgvSrcDir -Filter '*.dll' | ForEach-Object {
            Copy-Item $_.FullName $pgLib -Force
            Log "  copiado>> $($_.Name)"
        }
    }

    if (-not (Test-Path $ctrlFile)) {
        Die "vector.control nao encontrado em $PgRoot\share\extension"
    }
    Log "[5] Binarios instalados!"

    # Ativar extensao no banco
    Log "[5] Criando extensao no banco $DbName..."
    $extOut = (& $psql -U postgres -h 127.0.0.1 -d $DbName -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1)
    foreach ($l in $extOut) { Log "  psql>> $l" }

    $ec = RunPsql "SELECT count(*) FROM pg_extension WHERE extname='vector';"
    $ecVal = ($ec | Where-Object { $_ -match '^\s*\d' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)
    if ($ecVal -ne '1') { Die "Extensao vector nao foi ativada no banco." }
    Log "[5] Extensao vector ativa!"
}

# ── Etapa 6: upgrade coluna TEXT -> vector(384) ──────────────────────────────
Log "[6] Verificando tipo da coluna vetor..."
$colRows = RunPsql "SELECT data_type FROM information_schema.columns WHERE table_name='tcpo_embeddings' AND column_name='vetor';"
$colType = ($colRows | Where-Object { $_ -match '\S' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)
Log "[6] Tipo atual: $colType"

if ($colType -eq 'text') {
    Log "[6] Upgradando TEXT -> vector(384)..."
    $upgSql = @'
DO $upg$
BEGIN
    DROP INDEX IF EXISTS ix_tcpo_embeddings_hnsw;
    ALTER TABLE tcpo_embeddings DROP COLUMN IF EXISTS vetor;
    EXECUTE 'ALTER TABLE tcpo_embeddings ADD COLUMN vetor vector(384)';
    EXECUTE 'CREATE INDEX ix_tcpo_embeddings_hnsw ON tcpo_embeddings USING hnsw (vetor vector_cosine_ops) WITH (m = 16, ef_construction = 64)';
    RAISE NOTICE 'vetor: TEXT -> vector(384) concluido';
END $upg$;
'@
    $upgOut = (& $psql -U postgres -h 127.0.0.1 -d $DbName -c $upgSql 2>&1)
    foreach ($l in $upgOut) { Log "  upgrade>> $l" }
    Log "[6] Upgrade concluido."
} elseif ($colType -match 'USER-DEFINED') {
    Log "[6] Coluna vetor ja e tipo vector. OK."
} else {
    Log "[6] AVISO: tipo inesperado '$colType'"
}

# ── Resumo ────────────────────────────────────────────────────────────────────
$udtRows  = RunPsql "SELECT udt_name FROM information_schema.columns WHERE table_name='tcpo_embeddings' AND column_name='vetor';"
$finalUdt = ($udtRows | Where-Object { $_ -match '\S' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)

Log ""
Log "============================================="
Log " pgvector configurado com sucesso!"
Log " Extensao vector: ativa em '$DbName'"
Log " Coluna vetor (udt_name): $finalUdt"
Log " Log: $log"
Log "============================================="
