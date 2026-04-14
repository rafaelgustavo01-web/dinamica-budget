@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Dinamica Budget — Deploy Producao (Windows Server 2022)

:: ══════════════════════════════════════════════════════════════════════════════
::  DINAMICA BUDGET — Deploy Completo de Producao
::  Servidor: Windows Server 2022 | Intranet
::
::  Este script faz TUDO automaticamente:
::    ETAPA  1 — Verificar Administrador e pre-requisitos do SO
::    ETAPA  2 — Habilitar features (WSL2 + VirtualMachinePlatform + HypervisorPlatform)
::    ETAPA  3 — Instalar WSL2 + Ubuntu 22.04
::    ETAPA  4 — Instalar Docker Engine no WSL2
::    ETAPA  5 — Sincronizar projeto para o WSL2
::    ETAPA  6 — Gerar .env de producao
::    ETAPA  7 — Docker Compose: Build + Deploy
::    ETAPA  8 — Health Check + Firewall + Informacoes
::
::  Logs salvos em: %~dp0logs\deploy-YYYY-MM-DD_HHMMSS.log
::  Info salva em:  %~dp0logs\deploy-info.txt
::
::  Requisitos: Windows Server 2022, acesso admin, internet (1a vez)
::  Seguro re-executar: detecta estado atual e pula etapas ja concluidas.
:: ══════════════════════════════════════════════════════════════════════════════

:: ── Variaveis globais ────────────────────────────────────────────────────────
set "SCRIPT_START_TIME=%date% %time%"
set "WSL_DISTRO=Ubuntu-22.04"
set "WSL_APP_DIR=/opt/dinamica-budget"
set "WSL_USER="
set "API_PORT=8000"
set "DB_PORT=5432"
set "API_OK=0"

:: ── Raiz do projeto (onde este .bat esta) ────────────────────────────────────
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

:: ── Diretorio de logs ────────────────────────────────────────────────────────
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"
for /f "delims=" %%d in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HHmmss'"') do set "LOG_TS=%%d"
set "LOG_FILE=%PROJECT_ROOT%\logs\deploy-%LOG_TS%.log"
set "INFO_FILE=%PROJECT_ROOT%\logs\deploy-info.txt"

:: ── Funcao de log (ecoa + grava arquivo) ─────────────────────────────────────
:: Uso: call :log "mensagem"
goto :skip_log_func
:log
set "LOG_MSG=%~1"
if "!LOG_MSG!"=="" (echo.) else (echo !LOG_MSG!)
>> "%LOG_FILE%" echo [%date% %time%] !LOG_MSG!
goto :eof
:skip_log_func

:: ── IP do servidor ───────────────────────────────────────────────────────────
set "SERVER_IP=localhost"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" ^| findstr /v "127.0.0.1"') do (
    set "TMP_IP=%%a"
    set "TMP_IP=!TMP_IP: =!"
    if "!SERVER_IP!"=="localhost" set "SERVER_IP=!TMP_IP!"
)

echo.
echo ============================================================
echo   DINAMICA BUDGET — Deploy Producao
echo   Windows Server 2022 ^| WSL2 + Docker
echo ============================================================
echo.
call :log "Inicio        : !SCRIPT_START_TIME!"
call :log "Diretorio     : %PROJECT_ROOT%"
call :log "Servidor      : %COMPUTERNAME% (!SERVER_IP!)"
call :log "Log de deploy : %LOG_FILE%"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 1/8 — Verificar Administrador + Pre-requisitos
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 1/8] Verificar Administrador e SO"
echo.

:: Admin check
net session >nul 2>&1
if !errorlevel! neq 0 (
    call :log "   [ERRO] Executar como Administrador. Clique direito → Executar como administrador."
    goto :fim_erro
)
call :log "   [OK] Executando como Administrador"

:: Verificar build do Windows (Server 2022 = build 20348+)
set "WIN_BUILD=0"
for /f "delims=" %%b in ('powershell -NoProfile -Command "[System.Environment]::OSVersion.Version.Build"') do set "WIN_BUILD=%%b"
call :log "   Windows Build: !WIN_BUILD!"

if !WIN_BUILD! LSS 20348 (
    call :log "   [ERRO] Este script requer Windows Server 2022 (build 20348+)."
    call :log "          Build detectado: !WIN_BUILD!"
    call :log "          Para Server 2019, utilize o script alternativo."
    goto :fim_erro
)
call :log "   [OK] Windows Server 2022 confirmado"

:: Verificar arquivos essenciais
for %%f in (Dockerfile docker-compose.yml requirements.txt alembic.ini .env.example) do (
    if not exist "%PROJECT_ROOT%\%%f" (
        call :log "   [ERRO] Arquivo ausente: %%f"
        goto :fim_erro
    )
)
if not exist "%PROJECT_ROOT%\app\main.py" (
    call :log "   [ERRO] Arquivo ausente: app\main.py"
    goto :fim_erro
)
if not exist "%PROJECT_ROOT%\frontend\package.json" (
    call :log "   [ERRO] Arquivo ausente: frontend\package.json"
    goto :fim_erro
)
call :log "   [OK] Arquivos do projeto verificados"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 2/8 — Habilitar Features do Windows (3 features obrigatorias para WSL2)
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 2/8] Habilitar Features do Windows (WSL2)"
echo.

