# Fix ARR global responseTimeout to 20 minutes
# Must run as Administrator

Import-Module WebAdministration -ErrorAction SilentlyContinue

# Set ARR global proxy responseTimeout = 1200 seconds (20 min)
try {
    Set-WebConfigurationProperty -pspath "MACHINE/WEBROOT/APPHOST" `
        -filter "system.webServer/proxy" `
        -name "responseTimeout" `
        -value "00:20:00"
    Write-Host "ARR global responseTimeout set to 00:20:00"
} catch {
    Write-Warning "WebAdministration method failed: $_"
    Write-Host "Trying appcmd..."
    & "$env:SystemRoot\System32\inetsrv\appcmd.exe" set config `
        -section:system.webServer/proxy `
        /responseTimeout:"00:20:00"
}

# Also set HTTP.sys connection timeout (covers kernel-level timeouts)
try {
    & "$env:SystemRoot\System32\inetsrv\appcmd.exe" set config `
        -section:system.applicationHost/sites `
        "/[name='DinamicaBudget'].limits.connectionTimeout:00:20:00"
    Write-Host "Site connectionTimeout set to 00:20:00"
} catch {
    Write-Warning "connectionTimeout set failed: $_"
}

# Set application pool queue timeout (optional)
try {
    & "$env:SystemRoot\System32\inetsrv\appcmd.exe" set apppool `
        /apppool.name:"DinamicaBudget" `
        /processModel.idleTimeout:"00:30:00"
    Write-Host "AppPool idleTimeout set to 00:30:00"
} catch {
    Write-Warning "AppPool timeout set failed: $_"
}

iisreset /noforce
Write-Host "IIS reset done."
