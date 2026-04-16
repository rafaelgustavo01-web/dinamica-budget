#Requires -RunAsAdministrator
$ErrorActionPreference = "Continue"

$AppDir = "C:\DinamicaBudget"
$IISRoot = "C:\inetpub\DinamicaBudget"
$SiteName = "DinamicaBudget"
$PoolName = "DinamicaBudgetPool"
$ServiceName = "DinamicaBudgetAPI"
$ApiPort = 8000
$Hostname = "dinamica-budget.local"
$ServerIP = "10.20.20.10"
$AppCmd = "$env:windir\System32\inetsrv\appcmd.exe"
$Nssm = "C:\Windows\System32\nssm.exe"
$Log = "C:\Dinamica-Budget\logs\recover-deploy-admin.log"

if (!(Test-Path "C:\Dinamica-Budget\logs")) { New-Item -ItemType Directory -Path "C:\Dinamica-Budget\logs" -Force | Out-Null }
$lines = @()
function Add-Log([string]$msg) { $script:lines += $msg }

Add-Log "=== RECOVER DEPLOY START ==="
Add-Log (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

# 1) Ensure IIS webroot and frontend files
Add-Log "[1] IIS webroot + frontend"
if (!(Test-Path $IISRoot)) { New-Item -ItemType Directory -Path $IISRoot -Force | Out-Null }
$dist = Join-Path $AppDir "frontend\dist"
if (Test-Path (Join-Path $dist "index.html")) {
    robocopy $dist $IISRoot /MIR /R:2 /W:2 /NFL /NDL /NP | Out-Null
    Add-Log "OK: frontend copied"
} else {
    Add-Log "WARN: frontend dist missing, attempting build"
    Push-Location (Join-Path $AppDir "frontend")
    npm install | Out-Null
    npm run build | Out-Null
    Pop-Location
    if (Test-Path (Join-Path $dist "index.html")) {
        robocopy $dist $IISRoot /MIR /R:2 /W:2 /NFL /NDL /NP | Out-Null
        Add-Log "OK: frontend built and copied"
    } else {
        Add-Log "FAIL: frontend dist not available"
    }
}

# 2) Write web.config (proxy + SPA fallback)
Add-Log "[2] web.config"
@'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <defaultDocument>
      <files>
        <clear />
        <add value="index.html" />
      </files>
    </defaultDocument>
    <rewrite>
      <rules>
        <rule name="API Reverse Proxy" stopProcessing="true">
          <match url="^(api/.*|health|docs|redoc|openapi.json)(.*)$" />
          <action type="Rewrite" url="http://127.0.0.1:8000/{R:0}" />
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
  </system.webServer>
</configuration>
'@ | Set-Content (Join-Path $IISRoot "web.config") -Encoding UTF8 -Force
Add-Log "OK: web.config written"

# 3) IIS pool + site + bindings
Add-Log "[3] IIS site/pool"
if (!(Test-Path $AppCmd)) { Add-Log "FAIL: appcmd missing" }
& $AppCmd stop site "Default Web Site" | Out-Null
& $AppCmd list apppool $PoolName | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $AppCmd add apppool /name:$PoolName | Out-Null
    & $AppCmd set apppool $PoolName /managedRuntimeVersion:"" | Out-Null
    Add-Log "OK: pool created"
} else {
    Add-Log "OK: pool exists"
}
& $AppCmd delete site $SiteName | Out-Null
& $AppCmd add site /name:$SiteName /bindings:"http/*:80:" /physicalPath:$IISRoot | Out-Null
if ($LASTEXITCODE -eq 0) { Add-Log "OK: site created" } else { Add-Log "WARN: site create returned nonzero" }
& $AppCmd set app "$SiteName/" /applicationPool:$PoolName | Out-Null
& $AppCmd set site /site.name:$SiteName /+"bindings.[protocol='http',bindingInformation='*:80:$Hostname']" | Out-Null
& $AppCmd set site /site.name:$SiteName /+"bindings.[protocol='http',bindingInformation='$ServerIP:80:']" | Out-Null

# Disable any inherited HTTP redirect that was causing 302 to localhost:8000
& $AppCmd set config $SiteName -section:system.webServer/httpRedirect /enabled:"False" /destination:"" /exactDestination:"False" /httpResponseStatus:"Found" | Out-Null