set "NEED_REBOOT=0"

:: [1/3] Microsoft-Windows-Subsystem-Linux
call :log "   [1/3] Feature: Microsoft-Windows-Subsystem-Linux"
set "FEAT_WSL=0"
for /f "delims=" %%s in ('powershell -NoProfile -Command "(Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux).State"') do (
    call :log "         Estado: %%s"
    if /i "%%s"=="Enabled" set "FEAT_WSL=1"
)
if "!FEAT_WSL!"=="0" (
    call :log "         Habilitando (pode levar 1-2 min)..."
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart >> "%LOG_FILE%" 2>&1
    set "DISM_RC=!errorlevel!"
    if !DISM_RC! equ 0 (
        set "NEED_REBOOT=1"
        call :log "         Habilitado com sucesso."
    ) else if !DISM_RC! equ 3010 (
        set "NEED_REBOOT=1"
        call :log "         Habilitado com sucesso (codigo 3010 = reboot necessario)."
    ) else (
        call :log "         [ERRO] Falha ao habilitar Microsoft-Windows-Subsystem-Linux (codigo: !DISM_RC!)"
        goto :fim_erro
    )
) else (
    call :log "         [OK] Ja habilitado"
)

:: [2/3] VirtualMachinePlatform
call :log "   [2/3] Feature: VirtualMachinePlatform"
set "FEAT_VMP=0"
for /f "delims=" %%s in ('powershell -NoProfile -Command "(Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform).State"') do (
    call :log "         Estado: %%s"
    if /i "%%s"=="Enabled" set "FEAT_VMP=1"
)
if "!FEAT_VMP!"=="0" (
    call :log "         Habilitando..."
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart >> "%LOG_FILE%" 2>&1
    set "DISM_RC=!errorlevel!"
    if !DISM_RC! equ 0 (
        set "NEED_REBOOT=1"
        call :log "         Habilitado com sucesso."
    ) else if !DISM_RC! equ 3010 (
        set "NEED_REBOOT=1"
        call :log "         Habilitado com sucesso (codigo 3010 = reboot necessario)."
    ) else (
        call :log "         [ERRO] Falha ao habilitar VirtualMachinePlatform (codigo: !DISM_RC!)"
        goto :fim_erro
    )
) else (
    call :log "         [OK] Ja habilitado"
)

:: [3/3] HypervisorPlatform (Windows Hypervisor Platform — obrigatorio para WSL2 criar VMs)
:: Sem esta feature: erro HCS_E_HYPERV_NOT_INSTALLED ao instalar distro
call :log "   [3/3] Feature: HypervisorPlatform (Windows Hypervisor Platform)"
set "FEAT_HVP=0"
for /f "delims=" %%s in ('powershell -NoProfile -Command "(Get-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform).State"') do (
    call :log "         Estado: %%s"
    if /i "%%s"=="Enabled" set "FEAT_HVP=1"
)
if "!FEAT_HVP!"=="0" (
    call :log "         Habilitando (corrige: HCS_E_HYPERV_NOT_INSTALLED)..."
    dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart >> "%LOG_FILE%" 2>&1
    set "DISM_RC=!errorlevel!"
    if !DISM_RC! equ 0 (
        set "NEED_REBOOT=1"
        call :log "         Habilitado com sucesso."
    ) else if !DISM_RC! equ 3010 (
        set "NEED_REBOOT=1"
        call :log "         Habilitado com sucesso (codigo 3010 = reboot necessario)."
    ) else (
        call :log "         [AVISO] Falha ao habilitar HypervisorPlatform (codigo: !DISM_RC!)."
        call :log "         Se o servidor estiver em VM, habilite nested virtualization no host."
        call :log "         Ref: https://aka.ms/enablevirtualization"
    )
) else (
    call :log "         [OK] Ja habilitado"
)

if "!NEED_REBOOT!"=="1" (
    call :log ""
    echo    ╔══════════════════════════════════════════════════════════════╗
    echo    ║  REBOOT NECESSARIO (UNICA VEZ)                              ║
    echo    ║  3 features WSL2 foram habilitadas.                          ║
    echo    ║  Reinicie e execute este script novamente.                   ║
    echo    ╚══════════════════════════════════════════════════════════════╝
    echo.
    echo    Deseja reiniciar agora? (S/N)
    set /p "REBOOT_CHOICE="
    if /i "!REBOOT_CHOICE!"=="S" (
        shutdown /r /t 10 /c "Reboot para WSL2 — Dinamica Budget"
        call :log "   Reiniciando em 10 segundos..."
    )
    goto :fim_ok
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 3/8 — Instalar WSL2 + Ubuntu
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 3/8] Instalar WSL2 + Ubuntu 22.04"
echo.

:: Verificar se WSL2 + Ubuntu ja estao funcionais
set "WSL_READY=0"

