@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Dinamica Budget — Deploy Inteligente

:: ══════════════════════════════════════════════════════════════════════════════
::  DINAMICA BUDGET — Deploy Inteligente (Backend + Frontend em Docker)
::  Um clique → ambiente limpo, build, migrations, API + Frontend rodando.
::
::  Fluxo: prereqs → .env → down → build → up (compose orquestra) → health
:: ══════════════════════════════════════════════════════════════════════════════

echo.
echo ============================================================
echo   DINAMICA BUDGET — Deploy Automatico
echo ============================================================
echo.

:: Determinar raiz do projeto (diretorio onde esta o .bat)
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

echo   Inicio   : %date% %time%
echo   Diretorio: %PROJECT_ROOT%
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 1/6 — Verificar pre-requisitos
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 1/6 — Verificar pre-requisitos
echo.

docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo    [ERRO] Docker nao encontrado. Instale: https://docs.docker.com/desktop/install/windows-install/
    goto :fim_erro
)
for /f "delims=" %%v in ('docker --version 2^>nul') do echo    Docker: %%v

:: Docker Compose (plugin ou standalone)
set "COMPOSE_CMD="
docker compose version >nul 2>&1
if !errorlevel! equ 0 (
    set "COMPOSE_CMD=docker compose"
) else (
    docker-compose --version >nul 2>&1
    if !errorlevel! equ 0 set "COMPOSE_CMD=docker-compose"
)
if "!COMPOSE_CMD!"=="" (
    echo    [ERRO] Docker Compose nao encontrado.
    goto :fim_erro
)

docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo    [ERRO] Docker daemon nao esta rodando. Inicie o Docker Desktop.
    goto :fim_erro
)
echo    Docker daemon: OK

for %%f in (Dockerfile docker-compose.yml requirements.txt alembic.ini) do (
    if not exist "%%f" (
        echo    [ERRO] Arquivo nao encontrado: %%f
        goto :fim_erro
    )
)
echo    Arquivos essenciais: OK
echo    [OK] Pre-requisitos verificados
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 2/6 — Gerar .env (se nao existir)
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 2/6 — Configurar ambiente (.env)
echo.

