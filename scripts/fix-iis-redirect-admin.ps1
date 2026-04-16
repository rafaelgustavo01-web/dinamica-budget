#Requires -RunAsAdministrator
$ErrorActionPreference = "Continue"
$appcmd = "$env:windir\System32\inetsrv\appcmd.exe"
$log = "C:\Dinamica-Budget\logs\fix-iis-redirect-admin.log"
$out = @()
$out += "START: $(Get-Date -Format s)"

# Ensure site exists
& $appcmd list site "DinamicaBudget" > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    $out += "FAIL: Site DinamicaBudget not found"
    $out | Set-Content $log -Encoding UTF8
    exit 1
}

# Disable redirect globally and for site/app levels
$out += "Disable redirects"
& $appcmd set config -section:system.webServer/httpRedirect /enabled:"False" /destination:"" /exactDestination:"False" /httpResponseStatus:"Found" /childOnly:"False" /commit:apphost | Out-Null
& $appcmd set config "DinamicaBudget" -section:system.webServer/httpRedirect /enabled:"False" /destination:"" /exactDestination:"False" /httpResponseStatus:"Found" | Out-Null
& $appcmd set config "DinamicaBudget/" -section:system.webServer/httpRedirect /enabled:"False" /destination:"" /exactDestination:"False" /httpResponseStatus:"Found" | Out-Null

# Ensure rewrite rules file is in place
$webConfigPath = "C:\inetpub\DinamicaBudget\web.config"
if (!(Test-Path $webConfigPath)) {
@'
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <defaultDocument>
      <files><clear /><add value="index.html" /></files>
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
'@ | Set-Content $webConfigPath -Encoding UTF8 -Force
    $out += "web.config created"
}

# Ensure hosts entry exists
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$hosts = Get-Content $hostsFile -Encoding ASCII -ErrorAction SilentlyContinue
$hosts = $hosts | Where-Object { $_ -notmatch "dinamica-budget\.local" }
$hosts += ""
$hosts += "# Dinamica Budget"
$hosts += "127.0.0.1       dinamica-budget.local"
$hosts | Set-Content $hostsFile -Encoding ASCII -Force
$out += "hosts updated"

# Restart IIS
iisreset /restart | Out-Null
$out += "iis restarted"

# Log effective config snippets
$out += "--- site bindings ---"
$out += (& $appcmd list site "DinamicaBudget")
$out += "--- httpRedirect global ---"
$out += (& $appcmd list config -section:system.webServer/httpRedirect)
$out += "--- httpRedirect site ---"
$out += (& $appcmd list config "DinamicaBudget" -section:system.webServer/httpRedirect)

$out += "END: $(Get-Date -Format s)"
$out | Set-Content $log -Encoding UTF8
Write-Output "DONE"