:: Passo 1: Verificar se kernel WSL2 esta inicializado (com timeout para evitar travamento)
call :log "   Verificando kernel WSL2 (timeout 20s)..."
set "WSL_KERNEL_STATUS=UNKNOWN"
for /f "delims=" %%r in ('powershell -NoProfile -Command "try{$p=Start-Process wsl -ArgumentList '--status' -PassThru -WindowStyle Hidden;if($p.WaitForExit(20000)){if($p.ExitCode -eq 0){'OK'}else{'NEEDS_SETUP'}}else{try{$p.Kill()}catch{};'TIMEOUT'}}catch{'ERROR'}"') do set "WSL_KERNEL_STATUS=%%r"
call :log "   Kernel WSL2: !WSL_KERNEL_STATUS!"

if /i "!WSL_KERNEL_STATUS!"=="TIMEOUT" (
    call :log "   WSL2 nao respondeu — kernel nao inicializado."
    call :log "   Atualizando kernel WSL2 (wsl --update)..."
    wsl --update >> "%LOG_FILE%" 2>&1
    if !errorlevel! neq 0 (
        call :log "   [AVISO] Possivel falha ao atualizar kernel. Tentando prosseguir..."
    ) else (
        call :log "   [OK] Kernel WSL2 atualizado"
    )
)
if /i "!WSL_KERNEL_STATUS!"=="ERROR" (
    call :log "   wsl nao encontrado ou erro. Instalando WSL2..."
    wsl --update >> "%LOG_FILE%" 2>&1
    if !errorlevel! neq 0 (
        call :log "   [ERRO] Falha ao instalar WSL2. Verifique a conexao de internet."
        goto :fim_erro
    )
    call :log "   [OK] WSL2 instalado"
)
if /i "!WSL_KERNEL_STATUS!"=="NEEDS_SETUP" (
    call :log "   WSL2 presente mas precisa de atualizacao..."
    wsl --install --distribution Ubuntu-22.04 >> "%LOG_FILE%" 2>&1
    call :log "   [OK] WSL2 atualizado"
)

:: Passo 2: Verificar se Ubuntu esta instalado (com timeout)
call :log "   Verificando se Ubuntu esta instalado..."
set "UBUNTU_STATUS=UNKNOWN"
for /f "delims=" %%r in ('powershell -NoProfile -Command "try{$psi=New-Object System.Diagnostics.ProcessStartInfo;$psi.FileName='wsl';$psi.Arguments='-l -q';$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$p=[System.Diagnostics.Process]::Start($psi);$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();if($p.WaitForExit(15000)){[void][Threading.Tasks.Task]::WaitAll($ot,$et);if($ot.Result -match 'Ubuntu'){'FOUND'}else{'NOT_FOUND'}}else{try{$p.Kill()}catch{};'TIMEOUT'}}catch{'ERROR'}"') do set "UBUNTU_STATUS=%%r"
call :log "   Ubuntu: !UBUNTU_STATUS!"

if /i "!UBUNTU_STATUS!"=="FOUND" (
    :: Testar se Ubuntu responde (com timeout de 30s)
    set "UBUNTU_EXEC=UNKNOWN"
    for /f "delims=" %%r in ('powershell -NoProfile -Command "try{$psi=New-Object System.Diagnostics.ProcessStartInfo;$psi.FileName='wsl';$psi.Arguments='-d %WSL_DISTRO% -- echo WSL2_OK';$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$p=[System.Diagnostics.Process]::Start($psi);$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();if($p.WaitForExit(30000)){[void][Threading.Tasks.Task]::WaitAll($ot,$et);if($ot.Result -match 'WSL2_OK'){'OK'}else{'FAIL'}}else{try{$p.Kill()}catch{};'TIMEOUT'}}catch{'ERROR'}"') do set "UBUNTU_EXEC=%%r"
    call :log "   Ubuntu exec: !UBUNTU_EXEC!"
    if /i "!UBUNTU_EXEC!"=="OK" (
        call :log "   [OK] WSL2 com Ubuntu ja instalado e funcional"
        set "WSL_READY=1"
    )
)

if "!WSL_READY!"=="0" (
    call :log "   Atualizando kernel WSL2 antes de instalar distro (Server 2022)..."
    wsl --update >> "%LOG_FILE%" 2>&1

    call :log "   Instalando WSL2 + Ubuntu (pode levar 5-10 min)..."
    call :log "   Comando: wsl --install -d Ubuntu-22.04 --web-download --no-launch"

    :: Server 2022 — usar --web-download (Microsoft Store nao disponivel)
    wsl --install -d Ubuntu-22.04 --web-download --no-launch >> "%LOG_FILE%" 2>&1

    :: Definir WSL2 como padrao
    wsl --set-default-version 2 >> "%LOG_FILE%" 2>&1

    :: Verificar instalacao (com timeout)
    set "INSTALL_VERIFY=UNKNOWN"
    for /f "delims=" %%r in ('powershell -NoProfile -Command "try{$psi=New-Object System.Diagnostics.ProcessStartInfo;$psi.FileName='wsl';$psi.Arguments='-l -q';$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$p=[System.Diagnostics.Process]::Start($psi);$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();if($p.WaitForExit(15000)){[void][Threading.Tasks.Task]::WaitAll($ot,$et);if($ot.Result -match 'Ubuntu'){'OK'}else{'NOT_FOUND'}}else{try{$p.Kill()}catch{};'TIMEOUT'}}catch{'ERROR'}"') do set "INSTALL_VERIFY=%%r"

    if /i "!INSTALL_VERIFY!"=="OK" (
        call :log "   [OK] Ubuntu 22.04 instalado"
    ) else (
        call :log "   [AVISO] Ubuntu pode precisar de reboot ou inicializacao manual."
        call :log "   Resultado: !INSTALL_VERIFY!"
        call :log "   Execute: wsl -d Ubuntu-22.04"
        call :log "   Crie usuario e senha, depois execute este script novamente."
        goto :fim_erro
    )
)

