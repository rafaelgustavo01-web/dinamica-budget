#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Finaliza a configuração do Dinamica Budget após as migrações do banco de dados.
    Copia frontend, configura IIS, instala serviço NSSM e configura firewall.
    Execute como Administrador: PowerShell -ExecutionPolicy Bypass -File finish-setup.ps1
#>

$ErrorActionPreference = 'Continue'
$log = 'C:\Dinamica-Budget\logs\finish-setup.log'
$srcFront = 'C:\Dinamica-Budget\frontend\dist'
$iisRoot   = 'C:\inetpub\DinamicaBudget'
$deployDir = 'C:\DinamicaBudget'
$siteName  = 'DinamicaBudget'
$svcName   = 'DinamicaBudgetAPI'
$uvicornExe = "$deployDir\venv\Scripts\python.exe"
$uvicornArgs = '-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2'
$apiPort   = 8000
$httpPort  = 80

function Log($msg) {
    $ts = Get-Date -Format 'HH:mm:ss'
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content $log $line -Encoding utf8
}

New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
"=== finish-setup.ps1 iniciado $(Get-Date) ===" | Out-File $log -Encoding utf8

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Log "Executando como admin: $isAdmin"

# ── Etapa A: Permissões no diretório de deploy ─────────────────────────────
Log "[A] Corrigindo permissoes em $deployDir..."
try {
    $acl = Get-Acl $deployDir
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        'BUILTIN\Users', 'ReadAndExecute', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
    $acl.AddAccessRule($rule)
    Set-Acl $deployDir $acl
    Log "[A] OK"
} catch {
    Log "[A] AVISO: Nao foi possivel alterar ACL: $_"
}

# ── Etapa B: Copiar frontend dist para IIS root ────────────────────────────
Log "[B] Criando $iisRoot..."
New-Item -ItemType Directory -Force -Path $iisRoot | Out-Null
Log "[B] Copiando dist do frontend..."
robocopy $srcFront $iisRoot /MIR /NJH /NJS /NDL | Out-Null
Log "[B] Frontend copiado ($((Get-ChildItem $iisRoot -Recurse -File).Count) arquivos)"

# ── Etapa C: Escrever web.config ───────────────────────────────────────────
Log "[C] Escrevendo web.config..."
$webConfig = @'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <!-- Proxy /api/ and /docs /redoc /openapi.json to uvicorn -->
        <rule name="API Proxy" stopProcessing="true">
          <match url="^(api|docs|redoc|openapi\.json)(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:8000/{R:1}{R:2}" />
        </rule>
        <!-- SPA fallback: send everything else to index.html -->
        <rule name="SPA Fallback" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
    <staticContent>
      <mimeMap fileExtension=".js"   mimeType="application/javascript" />
      <mimeMap fileExtension=".mjs"  mimeType="application/javascript" />
      <mimeMap fileExtension=".css"  mimeType="text/css" />
      <mimeMap fileExtension=".svg"  mimeType="image/svg+xml" />
      <mimeMap fileExtension=".woff" mimeType="font/woff" />
      <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
      <mimeMap fileExtension=".json" mimeType="application/json" />
    </staticContent>
    <httpErrors errorMode="Detailed" />
  </system.webServer>
</configuration>
'@
$webConfig | Out-File "$iisRoot\web.config" -Encoding utf8 -Force
Log "[C] web.config escrito"

# ── Etapa D: Habilitar proxy ARR no IIS ───────────────────────────────────
Log "[D] Habilitando proxy ARR..."
$appcmd = "$env:SystemRoot\System32\inetsrv\appcmd.exe"
& $appcmd set config -section:system.webServer/proxy /enabled:True /commit:apphost 2>&1 | ForEach-Object { Log "  ARR: $_" }
Log "[D] OK"

# ── Etapa E: Criar site IIS DinamicaBudget ────────────────────────────────
Log "[E] Configurando site IIS '$siteName'..."
$existingSite = & $appcmd list site /name:$siteName 2>&1
if ($existingSite -match "SITE") {
    Log "[E] Site ja existe, atualizando physicalPath..."
    & $appcmd set site /site.name:$siteName "/[path='/'].physicalPath:$iisRoot" 2>&1 | ForEach-Object { Log "  $_" }
} else {
    Log "[E] Criando site novo..."
    & $appcmd add site /name:$siteName /physicalPath:$iisRoot /bindings:"http/*:${httpPort}:" 2>&1 | ForEach-Object { Log "  $_" }
}
Log "[E] OK"

