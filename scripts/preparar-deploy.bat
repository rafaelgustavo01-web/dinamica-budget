@echo off
chcp 65001 >nul 2>nul
REM ──────────────────────────────────────────────────────────────────────────
REM preparar-deploy.bat — Instalador inteligente: monta pacote de deploy
REM
REM Uso: duplo-clique ou via terminal:
REM   preparar-deploy.bat
REM   preparar-deploy.bat D:\deploy-package
REM   preparar-deploy.bat D:\deploy-package SKIP_FRONTEND
REM
REM O script detecta pre-requisitos, instala dependencias, e nunca fecha a janela.
REM ──────────────────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion
title Dinamica Budget - Preparar Deploy

REM ── Descobrir raiz do projeto (pai da pasta scripts) ────────────────────────
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%\..") do set "PROJECT_ROOT=%%~fI"

REM ── Parametros ──────────────────────────────────────────────────────────────
set "DEPLOY_DIR=%~1"
if "%DEPLOY_DIR%"=="" set "DEPLOY_DIR=C:\deploy-package"

set "SKIP_FRONTEND="
if /i "%~2"=="SKIP_FRONTEND" set "SKIP_FRONTEND=1"

set "HAS_ERROR=0"

echo.
echo ============================================================
echo   PREPARAR PACOTE DE DEPLOY — Dinamica Budget
echo ============================================================
echo.
echo   Projeto : %PROJECT_ROOT%
echo   Destino : %DEPLOY_DIR%
echo   Data    : %date% %time%
echo.

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 0 — Verificar pre-requisitos
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 0/5 — Verificar pre-requisitos
echo.

REM Node.js
where node >nul 2>nul
if %errorlevel%==0 (
    for /f "tokens=*" %%V in ('node --version 2^>nul') do echo    [OK] Node.js encontrado: %%V
) else (
    echo    [ERRO] Node.js NAO encontrado. Instale em https://nodejs.org
    set "HAS_ERROR=1"
)

REM npm
where npm >nul 2>nul
if %errorlevel%==0 (
    for /f "tokens=*" %%V in ('npm --version 2^>nul') do echo    [OK] npm encontrado: v%%V
) else (
    echo    [ERRO] npm NAO encontrado.
    set "HAS_ERROR=1"
)

REM Python
set "PYTHON_CMD="
where python >nul 2>nul && set "PYTHON_CMD=python"
if "%PYTHON_CMD%"=="" ( where python3 >nul 2>nul && set "PYTHON_CMD=python3" )
if "%PYTHON_CMD%"=="" ( where py >nul 2>nul && set "PYTHON_CMD=py" )

if defined PYTHON_CMD (
    for /f "tokens=*" %%V in ('%PYTHON_CMD% --version 2^>^&1') do echo    [OK] Python encontrado: %%V ^(cmd: %PYTHON_CMD%^)
) else (
    echo    [ERRO] Python NAO encontrado. Instale Python 3.12+ em https://python.org
    set "HAS_ERROR=1"
)

REM pip
if defined PYTHON_CMD (
    %PYTHON_CMD% -m pip --version >nul 2>nul
    if !errorlevel!==0 (
        echo    [OK] pip encontrado
    ) else (
        echo    [ERRO] pip NAO encontrado. Execute: %PYTHON_CMD% -m ensurepip --upgrade
        set "HAS_ERROR=1"
    )
)

REM Projeto
if exist "%PROJECT_ROOT%\app\main.py" (
    echo    [OK] Backend encontrado: app\main.py
) else (
    echo    [ERRO] Backend NAO encontrado em %PROJECT_ROOT%\app\
    set "HAS_ERROR=1"
)
if exist "%PROJECT_ROOT%\frontend\package.json" (
    echo    [OK] Frontend encontrado: frontend\package.json
) else (
    echo    [ERRO] Frontend NAO encontrado em %PROJECT_ROOT%\frontend\
    set "HAS_ERROR=1"
)
if exist "%PROJECT_ROOT%\requirements.txt" (
    echo    [OK] requirements.txt encontrado
) else (
    echo    [ERRO] requirements.txt NAO encontrado
    set "HAS_ERROR=1"
)

if "%HAS_ERROR%"=="1" (
    echo.
    echo ============================================================
    echo   PRE-REQUISITOS FALTANDO — Corrija os erros acima
    echo ============================================================
    echo.
    goto :WAIT_EXIT_ERR
)

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 1 — Build do frontend
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 1/5 — Build do frontend
echo.

if defined SKIP_FRONTEND (
    echo    [AVISO] Build do frontend IGNORADO ^(SKIP_FRONTEND^).
    if not exist "%PROJECT_ROOT%\frontend\dist\index.html" (
        echo    [ERRO] frontend\dist\index.html nao encontrado. Rode sem SKIP_FRONTEND.
        goto :WAIT_EXIT_ERR
    )
    echo    [OK] dist\index.html existente encontrado
) else (
    pushd "%PROJECT_ROOT%\frontend"

    if not exist "node_modules" (
        echo    Instalando dependencias do frontend ^(npm install^)...
        call npm install
        if !errorlevel! neq 0 (
            echo    [ERRO] npm install falhou ^(exit code: !errorlevel!^)
            echo    Tente manualmente: cd frontend ^&^& npm install
            popd
            goto :WAIT_EXIT_ERR
        )
        echo    [OK] npm install concluido
    ) else (
        echo    [OK] node_modules ja existe — pulando npm install
    )

    echo    Executando: npm run build ^(tsc + vite^)...
    call npm run build
    if !errorlevel! neq 0 (
        echo.
        echo    [ERRO] npm run build falhou ^(exit code: !errorlevel!^)
        echo    Corrija os erros TypeScript acima e rode novamente.
        popd
        goto :WAIT_EXIT_ERR
    )

    if not exist "dist\index.html" (
        echo    [ERRO] Build nao gerou dist\index.html
        popd
        goto :WAIT_EXIT_ERR
    )
    popd
    echo    [OK] Frontend buildado com sucesso
)

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 2 — Limpar e criar estrutura de pastas
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 2/5 — Montar estrutura do pacote em %DEPLOY_DIR%
echo.