:: Verificar se Ubuntu tem usuario configurado (com timeout)
set "WSL_USER="
for /f "delims=" %%u in ('powershell -NoProfile -Command "try{$psi=New-Object System.Diagnostics.ProcessStartInfo;$psi.FileName='wsl';$psi.Arguments='-d %WSL_DISTRO% -- whoami';$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$p=[System.Diagnostics.Process]::Start($psi);$ot=$p.StandardOutput.ReadToEndAsync();$et=$p.StandardError.ReadToEndAsync();if($p.WaitForExit(15000)){[void][Threading.Tasks.Task]::WaitAll($ot,$et);$r=$ot.Result.Trim();if($r){$r}else{''}}else{try{$p.Kill()}catch{};''}}"') do set "WSL_USER=%%u"
if "!WSL_USER!"=="" (
    call :log "   [AVISO] Ubuntu precisa de configuracao inicial."
    call :log "   Abrindo Ubuntu para criar usuario..."
    call :log "   Crie usuario e senha, feche, e execute este script novamente."
    wsl -d %WSL_DISTRO%
    goto :fim_ok
)
if /i "!WSL_USER!"=="root" (
    call :log "   [AVISO] Ubuntu rodando como root. Criando usuario 'deploy'..."
    wsl -d %WSL_DISTRO% -- bash -c "if ! id deploy >/dev/null 2>&1; then useradd -m -s /bin/bash deploy; echo 'deploy:Dinamica2024!' | chpasswd; usermod -aG sudo deploy; echo 'deploy ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/deploy; fi" >> "%LOG_FILE%" 2>&1
    :: Definir deploy como usuario padrao (preserva [boot] se existir)
    wsl -d %WSL_DISTRO% -- bash -c "if grep -q '^\[user\]' /etc/wsl.conf 2>/dev/null; then sed -i 's/^default=.*/default=deploy/' /etc/wsl.conf; else echo -e '\n[user]\ndefault=deploy' >> /etc/wsl.conf; fi" >> "%LOG_FILE%" 2>&1
    call :log "   [OK] Usuario 'deploy' criado. Reiniciando WSL..."
    wsl --terminate %WSL_DISTRO% >nul 2>&1
    timeout /t 3 /nobreak >nul
    for /f "delims=" %%u in ('wsl -d %WSL_DISTRO% -- whoami 2^>nul') do set "WSL_USER=%%u"
)
call :log "   [OK] WSL2 usuario: !WSL_USER!"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 4/8 — Instalar Docker Engine no WSL2
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 4/8] Instalar Docker Engine no WSL2"
echo.

:: Verificar se Docker ja funciona dentro do WSL
set "DOCKER_OK=0"
wsl -d %WSL_DISTRO% -- docker --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "delims=" %%v in ('wsl -d %WSL_DISTRO% -- docker --version 2^>nul') do call :log "   Docker: %%v"
    wsl -d %WSL_DISTRO% -- docker info >nul 2>&1
    if !errorlevel! equ 0 (
        call :log "   [OK] Docker Engine ja instalado e rodando"
        set "DOCKER_OK=1"
    ) else (
        call :log "   Docker instalado mas daemon nao responde. Iniciando..."
        wsl -d %WSL_DISTRO% -- sudo service docker start >> "%LOG_FILE%" 2>&1
        timeout /t 3 /nobreak >nul
        wsl -d %WSL_DISTRO% -- docker info >nul 2>&1
        if !errorlevel! equ 0 (
            call :log "   [OK] Docker daemon iniciado"
            set "DOCKER_OK=1"
        )
    )
)

