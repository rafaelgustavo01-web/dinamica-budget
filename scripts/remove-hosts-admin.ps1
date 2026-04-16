#Requires -RunAsAdministrator
$hostsFile = "$env:windir\System32\drivers\etc\hosts"
$lines = Get-Content $hostsFile -Encoding ASCII -ErrorAction SilentlyContinue
$clean = @()
foreach ($line in $lines) {
    if ($line -match 'dinamica-budget\.local') { continue }
    if ($line -match '# Dinamica Budget') { continue }
    $clean += $line
}
$text = ''
if ($clean.Count -gt 0) {
    $text = [string]::Join("`r`n", $clean) + "`r`n"
}
[System.IO.File]::WriteAllText($hostsFile, $text, [System.Text.Encoding]::ASCII)
ipconfig /flushdns | Out-Null
Write-Output 'HOSTS_REMOVED'
