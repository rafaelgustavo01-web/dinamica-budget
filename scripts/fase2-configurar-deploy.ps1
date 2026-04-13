#Requires -RunAsAdministrator
<#
.SYNOPSIS
    FASE 2 — Obtém token do GitHub, instala Docker e GitHub Actions Runner no WSL2.

.DESCRIPTION
    Execute APÓS reiniciar o servidor e inicializar o Ubuntu pela primeira vez (Fase 1).
    O script vai:
      1. Pedir seu GitHub PAT para gerar o token do runner
      2. Rodar o setup de Docker + runner dentro do WSL2
      3. Criar Task Scheduler para manter WSL2 rodando
      4. Mostrar o que configurar no GitHub

.PARAMETER GitHubOwner
    Dono do repositório (ex: rafaelgustavo01-web)

.PARAMETER GitHubRepo
    Nome do repositório (ex: Dinamica-Budget)

.PARAMETER RunnerName
    Nome amigável para o runner (padrão: servidor-producao)

.PARAMETER WslDistro
    Nome da distribuição WSL2 (padrão: Ubuntu-22.04)

.EXAMPLE
    .\scripts\fase2-configurar-deploy.ps1
    .\scripts\fase2-configurar-deploy.ps1 -GitHubOwner "meuUsuario" -GitHubRepo "MeuRepo"
#>
param(
    [string]$GitHubOwner = "rafaelgustavo01-web",
    [string]$GitHubRepo  = "Dinamica-Budget",
    [string]$RunnerName  = "servidor-producao",
    [string]$WslDistro   = "Ubuntu-22.04"
)

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/$GitHubOwner/$GitHubRepo"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  FASE 2 — Docker + GitHub Actions Runner no WSL2      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repositório: $RepoUrl" -ForegroundColor Yellow
Write-Host ""

# ── Verificar se WSL2 está disponível ────────────────────────────────────────
Write-Host "[Verificação] Checando WSL2..." -ForegroundColor Yellow
try {
    $wslList = wsl --list --quiet 2>&1
    if ($wslList -notmatch "Ubuntu") {
        Write-Error "Ubuntu não encontrado no WSL2. Execute a Fase 1, reinicie e inicialize o Ubuntu primeiro."
        exit 1
    }
    Write-Host "              ✅ WSL2 com Ubuntu disponível." -ForegroundColor Green
} catch {
    Write-Error "WSL2 não encontrado. Execute a Fase 1 primeiro."
    exit 1
}

# ── Token do GitHub ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║  PASSO: Criar Personal Access Token (PAT) no GitHub             ║" -ForegroundColor Yellow
Write-Host "╠══════════════════════════════════════════════════════════════════╣" -ForegroundColor Yellow
Write-Host "║  1. Abra: https://github.com/settings/tokens/new                ║" -ForegroundColor Yellow
Write-Host "║  2. Note: 'Deploy Server Runner'                                 ║" -ForegroundColor Yellow
Write-Host "║  3. Expiration: 90 days (ou No expiration)                       ║" -ForegroundColor Yellow
Write-Host "║  4. Permissões necessárias: marque 'repo' (completo)             ║" -ForegroundColor Yellow
Write-Host "║  5. Clique em 'Generate token'                                   ║" -ForegroundColor Yellow
Write-Host "║  6. COPIE o token (começa com ghp_...)                           ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

$securePat = Read-Host "Cole o seu GitHub PAT aqui" -AsSecureString
$pat = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePat)
)

if (-not $pat.StartsWith("ghp_") -and -not $pat.StartsWith("github_pat_")) {
    Write-Warning "O token parece inválido. Tokens GitHub começam com 'ghp_' ou 'github_pat_'."
    Write-Warning "Continuando mesmo assim..."
}

# ── Obter token de registro do runner via API GitHub ─────────────────────────
Write-Host ""
Write-Host "[1/4] Obtendo token de registro do runner (válido por 1 hora)..." -ForegroundColor Yellow