if "!DOCKER_OK!"=="0" (
    call :log "   Instalando Docker Engine no Ubuntu (3-5 min)..."
    call :log "   Fonte: repositorio oficial Docker (https://download.docker.com)"

    :: Script de instalacao Docker oficial (unificado)
    wsl -d %WSL_DISTRO% -- bash -c "
        set -e
        export DEBIAN_FRONTEND=noninteractive

        echo '>>> Removendo pacotes conflitantes...'
        sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

        echo '>>> Instalando dependencias...'
        sudo apt-get update -q
        sudo apt-get install -y -q ca-certificates curl gnupg lsb-release

        echo '>>> Adicionando chave GPG oficial do Docker...'
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
        sudo chmod a+r /etc/apt/keyrings/docker.gpg

        echo '>>> Adicionando repositorio Docker...'
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        echo '>>> Instalando Docker Engine + Compose plugin...'
        sudo apt-get update -q
        sudo apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        echo '>>> Adicionando usuario ao grupo docker...'
        sudo usermod -aG docker \$USER 2>/dev/null || true

        echo '>>> Habilitando systemd para Docker...'
        if grep -q '^\[boot\]' /etc/wsl.conf 2>/dev/null; then
            if ! grep -q 'systemd=true' /etc/wsl.conf; then
                sudo sed -i '/^\[boot\]/a systemd=true' /etc/wsl.conf
            fi
        else
            sudo bash -c 'echo -e \"\n[boot]\nsystemd=true\" >> /etc/wsl.conf'
        fi

        echo '>>> Iniciando Docker...'
        sudo service docker start 2>/dev/null || true
    " >> "%LOG_FILE%" 2>&1

    if !errorlevel! neq 0 (
        call :log "   [ERRO] Falha na instalacao do Docker."
        call :log "   Verifique o log: %LOG_FILE%"
        goto :fim_erro
    )

    :: Reiniciar WSL para aplicar systemd
    call :log "   Reiniciando WSL para aplicar systemd..."
    wsl --terminate %WSL_DISTRO% >nul 2>&1
    timeout /t 5 /nobreak >nul

    :: Iniciar Docker
    wsl -d %WSL_DISTRO% -- sudo service docker start >> "%LOG_FILE%" 2>&1
    timeout /t 3 /nobreak >nul

    :: Verificar
    wsl -d %WSL_DISTRO% -- docker info >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%v in ('wsl -d %WSL_DISTRO% -- docker --version 2^>nul') do call :log "   Docker: %%v"
        for /f "delims=" %%v in ('wsl -d %WSL_DISTRO% -- docker compose version 2^>nul') do call :log "   Compose: %%v"
        call :log "   [OK] Docker Engine instalado e funcionando"
    ) else (
        call :log "   [ERRO] Docker instalado mas nao responde."
        call :log "   Tente manualmente: wsl -d %WSL_DISTRO% -- sudo service docker start"
        goto :fim_erro
    )
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 5/8 — Sincronizar Projeto para WSL2
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 5/8] Sincronizar projeto para WSL2"
echo.

:: Converter caminho Windows → WSL
set "WIN_PATH=%PROJECT_ROOT%"
set "DRIVE_LETTER=%WIN_PATH:~0,1%"
set "REST_PATH=%WIN_PATH:~2%"
:: Converter \ para /
set "REST_PATH=%REST_PATH:\=/%"
:: Converter drive letter para minusculo via PowerShell
for /f "delims=" %%l in ('powershell -NoProfile -Command "'%DRIVE_LETTER%'.ToLower()"') do set "DRIVE_LOWER=%%l"
set "WSL_SOURCE=/mnt/%DRIVE_LOWER%%REST_PATH%"

call :log "   Origem (Windows): %PROJECT_ROOT%"
call :log "   Origem (WSL):     !WSL_SOURCE!"
call :log "   Destino (WSL):    %WSL_APP_DIR%"

:: Criar diretorio + sincronizar (rsync para performance e preservar permissoes)
wsl -d %WSL_DISTRO% -- bash -c "
    sudo mkdir -p %WSL_APP_DIR%
    sudo chown -R \$USER:\$USER %WSL_APP_DIR%

    # Instalar rsync se nao existir
    which rsync >/dev/null 2>&1 || sudo apt-get install -y rsync -q

    rsync -a --delete \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='.venv' \
        --exclude='venv' \
        --exclude='.env' \
        --exclude='logs/' \
        --exclude='output/' \
        --exclude='*.pyc' \
        '!WSL_SOURCE!/' '%WSL_APP_DIR%/'
    echo SYNC_OK
" >> "%LOG_FILE%" 2>&1

:: Verificar se sync foi OK
wsl -d %WSL_DISTRO% -- test -f %WSL_APP_DIR%/docker-compose.yml
if !errorlevel! equ 0 (
    call :log "   [OK] Projeto sincronizado"
) else (
    call :log "   [ERRO] Falha na sincronizacao. Verificar log."
    goto :fim_erro
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 6/8 — Gerar .env de Producao
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 6/8] Gerar .env de producao"
echo.

:: Verificar se .env ja existe no destino
set "ENV_EXISTS=0"
wsl -d %WSL_DISTRO% -- test -f %WSL_APP_DIR%/.env
if !errorlevel! equ 0 (
    call :log "   .env ja existe em %WSL_APP_DIR%/.env, mantendo."
    set "ENV_EXISTS=1"
)

