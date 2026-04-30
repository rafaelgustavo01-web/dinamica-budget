# load_db.ps1 - Load SQL file into PostgreSQL using credentials from .env
param(
    [string]$EnvFile = "..\.env",
    [string]$SqlFile = "..\..\der.sql"
)

function Get-EnvValue($file, $key) {
    $re = "^$key=(.*)$"
    Get-Content $file | ForEach-Object {
        if ($_ -match $re) { return $Matches[1].Trim(' "') }
    }
    return $null
}

$database_url = Get-EnvValue $EnvFile 'DATABASE_URL'
if (-not $database_url) { Write-Error "DATABASE_URL not found in $EnvFile"; exit 1 }
# parse postgresql+asyncpg://user:pass@host:port/dbname
$u = $database_url -replace '^postgresql\+asyncpg:\/\/', ''
$parts = $u -split '@'
$creds = $parts[0]
$hostpart = $parts[1]
$dbUser = $creds -split ':' | Select-Object -First 1
$dbPass = ($creds -split ':')[1]
$dbHost = $hostpart -split ':' | Select-Object -First 1
$dbPort = ($hostpart -split ':')[1] -split '/' | Select-Object -First 1
$dbName = ($hostpart -split '/')[-1]

# URL-decoding password if contains %xx
 $dbPass = [System.Uri]::UnescapeDataString($dbPass)

$psql = 'C:\Program Files\PostgreSQL\16\bin\psql.exe'
if (-not (Test-Path $psql)) {
    $psql = (Get-Command psql -ErrorAction SilentlyContinue).Source
}
if (-not $psql) { Write-Error "psql not found. Install PostgreSQL client or ensure psql in PATH"; exit 1 }

Write-Host ("Connecting to {0}:{1} db={2} as {3}" -f $dbHost,$dbPort,$dbName,$dbUser)
$env:PGPASSWORD = $dbPass
& "$psql" -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $SqlFile
if ($LASTEXITCODE -ne 0) { Write-Error "psql returned exit $LASTEXITCODE"; exit $LASTEXITCODE }
Write-Host "SQL import complete"
