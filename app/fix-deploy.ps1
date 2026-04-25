#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Dinamica Budget — Fix Deploy (corrige IIS, hosts, CORS, firewall)
    Executar como Administrador: powershell -ExecutionPolicy Bypass -File fix-deploy.ps1
.DESCRIPTION
    Repara o deploy existente sem reinstalar. Corrige:
    - IIS webroot (copia frontend/dist)
    - IIS site + app pool + bindings
    - web.config (URL Rewrite + ARR proxy)
    - Hosts file (URL amigavel)
    - CORS (adiciona IP e hostname)
    - Firewall (porta 80/443)
    - Reinicia servico da API
#>

param(
    [string]$AppDir       = "C:\DinamicaBudget",
    [string]$IISRoot      = "C:\inetpub\DinamicaBudget",
    [string]$SiteName     = "DinamicaBudget",
    [string]$PoolName     = "DinamicaBudgetPool",
    [string]$ServiceName  = "DinamicaBudgetAPI",
    [int]$ApiPort         = 8000,
    [int]$HttpPort        = 80,
    [string]$Hostname     = "dinamica-budget.local"
)

$ErrorActionPreference = "Continue"
$appcmd = "$env:windir\System32\inetsrv\appcmd.exe"

# ── Helpers ─────────────────────────────────────────────────────────────────
function Write-Step($n, $msg) { Write-Host "`n  [$n] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)       { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg)     { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Fail($msg)     { Write-Host "    [FAIL] $msg" -ForegroundColor Red }
function Write-Info($msg)     { Write-Host "    [INFO] $msg" -ForegroundColor Gray }

Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   DINAMICA BUDGET — Fix Deploy" -ForegroundColor White
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Detect server IP
$serverIP = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -ne 'WellKnown' } |
    Select-Object -First 1).IPAddress
if (-not $serverIP) { $serverIP = "127.0.0.1" }
Write-Info "IP do servidor: $serverIP"
Write-Info "Hostname: $Hostname"

# ── ETAPA 1: Copiar frontend para IIS webroot ──────────────────────────────
Write-Step "1/8" "Copiar frontend para IIS webroot"
$distDir = "$AppDir\frontend\dist"
if (-not (Test-Path "$distDir\index.html")) {
    Write-Warn "Frontend nao encontrado em $distDir. Tentando build..."
    Push-Location "$AppDir\frontend"
    & npm install 2>&1 | Out-Null
    & npm run build 2>&1 | Out-Null
    Pop-Location
    if (-not (Test-Path "$distDir\index.html")) {
        Write-Fail "Build do frontend falhou. Verifique manualmente."
    }
}
if (Test-Path "$distDir\index.html") {
    if (-not (Test-Path $IISRoot)) { New-Item -ItemType Directory -Path $IISRoot -Force | Out-Null }
    robocopy $distDir $IISRoot /MIR /R:2 /W:2 /NFL /NDL /NP | Out-Null
    Write-Ok "Frontend copiado para $IISRoot"
} else {
    Write-Fail "Nao foi possivel copiar frontend"
}

# ── ETAPA 2: web.config (URL Rewrite + SPA Fallback) ───────────────────────
Write-Step "2/8" "Gerar web.config"
$webConfig = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <defaultDocument>
      <files>
        <clear />
        <add value="index.html" />
      </files>
    </defaultDocument>
    <staticContent>
      <remove fileExtension=".json" />
      <mimeMap fileExtension=".json" mimeType="application/json" />
      <remove fileExtension=".woff" />
      <mimeMap fileExtension=".woff" mimeType="font/woff" />
      <remove fileExtension=".woff2" />
      <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
      <remove fileExtension=".svg" />
      <mimeMap fileExtension=".svg" mimeType="image/svg+xml" />
    </staticContent>
    <rewrite>
      <rules>
        <rule name="API Reverse Proxy" stopProcessing="true">
          <match url="^(api/.*|health|docs|redoc|openapi.json)(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:${ApiPort}/{R:0}" />
        </rule>
        <rule name="SPA Fallback" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
    <httpCompression>
      <dynamicTypes>
        <add mimeType="application/json" enabled="true" />
      </dynamicTypes>
    </httpCompression>
  </system.webServer>
</configuration>
"@
$webConfig | Set-Content -Path "$IISRoot\web.config" -Encoding UTF8 -Force
Write-Ok "web.config criado com API Proxy + SPA Fallback"

# ── ETAPA 3: App Pool + Site IIS ───────────────────────────────────────────
Write-Step "3/8" "Configurar IIS (App Pool + Site)"