if "!ENV_EXISTS!"=="0" (
    :: Verificar se existe .env local na raiz Windows para copiar
    if exist "%PROJECT_ROOT%\.env" (
        call :log "   Copiando .env do Windows para WSL..."
        wsl -d %WSL_DISTRO% -- bash -c "cp '!WSL_SOURCE!/.env' '%WSL_APP_DIR%/.env'"
        call :log "   [OK] .env copiado de %PROJECT_ROOT%\.env"
    ) else (
        call :log "   Gerando .env a partir de .env.example..."

        :: Gerar SECRET_KEY (64 hex = 32 bytes)
        set "SECRET_KEY="
        for /f "delims=" %%k in ('powershell -NoProfile -Command "[System.BitConverter]::ToString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).Replace('-','').ToLower()"') do set "SECRET_KEY=%%k"

        if "!SECRET_KEY!"=="" (
            call :log "   [ERRO] Falha ao gerar SECRET_KEY."
            goto :fim_erro
        )

        :: Copiar .env.example e substituir valores
        wsl -d %WSL_DISTRO% -- bash -c "
            cp '%WSL_APP_DIR%/.env.example' '%WSL_APP_DIR%/.env'
            sed -i 's|CHANGE_ME_use_secrets_token_hex_32|!SECRET_KEY!|g' '%WSL_APP_DIR%/.env'
            sed -i 's|@localhost:5432|@db:5432|g' '%WSL_APP_DIR%/.env'
        " >> "%LOG_FILE%" 2>&1

        call :log "   [OK] .env criado (SECRET_KEY gerada, DATABASE_URL apontando para db:5432)"
        call :log "   [AVISO] Configure ROOT_USER_EMAIL e ROOT_USER_PASSWORD no .env antes do 1o uso!"
    )
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 7/8 — Docker Compose: Build + Deploy
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 7/8] Docker Compose: Build + Deploy"
echo.

:: [1/4] Parar containers anteriores
call :log "   [1/4] Parando containers anteriores..."
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose down --remove-orphans 2>/dev/null || true" >> "%LOG_FILE%" 2>&1
call :log "         OK"

:: [2/4] Pull imagem do banco (pgvector)
call :log "   [2/4] Baixando imagem PostgreSQL (pgvector/pgvector:pg16)..."
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose pull db" >> "%LOG_FILE%" 2>&1
call :log "         OK"

:: [3/4] Build das imagens
call :log "   [3/4] Build das imagens (Frontend + Backend)..."
call :log "         Pode levar 3-10 min na primeira vez..."
echo.
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose build --no-cache 2>&1"
if !errorlevel! neq 0 (
    call :log "   [ERRO] Build falhou. Verifique o log acima."
    call :log "   Diagnostico: docker compose logs"
    goto :fim_erro
)
call :log "   [OK] Build concluido"
echo.

:: [4/4] Iniciar servicos
call :log "   [4/4] Iniciando servicos (DB → Migrations → API)..."
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose up -d 2>&1"
echo.

:: ── Monitorar banco ──────────────────────────────────────────────────────────
call :log "   Aguardando banco de dados..."
set /a "WAITED=0"
:loop_db
if !WAITED! geq 90 (
    call :log "   [ERRO] Banco nao ficou ready em 90s"
    wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose logs db" >> "%LOG_FILE%" 2>&1
    goto :fim_erro
)
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose exec -T db pg_isready -U postgres" >nul 2>&1
if !errorlevel! equ 0 (
    call :log "   [OK] Banco de dados pronto"
    goto :db_ok
)
timeout /t 3 /nobreak >nul
set /a "WAITED+=3"
goto :loop_db
:db_ok
echo.

:: ── Monitorar migrations ─────────────────────────────────────────────────────
call :log "   Aguardando migrations (alembic upgrade head)..."
set /a "WAITED=0"
:loop_mig
if !WAITED! geq 120 (
    call :log "   [ERRO] Migrations nao completaram em 120s"
    wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose logs migrations" >> "%LOG_FILE%" 2>&1
    goto :fim_erro
)

:: Verificar estado do container de migrations
set "MIG_STATUS="
for /f "delims=" %%s in ('wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -a --format \"{{.State}}\" migrations 2>/dev/null"') do set "MIG_STATUS=%%s"

if /i "!MIG_STATUS!"=="exited" (
    :: Verificar exit code
    set "MIG_EXIT="
    for /f "delims=" %%e in ('wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -a --format \"{{.ExitCode}}\" migrations 2>/dev/null"') do set "MIG_EXIT=%%e"
    if "!MIG_EXIT!"=="0" (
        call :log "   [OK] Migrations executadas com sucesso"
        goto :mig_ok
    ) else (
        call :log "   [ERRO] Migrations falharam (exit code: !MIG_EXIT!)"
        wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose logs migrations" >> "%LOG_FILE%" 2>&1
        goto :fim_erro
    )
)

timeout /t 3 /nobreak >nul
set /a "WAITED+=3"
goto :loop_mig
:mig_ok
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 8/8 — Health Check + Firewall + Info
:: ══════════════════════════════════════════════════════════════════════════════
call :log "[ETAPA 8/8] Health Check + Firewall + Informacoes"
echo.

