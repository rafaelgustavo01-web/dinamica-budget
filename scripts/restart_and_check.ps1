# Restart dinamica-backend service and check health
Restart-Service -Name 'dinamica-backend' -Force
Get-Service -Name 'dinamica-backend' | Select-Object Status,DisplayName
try {
    $h = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 30
    $h | ConvertTo-Json -Depth 4
} catch {
    Write-Output ('HEALTH_ERROR: ' + $_.Exception.Message)
}