if exist ".env" (
    echo    .env ja existe, mantendo configuracao atual.
) else (
    echo    .env nao encontrado — gerando automaticamente...

    if not exist ".env.example" (
        echo    [ERRO] .env.example nao encontrado.
        goto :fim_erro
    )

    :: Gerar SECRET_KEY segura (64 hex chars = 32 bytes)
    set "SECRET_KEY="
    for /f "delims=" %%k in ('python -c "import secrets; print(secrets.token_hex(32))" 2^>nul') do set "SECRET_KEY=%%k"
    if "!SECRET_KEY!"=="" (
        for /f "delims=" %%k in ('powershell -NoProfile -Command "[System.BitConverter]::ToString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).Replace('-','')" 2^>nul') do set "SECRET_KEY=%%k"
    )
    if "!SECRET_KEY!"=="" (
        echo    [ERRO] Nao foi possivel gerar SECRET_KEY.
        goto :fim_erro
    )

    copy /y ".env.example" ".env" >nul
    powershell -NoProfile -Command "(Get-Content '.env') -replace 'CHANGE_ME_use_secrets_token_hex_32', '!SECRET_KEY!' | Set-Content '.env' -Encoding UTF8"
    echo    SECRET_KEY gerada com sucesso
    echo    [OK] .env criado
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 3/6 — Parar containers anteriores
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 3/6 — Limpar containers anteriores
echo.

echo    Parando containers do projeto...
!COMPOSE_CMD! down --remove-orphans >nul 2>&1
echo    [OK] Containers anteriores removidos (dados do banco preservados)

:: Limpar imagens de build antigas
for /f "delims=" %%i in ('docker images -q "dinamica-budget*" 2^>nul') do (
    docker rmi %%i >nul 2>&1
)
echo    [OK] Imagens antigas removidas
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 4/6 — Build das imagens Docker
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 4/6 — Build das imagens (Frontend + Backend)
echo    Isso pode levar alguns minutos na primeira vez...
echo.

!COMPOSE_CMD! build --no-cache 2>&1
if !errorlevel! neq 0 (
    echo.
    echo    [ERRO] Build falhou. Verifique os erros acima.
    goto :fim_erro
)
echo.
echo    [OK] Build concluido
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 5/6 — Subir tudo (Compose orquestra: DB → Migrations → API)
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 5/6 — Iniciar servicos
echo    Compose gerencia a ordem: DB (healthy) → Migrations → API
echo.

:: Subir tudo de uma vez — compose respeita depends_on/conditions
!COMPOSE_CMD! up -d 2>&1
if !errorlevel! neq 0 (
    echo    [AVISO] Compose retornou erro, verificando estado real...
)

:: ── Monitorar DB ─────────────────────────────────────────────────────────────
echo    [1/3] Aguardando banco de dados...
set /a "WAITED=0"
:loop_db
if !WAITED! geq 60 (
    echo    [ERRO] Timeout aguardando banco de dados (60s)
    !COMPOSE_CMD! logs db 2>&1
    goto :fim_erro
)
for /f "delims=" %%s in ('docker inspect --format "{{.State.Health.Status}}" dinamica-budget-db-1 2^>nul') do set "DB_STATUS=%%s"
if "!DB_STATUS!"=="" (
    :: Tentar nome alternativo
    for /f "delims=" %%c in ('!COMPOSE_CMD! ps -q db 2^>nul') do (
        for /f "delims=" %%s in ('docker inspect --format "{{.State.Health.Status}}" %%c 2^>nul') do set "DB_STATUS=%%s"
    )
)
if "!DB_STATUS!"=="healthy" (
    echo    [OK] Banco de dados pronto
    goto :db_ok
)
timeout /t 3 /nobreak >nul
set /a "WAITED+=3"
if !WAITED! leq 60 echo    Aguardando... (!WAITED!/60s)
goto :loop_db
:db_ok
echo.

:: ── Monitorar Migrations ─────────────────────────────────────────────────────
echo    [2/3] Aguardando migrations...
set /a "WAITED=0"
:loop_mig
if !WAITED! geq 120 (
    echo    [ERRO] Timeout aguardando migrations (120s)
    !COMPOSE_CMD! logs migrations 2>&1
    goto :fim_erro
)

:: Verificar se migration container existe e seu status
set "MIG_STATE="
set "MIG_EXIT_CODE="
for /f "delims=" %%c in ('!COMPOSE_CMD! ps -aq migrations 2^>nul') do (
    for /f "delims=" %%s in ('docker inspect --format "{{.State.Status}}" %%c 2^>nul') do set "MIG_STATE=%%s"
    for /f "delims=" %%e in ('docker inspect --format "{{.State.ExitCode}}" %%c 2^>nul') do set "MIG_EXIT_CODE=%%e"
)

if "!MIG_STATE!"=="exited" (
    if "!MIG_EXIT_CODE!"=="0" (
        echo    [OK] Migrations executadas com sucesso
        goto :mig_ok
    ) else (
        echo    [ERRO] Migrations falharam (exit code: !MIG_EXIT_CODE!)
        echo.
        !COMPOSE_CMD! logs migrations 2>&1
        goto :fim_erro
    )
)

timeout /t 3 /nobreak >nul
set /a "WAITED+=3"
if !WAITED! leq 120 echo    Aguardando... (!WAITED!/120s)
goto :loop_mig
:mig_ok
echo.

:: ── Monitorar API ────────────────────────────────────────────────────────────
echo    [3/3] Aguardando API inicializar...

:: Verificar se API container esta rodando
set /a "API_RETRY=0"
:check_api_running
for /f "delims=" %%c in ('!COMPOSE_CMD! ps -q api 2^>nul') do (
    for /f "delims=" %%s in ('docker inspect --format "{{.State.Status}}" %%c 2^>nul') do set "API_STATE=%%s"
)
if "!API_STATE!" neq "running" (
    if !API_RETRY! geq 10 (
        echo    [AVISO] API container nao esta running (estado: !API_STATE!)
        echo    Tentando iniciar API explicitamente...
        !COMPOSE_CMD! up -d api 2>&1
        timeout /t 5 /nobreak >nul
    ) else (
        set /a "API_RETRY+=1"
        timeout /t 3 /nobreak >nul
        goto :check_api_running
    )
)
echo    API container rodando, aguardando health check...
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 6/6 — Health check da API
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 6/6 — Health check
echo.

set /a "WAITED=0"
set /a "MAX_WAIT=150"
set "API_OK=0"

:loop_health
if !WAITED! geq !MAX_WAIT! goto :health_done

set "HTTP_CODE=0"
curl -s -o nul -w "%%{http_code}" http://localhost:8000/health >"%TEMP%\_dyn_health.txt" 2>nul
if exist "%TEMP%\_dyn_health.txt" (
    set /p HTTP_CODE=<"%TEMP%\_dyn_health.txt"
    del "%TEMP%\_dyn_health.txt" >nul 2>&1
)
if "!HTTP_CODE!"=="0" (
    :: Fallback para PowerShell se curl nao disponivel
    for /f "delims=" %%c in ('powershell -NoProfile -Command "try{(Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 3).StatusCode}catch{0}" 2^>nul') do set "HTTP_CODE=%%c"
)

if "!HTTP_CODE!"=="200" (
    echo    [OK] API respondendo! (HTTP 200)
    set "API_OK=1"
    goto :health_done
)

timeout /t 5 /nobreak >nul
set /a "WAITED+=5"
echo    Aguardando API... (!WAITED!/!MAX_WAIT!s)
goto :loop_health

:health_done
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: RESUMO FINAL
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo    Status dos containers:
!COMPOSE_CMD! ps -a 2>&1
echo.

if "!API_OK!"=="1" (
    echo    Resposta do /health:
    curl -s http://localhost:8000/health 2>nul
    if !errorlevel! neq 0 (
        powershell -NoProfile -Command "try{(Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 5).Content}catch{}" 2>nul
    )
    echo.
    echo.
    echo ============================================================
    echo   DEPLOY CONCLUIDO COM SUCESSO!
    echo ============================================================
    echo.
    echo   Aplicacao : http://localhost:8000
    echo   API Docs  : http://localhost:8000/docs
    echo   Health    : http://localhost:8000/health
    echo   Banco     : localhost:5432
    echo.
    echo   Comandos uteis:
    echo     Ver logs      : docker compose logs -f api
    echo     Parar tudo    : docker compose down
    echo     Reiniciar API : docker compose restart api
    echo     Rebuild       : deploy.bat
    echo.
) else (
    echo ============================================================
    echo   DEPLOY CONCLUIDO (API pode estar inicializando)
    echo ============================================================
    echo.
    echo   API nao respondeu em !MAX_WAIT!s.
    echo   Pode estar carregando o modelo ML (normal na 1a vez).
    echo.
    echo   Verifique com:
    echo     docker compose logs -f api
    echo     curl http://localhost:8000/health
    echo.
)

goto :fim_ok

:: ══════════════════════════════════════════════════════════════════════════════
:fim_erro
echo.
echo ============================================================
echo   OCORRERAM ERROS — Verifique as mensagens acima
echo ============================================================
echo.
echo   Diagnostico:
echo     docker compose logs
echo     docker compose ps -a
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 1

:fim_ok
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0
