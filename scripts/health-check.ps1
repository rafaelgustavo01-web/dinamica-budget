# scripts/health-check.ps1
param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432
)

Write-Host "=== Dinamica Budget — Health Check ===" -ForegroundColor Cyan

# 1. Testar API via Endpoint Health
Write-Host "`n[1/3] API Health..." -ForegroundColor Yellow
try {
    # Suprime erro de certificado se for HTTPS auto-assinado (comum on-premise)
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/health/" -Method Get -TimeoutSec 5
    
    if ($response.status -eq "healthy") {
        Write-Host "  API: OK (Versão: $($response.version))" -ForegroundColor Green
    } else {
        Write-Host "  API: DEGRADADA (Banco: $($response.database))" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  API: FALHA — Verifique se o serviço está rodando em $ApiUrl" -ForegroundColor Red
    Write-Host "  Erro: $($_.Exception.Message)" -ForegroundColor Gray
}

# 2. Testar PostgreSQL via TCP Port (mais simples que psql on-premise)
Write-Host "`n[2/3] PostgreSQL Connectivity..." -ForegroundColor Yellow
$connection = New-Object System.Net.Sockets.TcpClient
try {
    $connection.Connect($DbHost, $DbPort)
    if ($connection.Connected) {
        Write-Host "  PostgreSQL: OK (Porta $DbPort aberta)" -ForegroundColor Green
    }
} catch {
    Write-Host "  PostgreSQL: FALHA — Porta $DbPort inacessível em $DbHost" -ForegroundColor Red
} finally {
    $connection.Close()
}

# 3. Testar Espaço em Disco (Partição de Dados)
Write-Host "`n[3/3] Disk Space (C:)..." -ForegroundColor Yellow
try {
    $disk = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "C:" }
    $freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
    $totalGB = [math]::Round($disk.Size / 1GB, 2)
    $freePercent = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 1)

    if ($freePercent -gt 15) {
        Write-Host "  Disk: OK ($freeGB GB livres de $totalGB GB — $freePercent%)" -ForegroundColor Green
    } elseif ($freePercent -gt 5) {
        Write-Host "  Disk: ATENÇÃO ($freeGB GB livres — $freePercent%)" -ForegroundColor Yellow
    } else {
        Write-Host "  Disk: CRÍTICO ($freeGB GB livres — $freePercent%)" -ForegroundColor Red
    }
} catch {
    Write-Host "  Disk check failed: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host "`n=== Fim do Health Check ===" -ForegroundColor Cyan
