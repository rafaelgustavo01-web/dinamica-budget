$token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OGJjMTBlZS1lY2ViLTQ0ZjctOThkMy01MTM3ZDcyZjJiNWEiLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc3NTA2MTQyfQ.zV2dFotfpjswIsTosrE8ymyYxPmKGTwvht-xmpKSgJU'
$body = @{ texto_busca = 'alvenaria'; limite_resultados = 5; threshold_score = 0.65 } | ConvertTo-Json

function TryPost($url) {
    Write-Host "POST $url"
    try {
        $r = Invoke-WebRequest -Uri $url -Method Post -Body $body -ContentType 'application/json' -Headers @{ Authorization = "Bearer $token" } -UseBasicParsing
        Write-Host $r.StatusCode
        Write-Host $r.Headers['Content-Type']
        if ($r.Content) { Write-Host ($r.Content.Substring(0, [Math]::Min(800, $r.Content.Length))) }
    } catch {
        if ($_.Exception.Response) {
            $code = $_.Exception.Response.StatusCode.Value__
            Write-Host "ERROR STATUS: $code"
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $text = $reader.ReadToEnd()
            Write-Host $text
        } else {
            Write-Host "ERROR: $_"
        }
    }
    Write-Host ""
}

TryPost 'http://127.0.0.1:8000/api/v1/busca/servicos'
TryPost 'http://127.0.0.1:8000/api/v1/busca/servicos/'