if (-not (Test-Path $appcmd)) {
    Write-Fail "IIS nao instalado. Instale: Install-WindowsFeature Web-Server -IncludeManagementTools"
} else {
    # Parar Default Web Site (libera porta 80)
    & $appcmd stop site "Default Web Site" 2>&1 | Out-Null
    Write-Info "Default Web Site parado"

    # App Pool
    $poolExists = & $appcmd list apppool $PoolName 2>&1
    if ($LASTEXITCODE -ne 0) {
        & $appcmd add apppool /name:$PoolName 2>&1 | Out-Null
        & $appcmd set apppool $PoolName /managedRuntimeVersion:"" 2>&1 | Out-Null
        Write-Ok "App pool '$PoolName' criado (No Managed Code)"
    } else {
        Write-Info "App pool '$PoolName' ja existe"
    }

    # Remover site antigo se existir (para recriar com bindings corretos)
    & $appcmd delete site $SiteName 2>&1 | Out-Null

    # Criar site com binding para todas as interfaces
    & $appcmd add site /name:$SiteName /bindings:"http/*:${HttpPort}:" /physicalPath:$IISRoot 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Site '$SiteName' criado na porta $HttpPort"
    } else {
        Write-Warn "Falha ao criar site. Porta $HttpPort pode estar em uso."
    }

    # Adicionar binding com hostname
    & $appcmd set site /site.name:$SiteName /+"bindings.[protocol='http',bindingInformation='*:${HttpPort}:${Hostname}']" 2>&1 | Out-Null
    Write-Ok "Binding adicionado: http://${Hostname}:${HttpPort}"

    # Adicionar binding com IP
    & $appcmd set site /site.name:$SiteName /+"bindings.[protocol='http',bindingInformation='${serverIP}:${HttpPort}:']" 2>&1 | Out-Null
    Write-Info "Binding IP: http://${serverIP}:${HttpPort}"

    # Associar pool e iniciar
    & $appcmd set app "$SiteName/" /applicationPool:$PoolName 2>&1 | Out-Null
    & $appcmd start site $SiteName 2>&1 | Out-Null
    Write-Ok "Site iniciado"
}

# ── ETAPA 4: Habilitar ARR Proxy ──────────────────────────────────────────
Write-Step "4/8" "Habilitar ARR (Application Request Routing)"
if (Test-Path "$env:windir\System32\inetsrv\requestRouter.dll") {
    & $appcmd set config -section:system.webServer/proxy /enabled:"True" /commit:apphost 2>&1 | Out-Null
    & $appcmd set config -section:system.webServer/proxy /preserveHostHeader:"True" /commit:apphost 2>&1 | Out-Null
    Write-Ok "ARR proxy habilitado com preserveHostHeader"
} else {
    Write-Warn "ARR nao instalado. Reverse proxy nao funcionara."
    Write-Info "Instale: WebPI > Application Request Routing 3.0"
}

# ── ETAPA 5: Hosts file ───────────────────────────────────────────────────
Write-Step "5/8" "Configurar hosts file (URL amigavel)"
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$hostsContent = Get-Content $hostsFile -ErrorAction SilentlyContinue
$entry127 = "127.0.0.1       $Hostname"
$entryIP  = "$serverIP       $Hostname"

# Remover entradas antigas do dinamica-budget
$newLines = $hostsContent | Where-Object { $_ -notmatch "dinamica-budget" }

# Adicionar novas entradas
$newLines += ""
$newLines += "# Dinamica Budget - Sistema de Orcamentacao"
$newLines += $entry127

$newLines | Set-Content $hostsFile -Encoding ASCII -Force
Write-Ok "Hosts file atualizado: $Hostname -> 127.0.0.1"
Write-Info "Em maquinas clientes, adicionar no hosts: $entryIP"

# ── ETAPA 6: CORS no .env ────────────────────────────────────────────────
Write-Step "6/8" "Atualizar CORS no .env"
$envFile = "$AppDir\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Encoding UTF8
    $corsLine = $envContent | Where-Object { $_ -match "^ALLOWED_ORIGINS=" }
    $newCors = "ALLOWED_ORIGINS=[`"http://${serverIP}`",`"http://${Hostname}`",`"http://localhost`",`"http://127.0.0.1`",`"http://localhost:5173`",`"http://localhost:3000`"]"
    if ($corsLine) {
        $envContent = $envContent -replace [regex]::Escape($corsLine), $newCors
    } else {
        $envContent += $newCors
    }
    $envContent | Set-Content $envFile -Encoding UTF8
    Write-Ok "CORS atualizado: IP, hostname, localhost"
} else {
    Write-Warn ".env nao encontrado em $envFile"
}

