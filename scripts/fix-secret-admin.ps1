#Requires -RunAsAdministrator
$log = "C:\Dinamica-Budget\logs\fix-secret-admin.log"
$envFile = "C:\DinamicaBudget\.env"
$lines = @()
$lines += "START: $(Get-Date -Format s)"
if (!(Test-Path $envFile)) {
    $lines += "ERROR: .env not found at $envFile"
    $lines | Set-Content $log -Encoding UTF8
    exit 1
}
$key = python -c "import secrets; print(secrets.token_hex(32))"
$content = Get-Content $envFile -Encoding UTF8
$old = $content | Where-Object { $_ -match '^SECRET_KEY=' }
if ($old) {
    $content = $content -replace [regex]::Escape($old), ("SECRET_KEY=" + $key)
} else {
    $content += ("SECRET_KEY=" + $key)
}
Set-Content $envFile $content -Encoding UTF8 -Force
$verify = (Get-Content $envFile -Encoding UTF8 | Where-Object { $_ -match '^SECRET_KEY=' })
$lines += "UPDATED: $verify"
$lines += "END: $(Get-Date -Format s)"
$lines | Set-Content $log -Encoding UTF8
Write-Output "DONE"
