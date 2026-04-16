#Requires -RunAsAdministrator
param(
    [string]$AdminEmail = "",
    [string]$AdminPassword = "",
    [string]$AdminName = "",
    [string]$DbPassword = ""
)

$ErrorActionPreference = "Continue"

$AppDir = "C:\DinamicaBudget"
$EnvFile = Join-Path $AppDir ".env"
$LogDir = "C:\Dinamica-Budget\logs"
$LogFile = Join-Path $LogDir "fix-auth-login-admin.log"
$ServiceName = "DinamicaBudgetAPI"
$HostName = "dinamica-budget.local"
$ApiPort = 8000
$NssmPath = "C:\Windows\System32\nssm.exe"

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$lines = @()
function Add-Log([string]$Message) {
    $script:lines += $Message
}

function Save-And-Exit([int]$Code) {
    $script:lines += "END: $(Get-Date -Format s)"
    $script:lines | Set-Content -Path $LogFile -Encoding UTF8
    exit $Code
}

function Is-PlaceholderValue([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return $true }
    $v = $Value.Trim().ToLowerInvariant()
    if ($v -in @(
            "change_me_use_secrets_token_hex_32",
            "change_me",
            "changeme",
            "secret",
            "placeholder",
            "use_email_admin",
            "use_password_admin",
            "use_name_admin",
            "your_password",
            "your_email"
        )) {
        return $true
    }
    if ($v.StartsWith("use_")) { return $true }
    if ($v.Contains("placeholder")) { return $true }
    return $false
}

function Get-EnvMap([string]$Path) {
    $map = @{}
    foreach ($raw in Get-Content -Path $Path -Encoding UTF8) {
        $line = $raw.Trim()
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line.StartsWith("#")) { continue }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }
        $k = $line.Substring(0, $idx).Trim()
        $v = $line.Substring($idx + 1).Trim()
        $map[$k] = $v
    }
    return $map
}

function Set-EnvKey([string]$Path, [string]$Key, [string]$Value) {
    $content = Get-Content -Path $Path -Encoding UTF8
    $pattern = "^" + [regex]::Escape($Key) + "="
    $updated = $false
    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match $pattern) {
            $content[$i] = "$Key=$Value"
            $updated = $true
            break
        }
    }
    if (-not $updated) {
        $content += "$Key=$Value"
    }
    Set-Content -Path $Path -Value $content -Encoding UTF8
}

Add-Log "START: $(Get-Date -Format s)"
Add-Log "Checking auth/login stack"

if (!(Test-Path $EnvFile)) {
    Add-Log "FAIL: .env not found at $EnvFile"
    Save-And-Exit 1
}

$envMap = Get-EnvMap -Path $EnvFile

$secret = ""
if ($envMap.ContainsKey("SECRET_KEY")) { $secret = $envMap["SECRET_KEY"] }

if ((Is-PlaceholderValue $secret) -or $secret.Trim().Length -lt 32) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $newSecret = -join ($bytes | ForEach-Object { $_.ToString("x2") })
    Set-EnvKey -Path $EnvFile -Key "SECRET_KEY" -Value $newSecret
    Add-Log "FIX: SECRET_KEY regenerated"
} else {
    Add-Log "OK: SECRET_KEY looks valid"
}

