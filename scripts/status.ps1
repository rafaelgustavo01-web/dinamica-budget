$ESC   = [char]27
$RESET = "$ESC[0m"
$BOLD  = "$ESC[1m"
$GREEN = "$ESC[32m"
$RED   = "$ESC[31m"
$YELL  = "$ESC[33m"
$CYAN  = "$ESC[36m"
$DIM   = "$ESC[2m"

function OK   { param($t) Write-Host "  ${GREEN}[OK]  ${RESET} $t" }
function FAIL { param($t) Write-Host "  ${RED}[FAIL]${RESET} $t" }
function WARN { param($t) Write-Host "  ${YELL}[WARN]${RESET} $t" }

function Section { param($title)
    Write-Host ""
    Write-Host "${BOLD}${CYAN}=== $title ===${RESET}"
    Write-Host "${DIM}$('-'*60)${RESET}"
}

Clear-Host
Write-Host ""
Write-Host "${BOLD}${CYAN}+----------------------------------------------------------+"
Write-Host "|    DINAMICA BUDGET - STATUS DO SISTEMA                   |"
Write-Host "|    $(Get-Date -Format 'dd/MM/yyyy  HH:mm:ss')                                  |"
Write-Host "+----------------------------------------------------------+${RESET}"

Section "1. SERVICOS WINDOWS"
$pgSvc = Get-Service 'postgresql-x64-16' -ErrorAction SilentlyContinue
if ($pgSvc) {
    if ($pgSvc.Status -eq 'Running') { OK "PostgreSQL 16            Status: $($pgSvc.Status)" }
    else { FAIL "PostgreSQL 16            Status: $($pgSvc.Status)" }
} else { WARN "postgresql-x64-16 nao encontrado" }

$apiSvc = Get-Service 'DinamicaBudgetAPI' -ErrorAction SilentlyContinue
if ($apiSvc) {
    if ($apiSvc.Status -eq 'Running') { OK "DinamicaBudgetAPI (NSSM) Status: $($apiSvc.Status)" }
    else { FAIL "DinamicaBudgetAPI (NSSM) Status: $($apiSvc.Status)" }
} else { WARN "DinamicaBudgetAPI nao encontrado" }

$iisSvc = Get-Service 'W3SVC' -ErrorAction SilentlyContinue
if ($iisSvc) {
    if ($iisSvc.Status -eq 'Running') { OK "IIS (W3SVC)              Status: $($iisSvc.Status)" }
    else { FAIL "IIS (W3SVC)              Status: $($iisSvc.Status)" }
} else { WARN "IIS (W3SVC) nao encontrado" }

Section "2. PORTAS EM ESCUTA"
foreach ($p in @(80, 443, 8000, 5432)) {
    $conn = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $pname = if ($proc) { $proc.ProcessName } else { "PID $($conn.OwningProcess)" }
        OK ("Porta $p".PadRight(12) + " LISTEN  ($pname)")
    } else {
        FAIL ("Porta $p".PadRight(12) + " nao esta em LISTEN")
    }
}

Section "3. API HEALTH"
try {
    $r = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 5 -ErrorAction Stop
    OK "status             = $($r.status)"
    if ($r.database_connected) { OK "database_connected = True" } else { FAIL "database_connected = False" }
    if ($r.embedder_ready)     { OK "embedder_ready     = True" } else { WARN "embedder_ready     = False" }
} catch {
    FAIL "http://127.0.0.1:8000/health - $_"
}
try {
    $d = Invoke-WebRequest 'http://127.0.0.1:8000/docs' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($d.StatusCode -eq 200) { OK "Swagger UI /docs   = HTTP $($d.StatusCode)" }
    else { WARN "Swagger /docs = HTTP $($d.StatusCode)" }
} catch { WARN "/docs indisponivel" }

