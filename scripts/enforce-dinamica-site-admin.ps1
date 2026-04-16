#Requires -RunAsAdministrator
$ErrorActionPreference = "Continue"
$appcmd = "$env:windir\System32\inetsrv\appcmd.exe"
$log = "C:\Dinamica-Budget\logs\enforce-dinamica-site-admin.log"
$out = @()
$out += "START: $(Get-Date -Format s)"

# Fix hosts file formatting and ensure entry
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$hosts = Get-Content $hostsFile -Encoding ASCII -ErrorAction SilentlyContinue
$hosts = $hosts | Where-Object { $_ -notmatch "dinamica-budget\.local" -and $_ -notmatch "# Dinamica Budget" }
$hosts += ""
$hosts += "# Dinamica Budget"
$hosts += "127.0.0.1       dinamica-budget.local"
$hosts | Set-Content $hostsFile -Encoding ASCII -Force
$out += "hosts fixed"

# Ensure Dinamica site points to correct path
& $appcmd set vdir "DinamicaBudget/" /physicalPath:"C:\inetpub\DinamicaBudget" | Out-Null
& $appcmd set app "DinamicaBudget/" /applicationPool:"DinamicaBudgetPool" | Out-Null

# Ensure bindings
& $appcmd set site /site.name:"DinamicaBudget" /+"bindings.[protocol='http',bindingInformation='*:80:']" | Out-Null
& $appcmd set site /site.name:"DinamicaBudget" /+"bindings.[protocol='http',bindingInformation='*:80:dinamica-budget.local']" | Out-Null
& $appcmd set site /site.name:"DinamicaBudget" /+"bindings.[protocol='http',bindingInformation='10.20.20.10:80:']" | Out-Null

# Stop default site and start Dinamica site
& $appcmd stop site "Default Web Site" | Out-Null
& $appcmd start site "DinamicaBudget" | Out-Null

# Restart IIS to apply cleanly
iisreset /restart | Out-Null

# Stop default again (iisreset may start it)
& $appcmd stop site "Default Web Site" | Out-Null
& $appcmd start site "DinamicaBudget" | Out-Null

# Report state
$out += "--- Sites ---"
$out += (& $appcmd list site)
$out += "--- Dinamica Site Config ---"
$out += (& $appcmd list site "DinamicaBudget")
$out += "--- Hosts Entry ---"
$out += (Get-Content $hostsFile -Encoding ASCII | Select-String "dinamica-budget\.local").ToString()
$out += "END: $(Get-Date -Format s)"
$out | Set-Content $log -Encoding UTF8
Write-Output "DONE"
