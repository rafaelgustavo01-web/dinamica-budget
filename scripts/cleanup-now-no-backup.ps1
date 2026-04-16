#Requires -RunAsAdministrator
$ErrorActionPreference = 'Continue'

$AppDir = 'C:\DinamicaBudget'
$SiteName = 'DinamicaBudget'
$PoolName = 'DinamicaBudgetPool'
$ServiceName = 'DinamicaBudgetAPI'
$HostsFile = "$env:windir\System32\drivers\etc\hosts"
$AppCmd = "$env:windir\System32\inetsrv\appcmd.exe"
$Log = 'C:\Dinamica-Budget\logs\cleanup-now-no-backup.log'

if (!(Test-Path 'C:\Dinamica-Budget\logs')) { New-Item -ItemType Directory -Path 'C:\Dinamica-Budget\logs' -Force | Out-Null }
$lines = @()
function L([string]$m){ $script:lines += $m; Write-Output $m }

L "=== CLEANUP NOW (SEM BACKUP) ==="
L (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# 1) Stop/remove API service
L '[1] Service cleanup'
try {
    sc.exe query $ServiceName | Out-Null
    if ($LASTEXITCODE -eq 0) {
        if (Test-Path 'C:\Windows\System32\nssm.exe') {
            & 'C:\Windows\System32\nssm.exe' stop $ServiceName | Out-Null
            Start-Sleep -Seconds 2
            & 'C:\Windows\System32\nssm.exe' remove $ServiceName confirm | Out-Null
        }
        sc.exe stop $ServiceName | Out-Null
        sc.exe delete $ServiceName | Out-Null
        L "OK: service removed ($ServiceName)"
    } else {
        L 'SKIP: service not found'
    }
} catch {
    L "WARN: service cleanup failed: $($_.Exception.Message)"
}

# 2) Stop related python/node processes under deploy dir
L '[2] Process cleanup'
try {
    $procs = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -match 'python|node|uvicorn') -and ($_.ExecutablePath -like 'C:\DinamicaBudget*')
    }
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        L "OK: process stopped PID=$($p.ProcessId) Name=$($p.Name)"
    }
    if (-not $procs) { L 'SKIP: no related processes found' }
} catch {
    L "WARN: process cleanup failed: $($_.Exception.Message)"
}

# 3) IIS site/pool cleanup
L '[3] IIS cleanup'
if (Test-Path $AppCmd) {
    try { & $AppCmd stop site $SiteName | Out-Null } catch {}
    try { & $AppCmd delete site $SiteName | Out-Null; L "OK: site removed ($SiteName)" } catch { L "SKIP/WARN: site remove issue" }
    try { & $AppCmd stop apppool $PoolName | Out-Null } catch {}
    try { & $AppCmd delete apppool $PoolName | Out-Null; L "OK: app pool removed ($PoolName)" } catch { L "SKIP/WARN: pool remove issue" }
} else {
    L 'SKIP: IIS appcmd not found'
}

# 4) Firewall cleanup
L '[4] Firewall cleanup'
try {
    netsh advfirewall firewall delete rule name='Dinamica Budget HTTP' | Out-Null
    netsh advfirewall firewall delete rule name='Dinamica Budget HTTPS' | Out-Null
    L 'OK: firewall rules removed'
} catch {
    L "WARN: firewall cleanup failed: $($_.Exception.Message)"
}

# 5) Hosts cleanup
L '[5] Hosts cleanup'
try {
    if (Test-Path $HostsFile) {
        $h = Get-Content $HostsFile -Encoding ASCII -ErrorAction SilentlyContinue
        $h = $h | Where-Object { $_ -notmatch 'dinamica-budget\.local' -and $_ -notmatch '# Dinamica Budget' }
        $txt = ''
        if ($h -and $h.Count -gt 0) {
            $txt = [string]::Join("`r`n", $h) + "`r`n"
        }
        [System.IO.File]::WriteAllText($HostsFile, $txt, [System.Text.Encoding]::ASCII)
        ipconfig /flushdns | Out-Null
        L 'OK: hosts entries removed'
    }
} catch {
    L "WARN: hosts cleanup failed: $($_.Exception.Message)"
}

# 6) Drop DB without backup (if exists)
L '[6] Database cleanup (DROP sem backup)'
try {
    $envFile = Join-Path $AppDir '.env'
    if (!(Test-Path $envFile)) {
        L 'SKIP: .env not found; DB cleanup skipped'
    } else {
        $dbUrlLine = Get-Content $envFile -Encoding UTF8 | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
        if (-not $dbUrlLine) {
            L 'SKIP: DATABASE_URL missing in .env'
        } else {
            $dbUrl = ($dbUrlLine -split '=',2)[1]
            if ($dbUrl -match 'postgresql(?:\+\w+)?://([^:@]+):(.+)@([^:/]+):(\d+)/([^/?]+)') {
                $pgUser = $Matches[1]
                $pgPass = $Matches[2]
                $pgHost = $Matches[3]
                $pgPort = [int]$Matches[4]
                $dbName = $Matches[5]

                $psql = $null
                foreach ($v in 17,16,15,14) {
                    $c = "C:\Program Files\PostgreSQL\$v\bin\psql.exe"
                    if (Test-Path $c) { $psql = $c; break }
                }
                if (-not $psql) {
                    $cmd = Get-Command psql -ErrorAction SilentlyContinue
                    if ($cmd) { $psql = $cmd.Source }
                }

                if (-not $psql) {
                    L 'WARN: psql not found; DB drop skipped'
                } else {
                    $env:PGPASSWORD = $pgPass
                    $exists = & $psql -U $pgUser -h $pgHost -p $pgPort -tAc "SELECT 1 FROM pg_database WHERE datname='$dbName'" 2>&1
                    if ($LASTEXITCODE -eq 0 -and (($exists -join '') -match '1')) {
                        & $psql -U $pgUser -h $pgHost -p $pgPort -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$dbName' AND pid <> pg_backend_pid();" | Out-Null
                        & $psql -U $pgUser -h $pgHost -p $pgPort -d postgres -c "DROP DATABASE IF EXISTS $dbName;" | Out-Null
                        if ($LASTEXITCODE -eq 0) {
                            L "OK: database dropped ($dbName)"
                        } else {
                            L "WARN: failed to drop database ($dbName)"
                        }
                    } else {
                        L "SKIP: database does not exist ($dbName)"
                    }
                    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
                }
            } else {
                L 'WARN: DATABASE_URL parse failed'
            }
        }
    }
} catch {
    L "WARN: DB cleanup failed: $($_.Exception.Message)"
}

L '=== CLEANUP END ==='
$lines | Set-Content $Log -Encoding UTF8
Write-Output "LOG: $Log"