if exist "%DEPLOY_DIR%" (
    echo    Removendo pacote anterior...
    rmdir /S /Q "%DEPLOY_DIR%"
)

mkdir "%DEPLOY_DIR%\backend" 2>nul
mkdir "%DEPLOY_DIR%\frontend" 2>nul
mkdir "%DEPLOY_DIR%\wheels" 2>nul
mkdir "%DEPLOY_DIR%\scripts" 2>nul
echo    [OK] Estrutura criada: backend, frontend, wheels, scripts

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 3 — Copiar arquivos
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 3/5 — Copiar arquivos do projeto
echo.

REM Backend
xcopy /E /Y /Q "%PROJECT_ROOT%\app" "%DEPLOY_DIR%\backend\app\" >nul
xcopy /E /Y /Q "%PROJECT_ROOT%\alembic" "%DEPLOY_DIR%\backend\alembic\" >nul
copy /Y "%PROJECT_ROOT%\alembic.ini" "%DEPLOY_DIR%\backend\" >nul
copy /Y "%PROJECT_ROOT%\requirements.txt" "%DEPLOY_DIR%\backend\" >nul
copy /Y "%PROJECT_ROOT%\pytest.ini" "%DEPLOY_DIR%\backend\" >nul 2>nul
echo    [OK] Backend copiado ^(app, alembic, configs^)

REM Frontend
xcopy /E /Y /Q "%PROJECT_ROOT%\frontend\dist\*" "%DEPLOY_DIR%\frontend\" >nul
echo    [OK] Frontend copiado ^(dist/^)

REM Scripts
set "SCRIPTS_COPIED=0"
for %%F in (deploy.ps1 deploy.bat preparar-deploy.ps1 preparar-deploy.bat backup-db.ps1 health-check.ps1 instalar-servico.ps1) do (
    if exist "%PROJECT_ROOT%\scripts\%%F" (
        copy /Y "%PROJECT_ROOT%\scripts\%%F" "%DEPLOY_DIR%\scripts\" >nul 2>nul
        set /a SCRIPTS_COPIED+=1
    )
)
echo    [OK] Scripts copiados ^(!SCRIPTS_COPIED! arquivos^)

REM Docker files
for %%F in (docker-compose.yml Dockerfile) do (
    if exist "%PROJECT_ROOT%\%%F" copy /Y "%PROJECT_ROOT%\%%F" "%DEPLOY_DIR%\" >nul 2>nul
)
echo    [OK] Arquivos Docker copiados

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 4 — Baixar wheels Python
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 4/5 — Baixar wheels Python para install offline
echo.

echo    Executando: pip download -r requirements.txt ...
%PYTHON_CMD% -m pip download -r "%PROJECT_ROOT%\requirements.txt" -d "%DEPLOY_DIR%\wheels"
if !errorlevel! neq 0 (
    echo    [ERRO] pip download falhou ^(exit code: !errorlevel!^)
    echo    Verifique sua conexao com a internet e tente novamente.
    goto :WAIT_EXIT_ERR
)

set "WHEEL_COUNT=0"
for %%F in ("%DEPLOY_DIR%\wheels\*") do set /a WHEEL_COUNT+=1
echo    [OK] Wheels baixados: !WHEEL_COUNT! pacotes em wheels\

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 5 — Resumo final
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 5/5 — Resumo do pacote
echo.

set "TOTAL=0"
for /R "%DEPLOY_DIR%" %%F in (*) do set /a TOTAL+=1

echo    Conteudo do pacote:
for %%D in (backend frontend wheels scripts) do (
    set "SUB_COUNT=0"
    if exist "%DEPLOY_DIR%\%%D" (
        for /R "%DEPLOY_DIR%\%%D" %%F in (*) do set /a SUB_COUNT+=1
    )
    echo      %%D\ — !SUB_COUNT! arquivos
)

echo.
echo ============================================================
echo   PACOTE PRONTO — !TOTAL! arquivos
echo ============================================================
echo.
echo   Local: %DEPLOY_DIR%
echo.
echo   Proximo passo:
echo   1. Copie '%DEPLOY_DIR%' para o servidor ^(rede interna ou pendrive^)
echo   2. No servidor, execute:
echo      .\scripts\deploy.ps1 -PackagePath '%DEPLOY_DIR%'
echo      ou: deploy.bat %DEPLOY_DIR%
echo.

goto :WAIT_EXIT_OK

:WAIT_EXIT_ERR
echo.
echo ============================================================
echo   ERRO — Pacote NAO foi gerado. Veja os erros acima.
echo ============================================================
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 1

:WAIT_EXIT_OK
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0
