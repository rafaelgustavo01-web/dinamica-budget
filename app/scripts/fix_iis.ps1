# fix_iis.ps1 - Disable WebDAV, ensure RequestFiltering allows PATCH/PUT, ensure site bindings and restart IIS
param()

Write-Host "Running IIS fixes as admin..."
# Disable WebDAV Publishing feature if installed
try {
    $feature = Get-WindowsFeature Web-DAV-Publishing -ErrorAction Stop
    if ($feature.Installed) {
        Write-Host "Removing Web-DAV-Publishing..."
        Remove-WindowsFeature Web-DAV-Publishing -Restart:$false -ErrorAction Stop
        Write-Host "Web-DAV removed"
    } else {
        Write-Host "Web-DAV not installed"
    }
} catch {
    Write-Warn "Could not check/remove Web-DAV: $_"
}

# Ensure ARR proxy enabled
Import-Module WebAdministration -ErrorAction SilentlyContinue
if (Get-Module -Name WebAdministration -ListAvailable) {
    Write-Host "WebAdministration available"
} else {
    Write-Warn "WebAdministration module not available"
}

# Ensure Request Filtering does not deny PATCH/PUT verbs
$appcmd = Join-Path $env:windir 'system32\inetsrv\appcmd.exe'
if (Test-Path $appcmd) {
    Write-Host "Checking requestFiltering for Default Web Site..."
    try {
        $cfg = & $appcmd list config "Default Web Site" -section:system.webServer/security/requestFiltering
        Write-Host $cfg
    } catch {
        Write-Warn "Could not read requestFiltering: $_"
    }
    # Remove deny for PATCH if exists
    try {
        & $appcmd set config "Default Web Site" -section:system.webServer/security/requestFiltering /-"verbs[@verb='PATCH']" 2>&1 | Out-Null
        & $appcmd set config "Default Web Site" -section:system.webServer/security/requestFiltering /-"verbs[@verb='PUT']" 2>&1 | Out-Null
        Write-Host "Removed any deny entries for PATCH/PUT (if present)"
    } catch {
        Write-Warn "Could not remove deny verbs: $_"
    }
} else {
    Write-Warn "appcmd not found: $appcmd"
}

# Ensure Default Web Site binding includes all unassigned on port 80
try {
    $sites = & $appcmd list site
    Write-Host $sites
    # Add binding to *:80 if not present
    $has80 = (& $appcmd list site "Default Web Site" ) -match ":80:"
    if (-not $has80) {
        Write-Host "Adding binding http/*:80: to Default Web Site"
        & $appcmd set site /site.name:"Default Web Site" /+bindings.[protocol='http',bindingInformation='*:80:']
    } else {
        Write-Host "Default Web Site already has port 80 binding"
    }
} catch {
    Write-Warn "Error checking/adding bindings: $_"
}

# Restart IIS
Write-Host "Restarting IIS..."
try {
    iisreset /restart | Write-Host
} catch {
    Write-Warn "iisreset failed: $_"
}

Write-Host "IIS fixes complete." 