try {
    $headers = @{
        Authorization            = "token $pat"
        Accept                   = "application/vnd.github+json"
        "X-GitHub-Api-Version"   = "2022-11-28"
    }
    $apiResponse = Invoke-RestMethod `
        -Uri     "https://api.github.com/repos/$GitHubOwner/$GitHubRepo/actions/runners/registration-token" `
        -Method  POST `
        -Headers $headers

    $runnerToken = $apiResponse.token
    $tokenExpiry = $apiResponse.expires_at
    Write-Host "      ✅ Token obtido! Válido até: $tokenExpiry" -ForegroundColor Green
} catch {
    Write-Error "Falha ao obter token. Verifique: usuario ($GitHubOwner), repositório ($GitHubRepo) e permissões do PAT (precisa de 'repo')."
    exit 1
} finally {
    # Limpar PAT da memória imediatamente após uso
    $pat = ("x" * 40)
    $pat = $null
    [System.GC]::Collect()
}

# ── Preparar script bash para WSL2 ───────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Preparando script de setup para o WSL2..." -ForegroundColor Yellow

# Caminho do template bash (relativo a este script)
$scriptDir     = Split-Path -Parent $MyInvocation.MyCommand.Path
$templatePath  = Join-Path $scriptDir "fase2-wsl-setup.sh"

if (-not (Test-Path $templatePath)) {
    Write-Error "Template não encontrado: $templatePath. Certifique-se que 'fase2-wsl-setup.sh' está na pasta scripts/."
    exit 1
}

# Substituir placeholders
$bashContent = (Get-Content $templatePath -Raw -Encoding UTF8) `
    -replace "__RUNNER_TOKEN__", $runnerToken `
    -replace "__REPO_URL__",     $RepoUrl     `
    -replace "__RUNNER_NAME__",  $RunnerName

# Salvar em local acessível pelo WSL2 (usando LF e sem BOM)
$tempBashPath = "$env:TEMP\dinamica-wsl-setup-$([System.Guid]::NewGuid().ToString('N').Substring(0,8)).sh"
[System.IO.File]::WriteAllText($tempBashPath, $bashContent.Replace("`r`n", "`n"))

# Converter caminho Windows → caminho WSL2
$driveLetter = $tempBashPath[0].ToString().ToLower()
$wslPath = "/mnt/$driveLetter/" + $tempBashPath.Substring(3).Replace('\', '/')

Write-Host "      ✅ Script preparado." -ForegroundColor Green

# ── Executar setup dentro do WSL2 ────────────────────────────────────────────
Write-Host ""
Write-Host "[3/4] Executando setup dentro do WSL2 (pode demorar 5-10 minutos)..." -ForegroundColor Yellow
Write-Host "      Acompanhe o progresso abaixo:" -ForegroundColor Yellow
Write-Host ""

try {
    wsl -d $WslDistro -- bash "$wslPath"
} catch {
    Write-Error "Falha ao executar setup no WSL2: $_"
    exit 1
} finally {
    # Limpar arquivo temporário com o token
    if (Test-Path $tempBashPath) { Remove-Item $tempBashPath -Force }
}

# ── Criar Task Scheduler para manter WSL2 rodando após reinicialização ────────
Write-Host ""
Write-Host "[4/4] Criando tarefa para iniciar WSL2 automaticamente no boot..." -ForegroundColor Yellow

$taskAction    = New-ScheduledTaskAction -Execute "wsl.exe" `
    -Argument "-d $WslDistro -- bash -c 'sleep infinity'"
$taskTrigger   = New-ScheduledTaskTrigger -AtStartup
$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId    "NT AUTHORITY\SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel  Highest
$taskSettings  = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `   # sem limite de tempo
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Register-ScheduledTask `
        -TaskName   "WSL2-Dinamica-Budget-Runner" `
        -Action     $taskAction `
        -Trigger    $taskTrigger `
        -Principal  $taskPrincipal `
        -Settings   $taskSettings `
        -Description "Mantém o WSL2 rodando para o GitHub Actions Runner do Dinamica-Budget" `
        -Force | Out-Null

    Write-Host "      ✅ Task Scheduler configurado." -ForegroundColor Green
} catch {
    Write-Warning "Não foi possível criar a Task Scheduler: $_"
    Write-Warning "O runner está instalado, mas pode não iniciar automaticamente após reboot."
}

# ── Reiniciar WSL2 para ativar systemd ────────────────────────────────────────
Write-Host ""
Write-Host "Reiniciando WSL2 para ativar o systemd (o runner iniciará automaticamente)..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 3
Start-Process "wsl.exe" -ArgumentList "-d $WslDistro -- sleep infinity"
Write-Host "✅ WSL2 reiniciado com systemd." -ForegroundColor Green

# ── Instruções finais ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ FASE 2 CONCLUÍDA — Servidor pronto para deploy!            ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║                                                                  ║" -ForegroundColor Green
Write-Host "║  AGORA CONFIGURE OS SECRETS NO GITHUB:                          ║" -ForegroundColor Green
Write-Host "║                                                                  ║" -ForegroundColor Green
Write-Host "║  1. Acesse: https://github.com/$GitHubOwner/$GitHubRepo" -ForegroundColor Green
Write-Host "║  2. Vá em: Settings → Secrets and variables → Actions           ║" -ForegroundColor Green
Write-Host "║  3. Clique em 'New repository secret'                            ║" -ForegroundColor Green
Write-Host "║                                                                  ║" -ForegroundColor Green
Write-Host "║  SECRET NECESSÁRIO:                                              ║" -ForegroundColor Green
Write-Host "║  ┌─────────────────┬─────────────────────────────────────────┐  ║" -ForegroundColor Green
Write-Host "║  │ Nome            │ ENV_PRODUCAO                            │  ║" -ForegroundColor Green
Write-Host "║  │ Valor           │ Conteúdo completo do seu arquivo .env   │  ║" -ForegroundColor Green
Write-Host "║  └─────────────────┴─────────────────────────────────────────┘  ║" -ForegroundColor Green
Write-Host "║                                                                  ║" -ForegroundColor Green
Write-Host "║  Verifique o runner em:                                          ║" -ForegroundColor Green
Write-Host "║  https://github.com/$GitHubOwner/$GitHubRepo/settings/actions/runners" -ForegroundColor Green
Write-Host "║                                                                  ║" -ForegroundColor Green
Write-Host "║  Após configurar o secret, faça um push para a branch main       ║" -ForegroundColor Green
Write-Host "║  e o deploy acontecerá automaticamente! 🚀                       ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