# Enable ARR proxy if available
& $AppCmd set config -section:system.webServer/proxy /enabled:"True" /commit:apphost | Out-Null
& $AppCmd set config -section:system.webServer/proxy /preserveHostHeader:"True" /commit:apphost | Out-Null

& $AppCmd start site $SiteName | Out-Null
Add-Log "OK: site started"

# 4) Hosts + firewall
Add-Log "[4] hosts + firewall"
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$hosts = Get-Content $hostsFile -Encoding ASCII -ErrorAction SilentlyContinue
$hosts = $hosts | Where-Object { $_ -notmatch "dinamica-budget" }
$hosts += ""
$hosts += "# Dinamica Budget"
$hosts += "127.0.0.1       $Hostname"
$hosts | Set-Content $hostsFile -Encoding ASCII -Force
netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" | Out-Null
netsh advfirewall firewall add rule name="Dinamica Budget HTTP" dir=in action=allow protocol=TCP localport=80 | Out-Null
netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" | Out-Null
netsh advfirewall firewall add rule name="Dinamica Budget HTTPS" dir=in action=allow protocol=TCP localport=443 | Out-Null
Add-Log "OK: hosts and firewall updated"

# 5) CORS update
Add-Log "[5] CORS"
$envFile = Join-Path $AppDir ".env"
if (Test-Path $envFile) {
    $content = Get-Content $envFile -Encoding UTF8
    $newCors = 'ALLOWED_ORIGINS=["http://10.20.20.10","http://dinamica-budget.local","http://localhost","http://127.0.0.1","http://localhost:5173","http://localhost:3000"]'
    $old = $content | Where-Object { $_ -match '^ALLOWED_ORIGINS=' }
    if ($old) { $content = $content -replace [regex]::Escape($old), $newCors } else { $content += $newCors }
    $content | Set-Content $envFile -Encoding UTF8
    Add-Log "OK: CORS updated"
} else {
    Add-Log "WARN: .env missing"
}

# 6) Ensure service exists and start API
Add-Log "[6] API service"
if (!(Test-Path $Nssm)) { Add-Log "FAIL: NSSM missing" }
$pythonExe = Join-Path $AppDir "venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) { Add-Log "FAIL: python in venv missing" }
sc.exe query $ServiceName | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $Nssm install $ServiceName $pythonExe "-m uvicorn app.main:app --host 127.0.0.1 --port $ApiPort --workers 2" | Out-Null
    & $Nssm set $ServiceName AppDirectory $AppDir | Out-Null
    & $Nssm set $ServiceName Start SERVICE_AUTO_START | Out-Null
    & $Nssm set $ServiceName DisplayName "Dinamica Budget API" | Out-Null
    & $Nssm set $ServiceName Description "FastAPI backend Dinamica Budget" | Out-Null
    Add-Log "OK: service installed"
} else {
    Add-Log "OK: service exists"
}
& $Nssm restart $ServiceName | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $Nssm start $ServiceName | Out-Null
}
Add-Log "OK: service restart/start requested"

iisreset /restart | Out-Null
Start-Sleep -Seconds 8

# 7) Validation
Add-Log "[7] validation"
try { $h = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 8; Add-Log "API: $($h.status)" } catch { Add-Log "API FAIL: $($_.Exception.Message)" }
try { $r = curl.exe -I "http://127.0.0.1/" 2>$null; Add-Log "IIS localhost: $($r -join ' ')" } catch { Add-Log "IIS localhost FAIL" }
try { $r = curl.exe -I "http://$ServerIP/" 2>$null; Add-Log "IIS IP: $($r -join ' ')" } catch { Add-Log "IIS IP FAIL" }
try { $r = curl.exe -I "http://$Hostname/" 2>$null; Add-Log "IIS host: $($r -join ' ')" } catch { Add-Log "IIS host FAIL" }
try { $r = Invoke-RestMethod "http://127.0.0.1/health" -TimeoutSec 8; Add-Log "Proxy health: $($r.status)" } catch { Add-Log "Proxy FAIL: $($_.Exception.Message)" }

Add-Log "=== RECOVER DEPLOY END ==="
$lines | Set-Content $Log -Encoding UTF8
Write-Output "DONE: $Log"