:: ── Health Check ─────────────────────────────────────────────────────────────
call :log "   Aguardando API responder (modelo ML pode levar 30-60s)..."
set /a "WAITED=0"
set /a "MAX_WAIT=180"

:loop_health
if !WAITED! geq !MAX_WAIT! goto :health_done

:: Usar curl via WSL (mais confiavel que PowerShell para chamadas internas)
wsl -d %WSL_DISTRO% -- bash -c "curl -sf http://localhost:!API_PORT!/health >/dev/null 2>&1"
if !errorlevel! equ 0 (
    call :log "   [OK] API respondendo! (HTTP 200)"
    set "API_OK=1"
    goto :health_done
)

timeout /t 5 /nobreak >nul
set /a "WAITED+=5"
if !WAITED! leq !MAX_WAIT! call :log "   Aguardando API... (!WAITED!/!MAX_WAIT!s)"
goto :loop_health

:health_done
echo.

:: ── Firewall ─────────────────────────────────────────────────────────────────
call :log "   Configurando firewall para acesso na rede..."
netsh advfirewall firewall delete rule name="Dinamica Budget API" >nul 2>&1
netsh advfirewall firewall add rule name="Dinamica Budget API" dir=in action=allow protocol=tcp localport=!API_PORT! >nul 2>&1
netsh advfirewall firewall delete rule name="Dinamica Budget DB" >nul 2>&1
netsh advfirewall firewall add rule name="Dinamica Budget DB" dir=in action=allow protocol=tcp localport=!DB_PORT! >nul 2>&1
call :log "   [OK] Portas !API_PORT! (API) e !DB_PORT! (DB) liberadas no firewall"

:: ── Port forwarding do Windows para WSL ──────────────────────────────────────
call :log "   Configurando port forwarding Windows → WSL2..."
:: Obter IP do WSL
set "WSL_IP="
for /f "delims=" %%i in ('wsl -d %WSL_DISTRO% -- hostname -I 2^>nul') do (
    for /f "tokens=1" %%j in ("%%i") do set "WSL_IP=%%j"
)
if "!WSL_IP!" neq "" (
    netsh interface portproxy delete v4tov4 listenport=!API_PORT! listenaddress=0.0.0.0 >nul 2>&1
    netsh interface portproxy add v4tov4 listenport=!API_PORT! listenaddress=0.0.0.0 connectport=!API_PORT! connectaddress=!WSL_IP! >nul 2>&1
    netsh interface portproxy delete v4tov4 listenport=!DB_PORT! listenaddress=0.0.0.0 >nul 2>&1
    netsh interface portproxy add v4tov4 listenport=!DB_PORT! listenaddress=0.0.0.0 connectport=!DB_PORT! connectaddress=!WSL_IP! >nul 2>&1
    call :log "   [OK] Port forwarding: 0.0.0.0:!API_PORT! → !WSL_IP!:!API_PORT!"
    call :log "   [OK] Port forwarding: 0.0.0.0:!DB_PORT! → !WSL_IP!:!DB_PORT!"
) else (
    call :log "   [AVISO] Nao foi possivel obter IP do WSL. Port forwarding nao configurado."
    call :log "   Acesso apenas via localhost."
)
echo.

:: ── Criar Task Scheduler para manter WSL rodando no boot ─────────────────────
call :log "   Configurando auto-start WSL + Docker no boot..."
schtasks /delete /tn "DinamicaBudget-WSL-Autostart" /f >nul 2>&1
schtasks /create /tn "DinamicaBudget-WSL-Autostart" ^
    /tr "wsl -d %WSL_DISTRO% -- sudo service docker start" ^
    /sc onstart /ru SYSTEM /rl HIGHEST /f >nul 2>&1
if !errorlevel! equ 0 (
    call :log "   [OK] Task Scheduler: WSL + Docker iniciam automaticamente no boot"
) else (
    call :log "   [AVISO] Nao foi possivel criar tarefa agendada. Docker pode nao iniciar automaticamente."
)

:: ── Criar Task Scheduler para port forwarding no boot ────────────────────────
schtasks /delete /tn "DinamicaBudget-PortForward" /f >nul 2>&1
set "PF_CMD=powershell -NoProfile -Command \"$ip=(wsl -d %WSL_DISTRO% -- hostname -I).Trim().Split(' ')[0]; netsh interface portproxy add v4tov4 listenport=%API_PORT% listenaddress=0.0.0.0 connectport=%API_PORT% connectaddress=$ip; netsh interface portproxy add v4tov4 listenport=%DB_PORT% listenaddress=0.0.0.0 connectport=%DB_PORT% connectaddress=$ip\""
schtasks /create /tn "DinamicaBudget-PortForward" ^
    /tr "%PF_CMD%" ^
    /sc onstart /delay 0000:30 /ru SYSTEM /rl HIGHEST /f >nul 2>&1
if !errorlevel! equ 0 (
    call :log "   [OK] Task Scheduler: Port forwarding recriado automaticamente no boot"
)
echo.

