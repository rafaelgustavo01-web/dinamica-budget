#Requires -RunAsAdministrator
<#
.SYNOPSIS
    FASE 1 — Instala WSL2 + Ubuntu 22.04 no Windows Server 2022.

.DESCRIPTION
    Execute este script como Administrador no servidor de produção.
    Após a conclusão, REINICIE o servidor e depois execute a Fase 2.

.EXAMPLE
    .\scripts\fase1-instalar-wsl2.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  FASE 1 — Instalando WSL2 + Ubuntu no Servidor        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Verificar Windows Server 2022 ───────────────────────────────────────────
$osCaption = (Get-WmiObject Win32_OperatingSystem).Caption
Write-Host "Sistema detectado: $osCaption" -ForegroundColor Yellow
if ($osCaption -notmatch "2022|2019") {
    Write-Warning "Este script foi testado para Windows Server 2019/2022."
}

# ── 1. Habilitar WSL ─────────────────────────────────────────────────────────
Write-Host "[1/4] Habilitando Windows Subsystem for Linux..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null
Write-Host "      ✅ WSL habilitado." -ForegroundColor Green

# ── 2. Habilitar Virtual Machine Platform ────────────────────────────────────
Write-Host "[2/4] Habilitando Virtual Machine Platform (necessário para WSL2)..." -ForegroundColor Yellow
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null
Write-Host "      ✅ Virtual Machine Platform habilitado." -ForegroundColor Green

# ── 3. Baixar e instalar kernel WSL2 ─────────────────────────────────────────
Write-Host "[3/4] Baixando kernel WSL2..." -ForegroundColor Yellow
$kernelUrl  = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
$kernelPath = "$env:TEMP\wsl_update_x64.msi"

try {
    Invoke-WebRequest -Uri $kernelUrl -OutFile $kernelPath -UseBasicParsing
    Start-Process msiexec.exe -ArgumentList "/i `"$kernelPath`" /quiet /norestart" -Wait
    Write-Host "      ✅ Kernel WSL2 instalado." -ForegroundColor Green
} catch {
    Write-Warning "Não foi possível baixar o kernel WSL2 automaticamente."
    Write-Warning "Baixe manualmente: $kernelUrl"
    Write-Warning "Instale o .msi e execute este script novamente."
    exit 1
}

# ── 4. Definir WSL2 como versão padrão e instalar Ubuntu ─────────────────────
Write-Host "[4/4] Configurando WSL2 como padrão e instalando Ubuntu 22.04..." -ForegroundColor Yellow
wsl --set-default-version 2

# Tentar instalar Ubuntu via wsl --install (disponível no Server 2022 com updates)
try {
    wsl --install -d Ubuntu-22.04 --no-launch 2>&1 | Out-Null
    Write-Host "      ✅ Ubuntu 22.04 instalado." -ForegroundColor Green
} catch {
    Write-Warning "Instalação automática não disponível. Baixe manualmente:"
    Write-Warning "https://aka.ms/wslubuntu2204"
}

# ── Limpeza ───────────────────────────────────────────────────────────────────
if (Test-Path $kernelPath) { Remove-Item $kernelPath -Force }

# ── Instruções finais ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ FASE 1 CONCLUÍDA                                        ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║  SIGA ESTES PASSOS ANTES DE CONTINUAR:                      ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║  1. REINICIE o servidor agora                                ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║  2. Após reiniciar, abra o terminal e execute:               ║" -ForegroundColor Green
Write-Host "║        wsl -d Ubuntu-22.04                                   ║" -ForegroundColor Green
Write-Host "║     Crie um usuário Linux quando solicitado (ex: deploy)     ║" -ForegroundColor Green
Write-Host "║     Defina uma senha e ANOTE — será usada pela Fase 2        ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║  3. Feche o Ubuntu e execute a Fase 2:                       ║" -ForegroundColor Green
Write-Host "║        .\scripts\fase2-configurar-deploy.ps1                 ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
