$log = 'C:\Dinamica-Budget\logs\pgvec2.txt'
$dest = 'C:\Windows\Temp\pgvector.zip'
$pgShare = 'C:\Program Files\PostgreSQL\16\share\extension'
$pgLib   = 'C:\Program Files\PostgreSQL\16\lib'

$urls = @(
    'https://github.com/pgvector/pgvector/releases/download/v0.7.4/pgvector-v0.7.4-pg16-windows-x64.zip',
    'https://github.com/pgvector/pgvector/releases/download/v0.7.2/pgvector-v0.7.2-pg16-windows-x64.zip',
    'https://github.com/pgvector/pgvector/releases/download/v0.7.0/pgvector-v0.7.0-pg16-windows-x64.zip',
    'https://github.com/pgvector/pgvector/releases/download/v0.8.0/vector-pg16.zip',
    'https://github.com/pgvector/pgvector/releases/download/v0.7.4/vector-pg16.zip'
)

"[INFO] Tentando baixar pgvector..." | Out-File $log -Encoding utf8

$downloaded = $false
foreach ($url in $urls) {
    "[INFO] URL: $url" | Out-File $log -Append -Encoding utf8
    $wc = New-Object System.Net.WebClient
    try {
        $wc.DownloadFile($url, $dest)
        $sz = (Get-Item $dest -ErrorAction SilentlyContinue).Length
        if ($sz -gt 10000) {
            $msg = "[OK] Baixado: $url ($sz bytes)"
            $msg | Out-File $log -Append -Encoding utf8
            $downloaded = $true
            break
        } else {
            "[WARN] Arquivo muito pequeno: $sz bytes" | Out-File $log -Append -Encoding utf8
        }
    } catch {
        "[WARN] Falhou: $_" | Out-File $log -Append -Encoding utf8
    }
}

if (-not $downloaded) {
    "[FAIL] Nenhuma URL funcionou para pgvector" | Out-File $log -Append -Encoding utf8
    exit 1
}

# Extrai e instala
$extractDir = 'C:\Windows\Temp\pgvector_extracted'
if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
Expand-Archive $dest -DestinationPath $extractDir -Force

"[INFO] Copiando arquivos para PostgreSQL..." | Out-File $log -Append -Encoding utf8
Get-ChildItem $extractDir -Recurse -Filter '*.control' | ForEach-Object {
    Copy-Item $_.FullName $pgShare -Force
    "[OK] $($_.Name) -> $pgShare" | Out-File $log -Append -Encoding utf8
}
Get-ChildItem $extractDir -Recurse -Filter '*.sql' | ForEach-Object {
    Copy-Item $_.FullName $pgShare -Force
}
Get-ChildItem $extractDir -Recurse -Filter '*.dll' | ForEach-Object {
    Copy-Item $_.FullName $pgLib -Force
    "[OK] $($_.Name) -> $pgLib" | Out-File $log -Append -Encoding utf8
}

$ctrl = "$pgShare\vector.control"
if (Test-Path $ctrl) {
    "[OK] pgvector instalado com sucesso!" | Out-File $log -Append -Encoding utf8
    exit 0
} else {
    "[FAIL] vector.control nao encontrado apos instalacao" | Out-File $log -Append -Encoding utf8
    exit 1
}