:: ── Status dos containers ─────────────────────────────────────────────────────
call :log "   Status dos containers:"
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -a" 2>&1
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: GERAR ARQUIVO DE INFORMACOES
:: ══════════════════════════════════════════════════════════════════════════════
(
echo ============================================================
echo   DINAMICA BUDGET — Informacoes de Deploy
echo ============================================================
echo.
echo   Data do Deploy   : !SCRIPT_START_TIME!
echo   Servidor         : %COMPUTERNAME%
echo   IP do Servidor   : !SERVER_IP!
echo   Abordagem        : WSL2 + Docker Engine
echo   SO               : Windows Server 2022 (build !WIN_BUILD!^)
echo   WSL Distro       : %WSL_DISTRO%
echo   WSL Usuario      : !WSL_USER!
echo   Projeto (WSL^)    : %WSL_APP_DIR%
echo.
echo ============================================================
echo   URLs DE ACESSO (INTRANET^)
echo ============================================================
echo.
echo   Aplicacao (Frontend + API^):
echo     http://!SERVER_IP!:!API_PORT!
echo     http://localhost:!API_PORT!
echo.
echo   Documentacao da API (Swagger^):
echo     http://!SERVER_IP!:!API_PORT!/docs
echo.
echo   API ReDoc:
echo     http://!SERVER_IP!:!API_PORT!/redoc
echo.
echo   Health Check:
echo     http://!SERVER_IP!:!API_PORT!/health
echo.
echo   Banco de Dados (PostgreSQL 16 + pgvector^):
echo     Host: !SERVER_IP!
echo     Porta: !DB_PORT!
echo     Database: dinamica_budget
echo     Usuario: postgres
echo.
echo ============================================================
echo   COMANDOS UTEIS
echo ============================================================
echo.
echo   ^(Todos os comandos Docker devem ser executados DENTRO do WSL^)
echo.
echo   Entrar no WSL:
echo     wsl -d %WSL_DISTRO%
echo.
echo   Ver status:
echo     cd %WSL_APP_DIR% ^&^& docker compose ps
echo.
echo   Ver logs:
echo     cd %WSL_APP_DIR% ^&^& docker compose logs -f api
echo.
echo   Reiniciar API:
echo     cd %WSL_APP_DIR% ^&^& docker compose restart api
echo.
echo   Parar tudo:
echo     cd %WSL_APP_DIR% ^&^& docker compose down
echo.
echo   Re-deploy completo:
echo     deploy-dinamica.bat
echo.
echo   Remover tudo:
echo     remove-dinamica.bat
echo.
echo ============================================================
echo   LOGS
echo ============================================================
echo.
echo   Log deste deploy: %LOG_FILE%
echo   Todos os logs:    %PROJECT_ROOT%\logs\
echo   Docker logs:      docker compose logs [servico]
echo.
echo ============================================================
) > "%INFO_FILE%"
call :log "   Informacoes salvas em: %INFO_FILE%"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: RESUMO FINAL
:: ══════════════════════════════════════════════════════════════════════════════
if "!API_OK!"=="1" (
    call :log ""
    :: Mostrar health response
    echo    Resposta do /health:
    wsl -d %WSL_DISTRO% -- bash -c "curl -s http://localhost:!API_PORT!/health 2>/dev/null"
    echo.
    echo.
    echo ============================================================
    echo   DEPLOY CONCLUIDO COM SUCESSO!
    echo ============================================================
    echo.
    echo   Aplicacao : http://!SERVER_IP!:!API_PORT!
    echo   API Docs  : http://!SERVER_IP!:!API_PORT!/docs
    echo   Health    : http://!SERVER_IP!:!API_PORT!/health
    echo   Banco     : !SERVER_IP!:!DB_PORT!
    echo.
    echo   Log       : %LOG_FILE%
    echo   Info      : %INFO_FILE%
    echo.
    call :log "DEPLOY CONCLUIDO COM SUCESSO"
) else (
    echo ============================================================
    echo   DEPLOY CONCLUIDO (API pode estar inicializando)
    echo ============================================================
    echo.
    echo   API nao respondeu em !MAX_WAIT!s.
    echo   Pode estar carregando o modelo ML (~60s na 1a vez).
    echo.
    echo   Verifique com:
    echo     wsl -d %WSL_DISTRO%
    echo     cd %WSL_APP_DIR% ^&^& docker compose logs -f api
    echo.
    echo   Log: %LOG_FILE%
    echo.
    call :log "DEPLOY CONCLUIDO - API pendente de inicializacao"
)

goto :fim_ok

:: ══════════════════════════════════════════════════════════════════════════════
:fim_erro
echo.
echo ============================================================
echo   OCORRERAM ERROS — Verifique as mensagens acima
echo ============================================================
echo.
echo   Log completo: %LOG_FILE%
echo.
echo   Diagnostico rapido:
echo     wsl -d %WSL_DISTRO%
echo     cd %WSL_APP_DIR% ^&^& docker compose logs
echo     cd %WSL_APP_DIR% ^&^& docker compose ps -a
echo.
call :log "DEPLOY FALHOU — Verifique o log"
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 1

:fim_ok
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0