Section "4. POSTGRESQL"
$env:PGPASSWORD = 'PostgresSetup123!'
$psql = 'C:\Program Files\PostgreSQL\16\bin\psql.exe'
if (-not (Test-Path $psql)) {
    FAIL "psql.exe nao encontrado"
} else {
    $ver = (& $psql -U postgres -h 127.0.0.1 -d postgres -t -c 'SELECT version();' 2>&1 | Where-Object { $_ -match 'PostgreSQL' } | Select-Object -First 1)
    if ($ver) { OK $ver.Trim() } else { WARN "Nao obteve versao" }

    $dbExists = (& $psql -U postgres -h 127.0.0.1 -d postgres -t -c "SELECT count(*) FROM pg_database WHERE datname='dinamica_budget';" 2>&1 | Where-Object { $_ -match '^\s*\d' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)
    if ($dbExists -eq '1') { OK "Banco dinamica_budget existe" } else { FAIL "Banco dinamica_budget NAO ENCONTRADO" }

    $exts = (& $psql -U postgres -h 127.0.0.1 -d dinamica_budget -t -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector','pg_trgm') ORDER BY extname;" 2>&1)
    foreach ($line in ($exts | Where-Object { $_ -match '\S' })) {
        $parts = ($line.Trim() -split '\|') | ForEach-Object { $_.Trim() }
        OK ("Extensao " + $parts[0].PadRight(15) + " v" + $parts[1])
    }
    if (-not ($exts | Where-Object { $_ -match 'vector' }))  { FAIL "Extensao vector NAO instalada" }
    if (-not ($exts | Where-Object { $_ -match 'pg_trgm' })) { FAIL "Extensao pg_trgm NAO instalada" }
}

Section "5. ALEMBIC MIGRATIONS"
if (Test-Path $psql) {
    $migs = (& $psql -U postgres -h 127.0.0.1 -d dinamica_budget -t -c "SELECT version_num FROM alembic_version ORDER BY version_num;" 2>&1 | Where-Object { $_ -match '\S' } | ForEach-Object { $_.Trim() })
    if ($migs) { foreach ($m in $migs) { OK "Versao: $m" } }
    else { FAIL "Nenhuma migration (alembic_version vazia?)" }
    $tc = (& $psql -U postgres -h 127.0.0.1 -d dinamica_budget -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>&1 | Where-Object { $_ -match '^\s*\d' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)
    OK "Tabelas no schema public: $tc"
}

Section "6. COLUNA VETOR"
if (Test-Path $psql) {
    $udt = (& $psql -U postgres -h 127.0.0.1 -d dinamica_budget -t -c "SELECT udt_name FROM information_schema.columns WHERE table_name='tcpo_embeddings' AND column_name='vetor';" 2>&1 | Where-Object { $_ -match '\S' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)
    if ($udt -eq 'vector')     { OK "tcpo_embeddings.vetor = vector(384)" }
    elseif ($udt -eq 'text')   { FAIL "tcpo_embeddings.vetor ainda e TEXT" }
    else                       { WARN "tcpo_embeddings.vetor = $udt" }
    $idx = (& $psql -U postgres -h 127.0.0.1 -d dinamica_budget -t -c "SELECT indexname FROM pg_indexes WHERE tablename='tcpo_embeddings' AND indexname LIKE '%hnsw%';" 2>&1 | Where-Object { $_ -match '\S' } | ForEach-Object { $_.Trim() } | Select-Object -First 1)
    if ($idx) { OK "Indice HNSW: $idx" } else { WARN "Indice HNSW nao encontrado" }
}

Section "7. IIS SITES"
try {
    Import-Module WebAdministration -ErrorAction Stop | Out-Null
    $sites = Get-Website -ErrorAction SilentlyContinue
    if ($sites) {
        foreach ($s in $sites) {
            $binding = ($s.Bindings.Collection | Select-Object -First 1).bindingInformation
            if ($s.State -eq 'Started') { OK ($s.Name.PadRight(25) + " State: $($s.State)  Binding: $binding") }
            else { WARN ($s.Name.PadRight(25) + " State: $($s.State)  Binding: $binding") }
        }
    } else { WARN "Nenhum site IIS encontrado" }
} catch { WARN "WebAdministration indisponivel" }

Section "8. PROCESSOS PYTHON"
$pys = Get-Process python, uvicorn -ErrorAction SilentlyContinue
if ($pys) {
    foreach ($p in $pys) {
        $mem = [math]::Round($p.WorkingSet64 / 1MB, 1)
        OK ($p.ProcessName.PadRight(12) + "  PID $($p.Id)   RAM $mem MB")
    }
} else { WARN "Nenhum processo Python/uvicorn" }

Section "9. DISCO E MEMORIA"
$disk = Get-PSDrive C | Select-Object Used, Free
$freeGB = [math]::Round($disk.Free / 1GB, 1)
$usedGB = [math]::Round($disk.Used / 1GB, 1)
if ($freeGB -gt 10) { OK "Disco C:  livre $freeGB GB / usado $usedGB GB" }
else { WARN "Disco C:  ESPACO BAIXO - livre $freeGB GB" }

$ram = Get-CimInstance Win32_OperatingSystem
$freeMB  = [math]::Round($ram.FreePhysicalMemory / 1024)
$totalMB = [math]::Round($ram.TotalVisibleMemorySize / 1024)
if ($freeMB -gt 512) { OK "RAM: $freeMB MB livre / $totalMB MB total" }
else { WARN "RAM: MEMORIA BAIXA - $freeMB MB livre" }

Section "10. DIRETORIOS"
@(
    @{ Path = 'C:\DinamicaBudget';          Label = 'Deploy dir' },
    @{ Path = 'C:\DinamicaBudget\venv';     Label = 'venv Python' },
    @{ Path = 'C:\DinamicaBudget\ml_models';Label = 'ML models' },
    @{ Path = 'C:\inetpub\DinamicaBudget';  Label = 'IIS webroot' }
) | ForEach-Object {
    if (Test-Path $_.Path) { OK ($_.Label.PadRight(14) + " " + $_.Path) }
    else { FAIL ($_.Label.PadRight(14) + " " + $_.Path + " NAO ENCONTRADO") }
}

Section "11. LOG DA API (ultimas 8 linhas)"
$apiLog = 'C:\DinamicaBudget\logs\uvicorn.log'
if (Test-Path $apiLog) {
    Get-Content $apiLog -Tail 8 | ForEach-Object { Write-Host "  ${DIM}$_${RESET}" }
} else { WARN "Log nao encontrado: $apiLog" }

Write-Host ""
Write-Host "${DIM}  Reexecutar: .\scripts\status.ps1${RESET}"
Write-Host ""