# ── Etapa F: Instalar/atualizar servico NSSM ─────────────────────────────
Log "[F] Configurando servico NSSM '$svcName'..."
$nssmPath = (Get-Command nssm -ErrorAction SilentlyContinue).Source
if (-not $nssmPath) {
    Log "[F] ERRO: nssm nao encontrado no PATH!"
    exit 1
}
$existingSvc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
if ($existingSvc) {
    Log "[F] Servico existente, parando e reconfigurando..."
    nssm stop $svcName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    nssm remove $svcName confirm 2>&1 | Out-Null
    Start-Sleep -Seconds 1
}
Log "[F] Instalando servico..."
nssm install $svcName $uvicornExe $uvicornArgs 2>&1 | ForEach-Object { Log "  $_" }
nssm set $svcName AppDirectory $deployDir 2>&1 | Out-Null
nssm set $svcName AppEnvironmentExtra "PYTHONPATH=$deployDir" 2>&1 | Out-Null
nssm set $svcName AppStdout "$deployDir\logs\uvicorn.log" 2>&1 | Out-Null
nssm set $svcName AppStderr "$deployDir\logs\uvicorn_err.log" 2>&1 | Out-Null
nssm set $svcName Start SERVICE_AUTO_START 2>&1 | Out-Null
nssm set $svcName DisplayName "Dinamica Budget API" 2>&1 | Out-Null
nssm set $svcName Description "Uvicorn FastAPI backend para Dinamica Budget" 2>&1 | Out-Null
Log "[F] Servico configurado"

# ── Etapa G: Regras de firewall ───────────────────────────────────────────
Log "[G] Configurando firewall..."
$ports = @(80, 443, 8000)
foreach ($p in $ports) {
    $ruleName = "DinamicaBudget-TCP$p"
    netsh advfirewall firewall delete rule name=$ruleName 2>&1 | Out-Null
    netsh advfirewall firewall add rule name=$ruleName dir=in action=allow protocol=TCP localport=$p 2>&1 | ForEach-Object { Log "  FW $p`: $_" }
}
Log "[G] OK"

# ── Etapa H: Iniciar servico ──────────────────────────────────────────────
Log "[H] Iniciando servico $svcName..."
New-Item -ItemType Directory -Force -Path "$deployDir\logs" | Out-Null
nssm start $svcName 2>&1 | ForEach-Object { Log "  $_" }
Start-Sleep -Seconds 5

# ── Etapa I: Iniciar site IIS ─────────────────────────────────────────────
Log "[I] Iniciando site IIS..."
& $appcmd start site /site.name:$siteName 2>&1 | ForEach-Object { Log "  $_" }
iisreset /noforce 2>&1 | ForEach-Object { Log "  IISRESET: $_" }
Log "[I] OK"

# ── Etapa J: Health check ─────────────────────────────────────────────────
Log "[J] Health check em http://127.0.0.1:$apiPort/health ..."
$ok = $false
for ($i = 1; $i -le 12; $i++) {
    Start-Sleep -Seconds 5
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$apiPort/health" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) {
            Log "[J] OK - API respondeu com 200 ($($resp.Content))"
            $ok = $true
            break
        }
    } catch {
        Log "[J] Tentativa $i falhou: $_"
    }
}
if (-not $ok) {
    Log "[J] AVISO: API nao respondeu em 60s. Verifique os logs em $deployDir\logs\uvicorn_err.log"
}

# ── Resumo ───────────────────────────────────────────────────────────────
Log ""
Log "========================================================="
Log " INSTALACAO CONCLUIDA"
Log "========================================================="
Log " Frontend: http://localhost:$httpPort"
Log " API:      http://127.0.0.1:$apiPort"
Log " API docs: http://127.0.0.1:$apiPort/docs"
Log " Servico:  $svcName ($(( Get-Service $svcName -ErrorAction SilentlyContinue ).Status))"
Log " Log:      $log"
Log "========================================================="
if (-not $ok) {
    Log " ATENCAO: Verifique $deployDir\logs\uvicorn_err.log para erros da API"
}
