@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Dinamica Budget — Remocao Completa

:: ══════════════════════════════════════════════════════════════════════════════
::  DINAMICA BUDGET — Remocao Completa com Backup
::  Windows Server 2022 ^| WSL2 + Docker
::
::  Este script remove TUDO do Dinamica Budget:
::    1. Backup automatico do banco (pg_dump)
::    2. Para e remove containers, imagens, volumes
::    3. Remove port forwarding e regras de firewall
::    4. Remove tarefas agendadas
::    5. (Opcional) Remove distro WSL2
::
::  Logs: %~dp0logs\remove-YYYY-MM-DD_HHMMSS.log
:: ══════════════════════════════════════════════════════════════════════════════

set "WSL_DISTRO=Ubuntu-22.04"
set "WSL_APP_DIR=/opt/dinamica-budget"
set "API_PORT=8000"
set "DB_PORT=5432"

:: Raiz do projeto
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

:: Log
if not exist "%PROJECT_ROOT%\logs" mkdir "%PROJECT_ROOT%\logs"
for /f "delims=" %%d in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HHmmss'"') do set "LOG_TS=%%d"
set "LOG_FILE=%PROJECT_ROOT%\logs\remove-%LOG_TS%.log"

goto :skip_log_func2
:log2
set "LOG_MSG=%~1"
if "!LOG_MSG!"=="" (echo.) else (echo !LOG_MSG!)
>> "%LOG_FILE%" echo [%date% %time%] !LOG_MSG!
goto :eof
:skip_log_func2

echo.
echo ============================================================
echo   DINAMICA BUDGET — Remocao Completa
echo   Windows Server 2022 ^| WSL2 + Docker
echo ============================================================
echo.
echo   ATENCAO: Este script ira:
echo     - Fazer BACKUP do banco de dados
echo     - PARAR todos os containers
echo     - REMOVER containers, imagens e volumes
echo     - REMOVER regras de firewall e port forwarding
echo     - REMOVER tarefas agendadas
echo.
echo   O backup sera salvo em: %PROJECT_ROOT%\backups\
echo.
echo ============================================================
echo.

:: Admin check
net session >nul 2>&1
if !errorlevel! neq 0 (
    call :log2 "[ERRO] Executar como Administrador."
    goto :fim_erro2
)

:: Confirmacao
set /p "CONFIRMA=Deseja continuar com a remocao? (S/N): "
if /i not "!CONFIRMA!"=="S" (
    echo Remocao cancelada.
    goto :fim_ok2
)

call :log2 ""
call :log2 "Inicio da remocao: %date% %time%"
call :log2 "Log: %LOG_FILE%"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 1/6 — Backup do Banco de Dados
:: ══════════════════════════════════════════════════════════════════════════════
call :log2 "[ETAPA 1/6] Backup do Banco de Dados"
echo.

if not exist "%PROJECT_ROOT%\backups" mkdir "%PROJECT_ROOT%\backups"
set "BACKUP_FILE=backups\dinamica_budget_REMOCAO_%LOG_TS%.sql"

:: Verificar se DB container esta rodando
set "DB_RUNNING=0"
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -q db 2>/dev/null" >nul 2>&1
if !errorlevel! equ 0 (
    for /f "delims=" %%c in ('wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -q db 2>/dev/null"') do (
        if "%%c" neq "" set "DB_RUNNING=1"
    )
)