if (-not [string]::IsNullOrWhiteSpace($AdminEmail)) {
    Set-EnvKey -Path $EnvFile -Key "ROOT_USER_EMAIL" -Value $AdminEmail
    Add-Log "FIX: ROOT_USER_EMAIL updated from script parameter"
}
if (-not [string]::IsNullOrWhiteSpace($AdminPassword)) {
    Set-EnvKey -Path $EnvFile -Key "ROOT_USER_PASSWORD" -Value $AdminPassword
    Add-Log "FIX: ROOT_USER_PASSWORD updated from script parameter"
}
if (-not [string]::IsNullOrWhiteSpace($AdminName)) {
    Set-EnvKey -Path $EnvFile -Key "ROOT_USER_NAME" -Value $AdminName
    Add-Log "FIX: ROOT_USER_NAME updated from script parameter"
}
if (-not [string]::IsNullOrWhiteSpace($DbPassword)) {
    $envMapForDb = Get-EnvMap -Path $EnvFile
    if ($envMapForDb.ContainsKey("DATABASE_URL")) {
        $dbUrlCurrent = $envMapForDb["DATABASE_URL"]
        if ($dbUrlCurrent -match '^(postgresql(?:\+\w+)?://[^:]+:)(.+)(@[^/]+/.+)$') {
            $dbPassEscaped = [Uri]::EscapeDataString($DbPassword)
            $dbPassEscaped = $dbPassEscaped.Replace('!', '%21')
            $dbUrlNew = $Matches[1] + $dbPassEscaped + $Matches[3]
            Set-EnvKey -Path $EnvFile -Key "DATABASE_URL" -Value $dbUrlNew
            Add-Log "FIX: DATABASE_URL password updated from script parameter"
        }
    }
}

$envMapAfterInput = Get-EnvMap -Path $EnvFile
$rootEmailNow = ""
$rootPassNow = ""
$rootNameNow = ""
if ($envMapAfterInput.ContainsKey("ROOT_USER_EMAIL")) { $rootEmailNow = $envMapAfterInput["ROOT_USER_EMAIL"] }
if ($envMapAfterInput.ContainsKey("ROOT_USER_PASSWORD")) { $rootPassNow = $envMapAfterInput["ROOT_USER_PASSWORD"] }
if ($envMapAfterInput.ContainsKey("ROOT_USER_NAME")) { $rootNameNow = $envMapAfterInput["ROOT_USER_NAME"] }

if ((Is-PlaceholderValue $rootEmailNow) -or (Is-PlaceholderValue $rootPassNow) -or $rootPassNow.Trim().Length -lt 8) {
    $emergencyEmail = "admin@dinamica-budget.local"
    $randA = [Guid]::NewGuid().ToString("N").Substring(0, 12)
    $randB = [Guid]::NewGuid().ToString("N").Substring(0, 8)
    $emergencyPass = "Db!" + $randA + $randB
    $emergencyName = "Administrador Dinamica"

    Set-EnvKey -Path $EnvFile -Key "ROOT_USER_EMAIL" -Value $emergencyEmail
    Set-EnvKey -Path $EnvFile -Key "ROOT_USER_PASSWORD" -Value $emergencyPass
    if ([string]::IsNullOrWhiteSpace($rootNameNow) -or (Is-PlaceholderValue $rootNameNow)) {
        Set-EnvKey -Path $EnvFile -Key "ROOT_USER_NAME" -Value $emergencyName
    }

    Add-Log "FIX: ROOT_USER credentials were placeholders and were auto-generated"
    Add-Log "INFO: EMERGENCY_ADMIN_EMAIL=$emergencyEmail"
}

$pythonExe = Join-Path $AppDir "venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) {
    Add-Log "FAIL: python not found in venv ($pythonExe)"
    Save-And-Exit 1
}

$tmpPy = Join-Path $env:TEMP "dinamica_auth_fix.py"
$tmpOut = Join-Path $env:TEMP "dinamica_auth_fix.out"

$pyCode = @'
import os
import uuid
import asyncio
from pathlib import Path

import asyncpg

APP_DIR = Path(r"C:\DinamicaBudget")
ENV_FILE = APP_DIR / ".env"


def parse_env(path: Path) -> dict:
    data = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def is_placeholder(value: str) -> bool:
    if value is None:
        return True
    v = value.strip().lower()
    if not v:
        return True
    if v in {
        "change_me_use_secrets_token_hex_32",
        "change_me",
        "changeme",
        "secret",
        "placeholder",
        "use_email_admin",
        "use_password_admin",
        "use_name_admin",
        "your_password",
        "your_email",
    }:
        return True
    return v.startswith("use_") or "placeholder" in v


