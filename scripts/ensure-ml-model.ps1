param(
    [string]$PythonExe = "C:\DinamicaBudget\venv\Scripts\python.exe",
    [string]$ModelName = "all-MiniLM-L6-v2",
    [string]$ModelCacheDir = "C:\DinamicaBudget\ml_models",
    [int]$TimeoutSec = 900
)

$ErrorActionPreference = 'Stop'

function Test-ModelReady {
    param([string]$CacheDir)

    $root = Join-Path $CacheDir 'models--sentence-transformers--all-MiniLM-L6-v2'
    $snapshots = Join-Path $root 'snapshots'
    if (-not (Test-Path $snapshots)) { return $false }

    $mainCfg = Get-ChildItem -Path $snapshots -Recurse -File -Filter 'config.json' -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '\\snapshots\\[^\\]+\\config.json$' } |
        Select-Object -First 1

    $poolCfg = Get-ChildItem -Path $snapshots -Recurse -File -Filter 'config.json' -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match '\\snapshots\\[^\\]+\\1_Pooling\\config.json$' } |
        Select-Object -First 1

    return ($null -ne $mainCfg -and $null -ne $poolCfg)
}

if (-not (Test-Path $PythonExe)) {
    Write-Host "[FAIL] Python do venv nao encontrado: $PythonExe"
    exit 11
}

New-Item -ItemType Directory -Path $ModelCacheDir -Force | Out-Null

if (Test-ModelReady -CacheDir $ModelCacheDir) {
    Write-Host "[OK] Modelo all-MiniLM-L6-v2 ja presente e valido em $ModelCacheDir"
    exit 0
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $null = Invoke-WebRequest -Uri 'https://huggingface.co' -TimeoutSec 8 -UseBasicParsing
} catch {
    Write-Host "[WARN] Sem internet para baixar modelo ML."
    exit 10
}

$tmpScript = Join-Path $env:TEMP 'dinamica_ensure_ml_model.py'
$pyCode = @'
import sys
from sentence_transformers import SentenceTransformer

model_name = sys.argv[1]
cache_dir = sys.argv[2]
SentenceTransformer(model_name, cache_folder=cache_dir)
print("MODEL_OK")
'@
Set-Content -Path $tmpScript -Value $pyCode -Encoding UTF8

$proc = Start-Process -FilePath $PythonExe -ArgumentList @($tmpScript, $ModelName, $ModelCacheDir) -PassThru -WindowStyle Hidden
if (-not $proc.WaitForExit($TimeoutSec * 1000)) {
    try { $proc.Kill() } catch {}
    Write-Host "[WARN] Timeout no download do modelo ML (${TimeoutSec}s)."
    exit 124
}

if ($proc.ExitCode -ne 0) {
    Write-Host "[FAIL] Download do modelo retornou codigo $($proc.ExitCode)."
    exit 12
}

if (-not (Test-ModelReady -CacheDir $ModelCacheDir)) {
    Write-Host "[FAIL] Modelo baixado mas validacao final falhou (arquivos incompletos)."
    exit 13
}

Write-Host "[OK] Modelo all-MiniLM-L6-v2 pronto em $ModelCacheDir"
exit 0