if "!DB_RUNNING!"=="1" (
    call :log2 "   Banco rodando. Executando pg_dump..."
    wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose exec -T db pg_dump -U postgres -d dinamica_budget --clean --if-exists" > "%PROJECT_ROOT%\%BACKUP_FILE%" 2>> "%LOG_FILE%"
    if !errorlevel! equ 0 (
        :: Verificar se arquivo tem conteudo (pelo menos headers do pg_dump)
        for %%f in ("%PROJECT_ROOT%\%BACKUP_FILE%") do set "BKP_SIZE=%%~zf"
        if !BKP_SIZE! gtr 100 (
            call :log2 "   [OK] Backup salvo: %BACKUP_FILE% (!BKP_SIZE! bytes)"
        ) else (
            call :log2 "   [AVISO] Backup pequeno (!BKP_SIZE! bytes) - banco pode estar vazio"
        )
    ) else (
        call :log2 "   [AVISO] pg_dump retornou erro. Backup pode estar incompleto."
    )
) else (
    call :log2 "   [AVISO] Container do banco nao esta rodando. Backup nao realizado."
    call :log2 "   Se o volume 'pgdata' existir, os dados permanecem no Docker."
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 2/6 — Parar e Remover Containers
:: ══════════════════════════════════════════════════════════════════════════════
call :log2 "[ETAPA 2/6] Parar e Remover Containers"
echo.

:: Verificar se WSL + Docker estao disponiveis
wsl -d %WSL_DISTRO% -- docker info >nul 2>&1
if !errorlevel! equ 0 (
    :: Iniciar Docker se necessario
    wsl -d %WSL_DISTRO% -- sudo service docker start >nul 2>&1
    timeout /t 2 /nobreak >nul

    call :log2 "   Parando e removendo containers..."
    wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose down -v --rmi all --remove-orphans 2>&1" >> "%LOG_FILE%" 2>&1

    :: Verificar se parou
    set "CONTAINERS_LEFT="
    for /f "delims=" %%c in ('wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -q 2>/dev/null"') do set "CONTAINERS_LEFT=%%c"
    if "!CONTAINERS_LEFT!"=="" (
        call :log2 "   [OK] Containers removidos"
    ) else (
        call :log2 "   [AVISO] Alguns containers podem ter ficado. Forcando..."
        wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose kill 2>/dev/null; docker compose rm -f 2>/dev/null"
    )

    :: Limpeza geral do Docker
    call :log2 "   Limpando imagens, volumes e cache orfaos..."
    wsl -d %WSL_DISTRO% -- bash -c "docker system prune -af --volumes 2>/dev/null || true" >> "%LOG_FILE%" 2>&1
    call :log2 "   [OK] Cleanup Docker concluido"
) else (
    call :log2 "   [AVISO] WSL/Docker nao disponivel. Pulando remocao de containers."
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 3/6 — Remover Arquivos do Projeto no WSL
:: ══════════════════════════════════════════════════════════════════════════════
call :log2 "[ETAPA 3/6] Remover arquivos do projeto no WSL"
echo.

wsl -d %WSL_DISTRO% -- test -d %WSL_APP_DIR% >nul 2>&1
if !errorlevel! equ 0 (
    wsl -d %WSL_DISTRO% -- bash -c "sudo rm -rf %WSL_APP_DIR%" >> "%LOG_FILE%" 2>&1
    call :log2 "   [OK] %WSL_APP_DIR% removido do WSL"
) else (
    call :log2 "   [OK] %WSL_APP_DIR% ja nao existe"
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 4/6 — Remover Port Forwarding e Firewall
:: ══════════════════════════════════════════════════════════════════════════════
call :log2 "[ETAPA 4/6] Remover port forwarding e regras de firewall"
echo.

:: Port forwarding
netsh interface portproxy delete v4tov4 listenport=!API_PORT! listenaddress=0.0.0.0 >nul 2>&1
call :log2 "   Port forwarding porta !API_PORT! removido"
netsh interface portproxy delete v4tov4 listenport=!DB_PORT! listenaddress=0.0.0.0 >nul 2>&1
call :log2 "   Port forwarding porta !DB_PORT! removido"

:: Regras de firewall
netsh advfirewall firewall delete rule name="Dinamica Budget API" >nul 2>&1
call :log2 "   Regra firewall 'Dinamica Budget API' removida"
netsh advfirewall firewall delete rule name="Dinamica Budget DB" >nul 2>&1
call :log2 "   Regra firewall 'Dinamica Budget DB' removida"

call :log2 "   [OK] Rede limpa"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 5/6 — Remover Tarefas Agendadas
:: ══════════════════════════════════════════════════════════════════════════════
call :log2 "[ETAPA 5/6] Remover tarefas agendadas"
echo.

schtasks /delete /tn "DinamicaBudget-WSL-Autostart" /f >nul 2>&1
call :log2 "   Task 'DinamicaBudget-WSL-Autostart' removida"
schtasks /delete /tn "DinamicaBudget-PortForward" /f >nul 2>&1
call :log2 "   Task 'DinamicaBudget-PortForward' removida"

call :log2 "   [OK] Tarefas agendadas removidas"
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 6/6 — Remover Distro WSL (Opcional)
:: ══════════════════════════════════════════════════════════════════════════════
call :log2 "[ETAPA 6/6] Remover distro WSL2 (Opcional)"
echo.
echo   A distro WSL2 (%WSL_DISTRO%) contem o Docker e ambiente.
echo   Remover libera espaco em disco mas requer reinstalacao completa
echo   no proximo deploy.
echo.
set /p "REMOVE_WSL=Deseja REMOVER a distro WSL2 %WSL_DISTRO%? (S/N): "
if /i "!REMOVE_WSL!"=="S" (
    call :log2 "   Removendo distro %WSL_DISTRO%..."
    wsl --unregister %WSL_DISTRO% >> "%LOG_FILE%" 2>&1
    if !errorlevel! equ 0 (
        call :log2 "   [OK] Distro %WSL_DISTRO% removida"
    ) else (
        call :log2 "   [AVISO] Nao foi possivel remover. Tente: wsl --unregister %WSL_DISTRO%"
    )
) else (
    call :log2 "   Distro WSL2 mantida (Docker e ambiente preservados)"
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: RESUMO
:: ══════════════════════════════════════════════════════════════════════════════
echo ============================================================
echo   REMOCAO CONCLUIDA
echo ============================================================
echo.
if "!DB_RUNNING!"=="1" (
    echo   Backup: %PROJECT_ROOT%\%BACKUP_FILE%
)
echo   Log:    %LOG_FILE%
echo.
echo   O que foi removido:
echo     - Containers, imagens e volumes Docker
echo     - Arquivos do projeto em %WSL_APP_DIR%
echo     - Regras de firewall (portas !API_PORT!, !DB_PORT!)
echo     - Port forwarding WSL2 ↔ Windows
echo     - Tarefas agendadas (auto-start)
if /i "!REMOVE_WSL!"=="S" echo     - Distro WSL2 %WSL_DISTRO%
echo.
echo   PRESERVADO:
echo     - Codigo-fonte em %PROJECT_ROOT%
echo     - Backups em %PROJECT_ROOT%\backups\
echo     - Logs em %PROJECT_ROOT%\logs\
if /i not "!REMOVE_WSL!"=="S" echo     - Distro WSL2 %WSL_DISTRO% (com Docker)
echo.
echo   Para re-instalar: deploy-dinamica.bat
echo.
call :log2 "REMOCAO CONCLUIDA — %date% %time%"

goto :fim_ok2

:fim_erro2
echo.
echo [ERRO] Verifique as mensagens acima.
echo Log: %LOG_FILE%
echo.
pause >nul
exit /b 1

:fim_ok2
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0