def main() -> int:
    env = parse_env(ENV_FILE)
    db_url = env.get("DATABASE_URL", "").strip()
    if not db_url:
        print("RESULT=FAIL")
        print("REASON=DATABASE_URL_MISSING")
        return 2

    root_email = env.get("ROOT_USER_EMAIL", "").strip().lower()
    root_password = env.get("ROOT_USER_PASSWORD", "").strip()
    root_name = env.get("ROOT_USER_NAME", "").strip() or "Administrador"

    can_seed = (
        not is_placeholder(root_email)
        and not is_placeholder(root_password)
        and len(root_password) >= 8
        and "@" in root_email
    )

    # Import from app package installed in this project
    import sys

    sys.path.insert(0, str(APP_DIR))
    from app.core.security import hash_password

    async def run() -> int:
        conn = await asyncpg.connect(db_url.replace("+asyncpg", ""))
        try:
            rows = await conn.fetch("SELECT id, email, is_admin, is_active FROM usuarios")
            admin_active = sum(1 for r in rows if bool(r[2]) and bool(r[3]))
            print(f"USERS_TOTAL={len(rows)}")
            print(f"ADMIN_ACTIVE={admin_active}")

            if not can_seed:
                print("RESULT=FAIL")
                print("REASON=ROOT_ENV_INVALID")
                return 3

            existing = await conn.fetchrow(
                "SELECT id FROM usuarios WHERE lower(email)=lower($1) LIMIT 1",
                root_email,
            )
            hashed = hash_password(root_password)

            if existing:
                await conn.execute(
                    """
                    UPDATE usuarios
                       SET nome=$1,
                           hashed_password=$2,
                           is_admin=TRUE,
                           is_active=TRUE,
                           updated_at=now()
                     WHERE id=$3
                    """,
                    root_name,
                    hashed,
                    existing[0],
                )
                print("ADMIN_FIX=UPDATED_CONFIGURED_ROOT")
            else:
                await conn.execute(
                    """
                    INSERT INTO usuarios (id, nome, email, hashed_password, is_active, is_admin)
                    VALUES (gen_random_uuid(), $1, lower($2), $3, TRUE, TRUE)
                    """,
                    root_name,
                    root_email,
                    hashed,
                )
                print("ADMIN_FIX=CREATED_CONFIGURED_ROOT")

            if root_email != "admin@dinamica-budget.local":
                deleted_res = await conn.execute(
                    "DELETE FROM usuarios WHERE lower(email)=lower($1)",
                    "admin@dinamica-budget.local",
                )
                print(f"EMERGENCY_ADMIN_REMOVED={deleted_res}")

            admin_active_after = await conn.fetchval(
                "SELECT count(*) FROM usuarios WHERE is_admin=TRUE AND is_active=TRUE"
            )
            print(f"ADMIN_ACTIVE_AFTER={admin_active_after}")
        finally:
            await conn.close()

        print("RESULT=OK")
        return 0

    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
'@

Set-Content -Path $tmpPy -Encoding UTF8 -Value $pyCode
& $pythonExe $tmpPy *> $tmpOut
$pyExit = $LASTEXITCODE

if (Test-Path $tmpOut) {
    foreach ($line in (Get-Content -Path $tmpOut -Encoding UTF8)) {
        Add-Log ("PY: " + $line)
    }
}

Remove-Item -Path $tmpPy -Force -ErrorAction SilentlyContinue
Remove-Item -Path $tmpOut -Force -ErrorAction SilentlyContinue

if ($pyExit -ne 0) {
    Add-Log "FAIL: database/admin validation failed (exit=$pyExit)"
    Add-Log "ACTION: set ROOT_USER_EMAIL/ROOT_USER_PASSWORD in .env and rerun"
    Save-And-Exit 1
}

