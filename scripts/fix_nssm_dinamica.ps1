# Fix NSSM service to use venv Python and restart the service
$service = 'dinamica-backend'
$venvPython = 'C:\Dinamica-Budget\app\venv\Scripts\python.exe'
$appDir = 'C:\Dinamica-Budget\app'
$appParams = '-m uvicorn backend.main:app --host 127.0.0.1 --port 8000'

Write-Output "Using venv python: $venvPython"
$nssmCmd = (Get-Command nssm -ErrorAction SilentlyContinue).Source
if (-not $nssmCmd) {
    Write-Error "nssm.exe not found in PATH. Please install nssm or run this script on the host with nssm available."
    exit 1
}

try {
    & $nssmCmd set $service Application $venvPython
    & $nssmCmd set $service AppDirectory $appDir
    & $nssmCmd set $service AppParameters $appParams
    Write-Output "NSSM service $service updated to use venv python."
    & $nssmCmd restart $service
    Write-Output "Service $service restart command issued."
} catch {
    $msg = $_.Exception.Message -as [string]
    Write-Error ("Failed to update or restart {0}: {1}" -f $service, $msg)
    exit 1
}

Write-Output "Done. Check nssm stderr log (nssm_stderr.log) and service status with: sc query $service"