# ── ETAPA 7: Firewall ────────────────────────────────────────────────────
Write-Step "7/8" "Regras de Firewall"
netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" 2>&1 | Out-Null
netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" 2>&1 | Out-Null
netsh advfirewall firewall add rule name="Dinamica Budget HTTP" dir=in action=allow protocol=TCP localport=$HttpPort 2>&1 | Out-Null
netsh advfirewall firewall add rule name="Dinamica Budget HTTPS" dir=in action=allow protocol=TCP localport=443 2>&1 | Out-Null
Write-Ok "Portas $HttpPort (HTTP) e 443 (HTTPS) liberadas"

# ── ETAPA 8: Reiniciar servicos e validar ─────────────────────────────────
Write-Step "8/8" "Reiniciar servicos e validar"

# Reiniciar API (para pegar novo CORS)
if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
    nssm restart $ServiceName 2>&1 | Out-Null
    Write-Ok "Servico $ServiceName reiniciado"
} else {
    Write-Warn "Servico $ServiceName nao encontrado"
}

# IIS reset
iisreset /restart 2>&1 | Out-Null
Write-Ok "IIS reiniciado"

# Aguardar API subir
Write-Info "Aguardando API iniciar (ate 45s)..."
$apiOk = $false
for ($i = 0; $i -lt 15; $i++) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:${ApiPort}/health" -TimeoutSec 3
        if ($r.status -eq "ok") { $apiOk = $true; break }
    } catch { }
    Start-Sleep -Seconds 3
}
if ($apiOk) {
    Write-Ok "API respondendo em http://127.0.0.1:${ApiPort}/health"
} else {
    Write-Warn "API nao respondeu. Verifique logs: $AppDir\logs\stderr.log"
}

# Testar IIS proxy
Start-Sleep -Seconds 2
$iisOk = $false
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1/health" -TimeoutSec 5
    if ($r.status -eq "ok") { $iisOk = $true }
} catch { }
if ($iisOk) {
    Write-Ok "IIS proxy funcionando: http://127.0.0.1/health"
} else {
    Write-Warn "IIS proxy nao respondeu em http://127.0.0.1/health"
}

# Testar frontend
$feOk = $false
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1/" -TimeoutSec 5 -UseBasicParsing
    if ($r.StatusCode -eq 200 -and $r.Content -match "html") { $feOk = $true }
} catch { }
if ($feOk) {
    Write-Ok "Frontend acessivel: http://127.0.0.1/"
} else {
    Write-Warn "Frontend nao respondeu em http://127.0.0.1/"
}

# Testar por IP
$ipOk = $false
try {
    $r = Invoke-WebRequest -Uri "http://${serverIP}/" -TimeoutSec 5 -UseBasicParsing
    if ($r.StatusCode -eq 200) { $ipOk = $true }
} catch { }
if ($ipOk) {
    Write-Ok "Acesso via IP: http://${serverIP}/"
} else {
    Write-Warn "Acesso via IP falhou: http://${serverIP}/"
}

# Testar por hostname
$hostOk = $false
try {
    $r = Invoke-WebRequest -Uri "http://${Hostname}/" -TimeoutSec 5 -UseBasicParsing
    if ($r.StatusCode -eq 200) { $hostOk = $true }
} catch { }
if ($hostOk) {
    Write-Ok "Acesso via URL: http://${Hostname}/"
} else {
    Write-Warn "Acesso via URL falhou: http://${Hostname}/"
}

# ── RESUMO ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   RESUMO" -ForegroundColor White
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "   ACESSO AO SISTEMA:" -ForegroundColor White
Write-Host "   Pelo IP:      http://${serverIP}" -ForegroundColor Green
Write-Host "   Pela URL:     http://${Hostname}" -ForegroundColor Green
Write-Host "   API Docs:     http://${serverIP}/docs" -ForegroundColor Green
Write-Host "   Health:       http://${serverIP}/health" -ForegroundColor Green
Write-Host ""
Write-Host "   PARA CLIENTES NA REDE:" -ForegroundColor Yellow
Write-Host "   Adicionar no hosts (C:\Windows\System32\drivers\etc\hosts):" -ForegroundColor Yellow
Write-Host "   ${serverIP}       ${Hostname}" -ForegroundColor White
Write-Host ""
Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor Cyan
