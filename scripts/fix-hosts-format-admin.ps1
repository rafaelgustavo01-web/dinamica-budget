#Requires -RunAsAdministrator
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$raw = Get-Content $hostsFile -Encoding ASCII -ErrorAction SilentlyContinue
$filtered = @()
foreach ($line in $raw) {
    if ($line -match 'dinamica-budget\.local') { continue }
    if ($line -match '# Dinamica Budget') { continue }
    $filtered += $line
}
if ($filtered.Count -gt 0 -and $filtered[-1] -ne "") { $filtered += "" }
$filtered += "# Dinamica Budget"
$filtered += "127.0.0.1       dinamica-budget.local"
$text = [string]::Join("`r`n", $filtered) + "`r`n"
[System.IO.File]::WriteAllText($hostsFile, $text, [System.Text.Encoding]::ASCII)
ipconfig /flushdns | Out-Null
Write-Output "HOSTS_FIXED"
