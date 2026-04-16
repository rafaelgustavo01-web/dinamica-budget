$ErrorActionPreference = "Continue"
$log = "C:\Dinamica-Budget\logs\fix-deploy.log"
if (!(Test-Path "C:\Dinamica-Budget\logs")) { New-Item -ItemType Directory -Path "C:\Dinamica-Budget\logs" -Force | Out-Null }
$out = @()
$appcmd = "$env:windir\System32\inetsrv\appcmd.exe"
$out += "=== FIX DEPLOY START ==="
$out += (Get-Date).ToString()

# 1. Copy frontend to IIS webroot
$out += "--- Step 1: IIS Webroot ---"
if (!(Test-Path "C:\inetpub\DinamicaBudget")) { 
    New-Item -ItemType Directory -Path "C:\inetpub\DinamicaBudget" -Force | Out-Null
}
$robocopyOut = robocopy "C:\DinamicaBudget\frontend\dist" "C:\inetpub\DinamicaBudget" /MIR /R:2 /W:2 /NFL /NDL /NP 2>&1
$out += "robocopy exit: $LASTEXITCODE"
$out += "index.html exists: $(Test-Path 'C:\inetpub\DinamicaBudget\index.html')"

# 2. Write web.config
$out += "--- Step 2: web.config ---"
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
    <staticContent>
      <remove fileExtension=".json" />
      <mimeMap fileExtension=".json" mimeType="application/json" />
      <remove fileExtension=".woff2" />
      <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
      <remove fileExtension=".svg" />
      <mimeMap fileExtension=".svg" mimeType="image/svg+xml" />
    </staticContent>
    <rewrite>
      <rules>
        <rule name="API Reverse Proxy" stopProcessing="true">
          <match url="^(api/.*|health|docs|redoc|openapi.json)(.*)" />
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
'@ | Set-Content "C:\inetpub\DinamicaBudget\web.config" -Encoding UTF8 -Force
$out += "web.config: $(Test-Path 'C:\inetpub\DinamicaBudget\web.config')"

# 3. IIS Configuration
$out += "--- Step 3: IIS Site ---"
try { & $appcmd stop site "Default Web Site" 2>&1 | Out-Null } catch {}
$out += "Default Web Site stopped"

try { & $appcmd delete site "DinamicaBudget" 2>&1 | Out-Null } catch {}

$poolCheck = & $appcmd list apppool "DinamicaBudgetPool" 2>&1
if ($LASTEXITCODE -ne 0) {
    & $appcmd add apppool /name:"DinamicaBudgetPool" 2>&1 | Out-Null
    & $appcmd set apppool "DinamicaBudgetPool" /managedRuntimeVersion:"" 2>&1 | Out-Null
    $out += "Pool created"
} else {
    $out += "Pool exists"
}

$siteResult = & $appcmd add site /name:"DinamicaBudget" /bindings:"http/*:80:" /physicalPath:"C:\inetpub\DinamicaBudget" 2>&1
$out += "Site add: $siteResult"

& $appcmd set app "DinamicaBudget/" /applicationPool:"DinamicaBudgetPool" 2>&1 | Out-Null

# Add hostname binding
& $appcmd set site /site.name:"DinamicaBudget" /+"bindings.[protocol='http',bindingInformation='*:80:dinamica-budget.local']" 2>&1 | Out-Null
$out += "Hostname binding added"

# Add IP binding 
& $appcmd set site /site.name:"DinamicaBudget" /+"bindings.[protocol='http',bindingInformation='10.20.20.10:80:']" 2>&1 | Out-Null
$out += "IP binding added"

& $appcmd start site "DinamicaBudget" 2>&1 | Out-Null
$out += "Site started"

# 4. ARR Proxy
$out += "--- Step 4: ARR ---"
if (Test-Path "$env:windir\System32\inetsrv\requestRouter.dll") {
    & $appcmd set config -section:system.webServer/proxy /enabled:"True" /commit:apphost 2>&1 | Out-Null
    & $appcmd set config -section:system.webServer/proxy /preserveHostHeader:"True" /commit:apphost 2>&1 | Out-Null
    $out += "ARR proxy enabled"
} else {
    $out += "ARR not installed - proxy wont work"
}

# 5. Hosts file
$out += "--- Step 5: Hosts ---"
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$h = Get-Content $hostsFile -Encoding ASCII -ErrorAction SilentlyContinue
$h = $h | Where-Object { $_ -notmatch "dinamica-budget" }
$h += ""
$h += "# Dinamica Budget - Sistema de Orcamentacao"
$h += "127.0.0.1       dinamica-budget.local"
$h | Set-Content $hostsFile -Encoding ASCII -Force
$out += "Hosts updated"

# 6. Firewall
$out += "--- Step 6: Firewall ---"
netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" 2>&1 | Out-Null
netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" 2>&1 | Out-Null
netsh advfirewall firewall add rule name="Dinamica Budget HTTP" dir=in action=allow protocol=TCP localport=80 2>&1 | Out-Null
netsh advfirewall firewall add rule name="Dinamica Budget HTTPS" dir=in action=allow protocol=TCP localport=443 2>&1 | Out-Null
$out += "Firewall configured"

# 7. CORS
$out += "--- Step 7: CORS ---"
$envFile = "C:\DinamicaBudget\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Encoding UTF8
    $corsLine = $envContent | Where-Object { $_ -match "^ALLOWED_ORIGINS=" }
    $newCors = 'ALLOWED_ORIGINS=["http://10.20.20.10","http://dinamica-budget.local","http://localhost","http://127.0.0.1","http://localhost:5173","http://localhost:3000"]'
    if ($corsLine) {
        $envContent = $envContent -replace [regex]::Escape($corsLine), $newCors
    } else {
        $envContent += $newCors
    }
    $envContent | Set-Content $envFile -Encoding UTF8
    $out += "CORS updated"
}

# 8. Restart services
$out += "--- Step 8: Restart ---"
nssm restart DinamicaBudgetAPI 2>&1 | Out-Null
$out += "API restarted"
iisreset /restart 2>&1 | Out-Null
$out += "IIS restarted"

# 9. Health checks (wait for API)
$out += "--- Step 9: Health Checks ---"
Start-Sleep -Seconds 8
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 10
    $out += "API health: $($r.status)"
} catch {
    $out += "API health FAILED: $_"
}

try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1/" -TimeoutSec 10 -UseBasicParsing
    $out += "Frontend (127.0.0.1): Status $($r.StatusCode)"
} catch {
    $out += "Frontend (127.0.0.1) FAILED: $($_.Exception.Message)"
}

try {
    $r = Invoke-WebRequest -Uri "http://10.20.20.10/" -TimeoutSec 10 -UseBasicParsing
    $out += "Frontend (IP): Status $($r.StatusCode)"
} catch {
    $out += "Frontend (IP) FAILED: $($_.Exception.Message)"
}

try {
    $r = Invoke-WebRequest -Uri "http://dinamica-budget.local/" -TimeoutSec 10 -UseBasicParsing
    $out += "Frontend (URL): Status $($r.StatusCode)"
} catch {
    $out += "Frontend (URL) FAILED: $($_.Exception.Message)"
}

try {
    $r = Invoke-RestMethod -Uri "http://dinamica-budget.local/health" -TimeoutSec 10
    $out += "API via URL: $($r.status)"
} catch {
    $out += "API via URL FAILED: $($_.Exception.Message)"
}

$out += "=== FIX DEPLOY DONE ==="
$out | Set-Content $log -Encoding UTF8
