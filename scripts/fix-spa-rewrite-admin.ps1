#Requires -RunAsAdministrator
$ErrorActionPreference = "Continue"

$appcmd = "$env:windir\System32\inetsrv\appcmd.exe"
$webRoot = "C:\inetpub\DinamicaBudget"
$siteName = "DinamicaBudget"
$hostName = "dinamica-budget.local"
$apiPort = 8000
$log = "C:\Dinamica-Budget\logs\fix-spa-rewrite-admin.log"

$out = @()
$out += "START: $(Get-Date -Format s)"

if (!(Test-Path $webRoot)) {
    $out += "FAIL: web root not found: $webRoot"
    $out | Set-Content $log -Encoding UTF8
    exit 1
}

# Enforce a deterministic web.config with SPA fallback and API reverse proxy.
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
    <rewrite>
      <rules>
        <rule name="API Reverse Proxy" stopProcessing="true">
          <match url="^(api/.*|health|docs|redoc|openapi.json)(.*)$" />
          <action type="Rewrite" url="http://127.0.0.1:$apiPort/{R:0}" />
        </rule>
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
  </system.webServer>
</configuration>
"@

$webConfigPath = Join-Path $webRoot "web.config"
$webConfig | Set-Content $webConfigPath -Encoding UTF8 -Force
$out += "web.config enforced: $webConfigPath"

# Make sure site is active and default site is not stealing traffic.
& $appcmd stop site "Default Web Site" | Out-Null
& $appcmd start site $siteName | Out-Null
$out += "site state refreshed"

# Test SPA deep-link routing through IIS.
$okLocal = $false
$okHost = $false
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1/login" -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -eq 200) { $okLocal = $true }
} catch {
    $out += "WARN local /login test failed: $($_.Exception.Message)"
}

try {
    $r2 = Invoke-WebRequest -Uri "http://$hostName/login" -UseBasicParsing -TimeoutSec 8
    if ($r2.StatusCode -eq 200) { $okHost = $true }
} catch {
    $out += "WARN hostname /login test failed: $($_.Exception.Message)"
}

$out += "TEST local_login=$okLocal host_login=$okHost"
$out += "END: $(Get-Date -Format s)"
$out | Set-Content $log -Encoding UTF8

if ($okLocal -and $okHost) {
    Write-Output "DONE"
    exit 0
}

Write-Output "FAIL"
exit 1