if (Test-Path $NssmPath) {
    $serviceExists = $false
    sc.exe query $ServiceName > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $serviceExists = $true
    }

    if (-not $serviceExists) {
        & $NssmPath install $ServiceName $pythonExe "-m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort --workers 1" | Out-Null
        Add-Log "FIX: service installed via NSSM"
    }

    & $NssmPath set $ServiceName Application $pythonExe | Out-Null
    & $NssmPath set $ServiceName AppParameters "-m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort --workers 1" | Out-Null
    & $NssmPath set $ServiceName AppDirectory $AppDir | Out-Null
    & $NssmPath set $ServiceName Start SERVICE_AUTO_START | Out-Null
    & $NssmPath set $ServiceName AppStdout "C:\Dinamica-Budget\logs\api-stdout.log" | Out-Null
    & $NssmPath set $ServiceName AppStderr "C:\Dinamica-Budget\logs\api-stderr.log" | Out-Null
    & $NssmPath set $ServiceName AppRotateFiles 1 | Out-Null
    & $NssmPath set $ServiceName AppRotateBytes 10485760 | Out-Null
    & $NssmPath set $ServiceName AppEnvironmentExtra "SENTENCE_TRANSFORMERS_HOME=$AppDir\ml_models" | Out-Null

    & $NssmPath restart $ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        & $NssmPath start $ServiceName | Out-Null
    }
    Add-Log "OK: service configured and restart/start requested via NSSM"
} else {
    sc.exe start $ServiceName | Out-Null
    Add-Log "WARN: NSSM not found, attempted service start via sc.exe"
}

$apiOk = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/health" -TimeoutSec 4
        if ($h.status -eq "ok" -or $h.status -eq "degraded") {
            $apiOk = $true
            break
        }
    } catch {
    }
    Start-Sleep -Seconds 2
}

if (-not $apiOk) {
    Add-Log "FAIL: API health still unavailable on 127.0.0.1:$ApiPort"
    if (Test-Path "C:\Dinamica-Budget\logs\api-stderr.log") {
        Add-Log "TAIL api-stderr.log:"
        foreach ($l in (Get-Content "C:\Dinamica-Budget\logs\api-stderr.log" -Tail 40)) {
            Add-Log ("ERR: " + $l)
        }
    }
    if (Test-Path "C:\Dinamica-Budget\logs\api-stdout.log") {
        Add-Log "TAIL api-stdout.log:"
        foreach ($l in (Get-Content "C:\Dinamica-Budget\logs\api-stdout.log" -Tail 40)) {
            Add-Log ("OUT: " + $l)
        }
    }
    Save-And-Exit 1
}
Add-Log "OK: API health reachable on localhost"

$loginCode = 0
try {
    $payload = '{"email":"dummy@example.com","password":"dummy12345"}'
    $resp = Invoke-WebRequest -Uri "http://$HostName/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $payload -UseBasicParsing -TimeoutSec 8
    $loginCode = [int]$resp.StatusCode
} catch {
    if ($_.Exception.Response) {
        $loginCode = [int]$_.Exception.Response.StatusCode
    }
}

Add-Log "CHECK: login endpoint returned HTTP $loginCode"
if ($loginCode -in @(401, 422, 429, 400)) {
    Add-Log "OK: login endpoint reachable via IIS/proxy"
} elseif ($loginCode -eq 0 -or $loginCode -eq 502 -or $loginCode -eq 404) {
    Add-Log "FAIL: login endpoint unhealthy (HTTP $loginCode)"
    Save-And-Exit 1
} else {
    Add-Log "WARN: unexpected login status ($loginCode), but request reached API"
}

$spaOk = $false
try {
    $spa = Invoke-WebRequest -Uri "http://$HostName/login" -UseBasicParsing -TimeoutSec 8
    if ($spa.StatusCode -eq 200) {
        $spaOk = $true
    }
} catch {
}

if ($spaOk) {
    Add-Log "OK: SPA deep-link /login reachable"
} else {
    Add-Log "WARN: SPA deep-link /login failed"
}

Add-Log "DONE"
Save-And-Exit 0
