@echo off
chcp 65001 >nul 2>nul
REM ──────────────────────────────────────────────────────────────────────────
REM deploy.bat — Instalador inteligente: deploy no Windows Server
REM
REM Uso: duplo-clique ou terminal:
REM   deploy.bat D:\deploy-package
REM   deploy.bat \\servidor\share\deploy-package
REM
REM O script valida tudo, executa etapa por etapa, e nunca fecha a janela.
REM ──────────────────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion
title Dinamica Budget - Deploy

set "PACKAGE=%~1"
set "APP_ROOT=C:\apps\dinamica-budget"
set "HAS_ERROR=0"

if "%PACKAGE%"=="" (
    echo.
    echo    [ERRO] Informe o caminho do pacote.
    echo    Uso: deploy.bat D:\deploy-package
    echo.
    goto :WAIT_EXIT_ERR
)

echo.
echo ============================================================
echo   DEPLOY DINAMICA BUDGET — Windows Server
echo ============================================================
echo.
echo   Pacote  : %PACKAGE%
echo   Destino : %APP_ROOT%
echo   Data    : %date% %time%
echo.

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 0 — Validar pacote e ambiente
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 0/6 — Validar pacote e ambiente do servidor
echo.

if exist "%PACKAGE%" (
    echo    [OK] Pacote encontrado: %PACKAGE%
) else (
    echo    [ERRO] Pacote NAO encontrado: %PACKAGE%
    set "HAS_ERROR=1"
)
if exist "%PACKAGE%\backend\app" (
    echo    [OK] backend\app encontrado no pacote
) else (
    echo    [ERRO] backend\app NAO encontrado no pacote
    set "HAS_ERROR=1"
)
if exist "%PACKAGE%\frontend\index.html" (
    echo    [OK] frontend\index.html encontrado no pacote
) else (
    echo    [ERRO] frontend\index.html NAO encontrado no pacote
    set "HAS_ERROR=1"
)
if exist "%APP_ROOT%\venv\Scripts\python.exe" (
    echo    [OK] Virtualenv encontrado: %APP_ROOT%\venv
) else (
    echo    [ERRO] Virtualenv NAO encontrado em %APP_ROOT%\venv
    echo    Crie com: python -m venv %APP_ROOT%\venv
    set "HAS_ERROR=1"
)
if exist "%APP_ROOT%\.env" (
    echo    [OK] .env encontrado em %APP_ROOT%\
) else (
    echo    [ERRO] .env NAO encontrado em %APP_ROOT%\ — configure antes do deploy
    set "HAS_ERROR=1"
)
if exist "%PACKAGE%\wheels" (
    echo    [OK] Pasta wheels encontrada
) else (
    echo    [ERRO] Pasta wheels NAO encontrada em %PACKAGE%\wheels
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

REM ── Criar estrutura ────────────────────────────────────────────────────────
for %%D in (backend frontend logs backups scripts) do (
    if not exist "%APP_ROOT%\%%D" mkdir "%APP_ROOT%\%%D"
)
echo    [OK] Estrutura de pastas verificada

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 1 — Parar servico
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 1/6 — Parar servico DinamicaBudget
echo.

net stop DinamicaBudget >nul 2>nul
if %errorlevel%==0 (
    echo    [OK] Servico parado
) else (
    echo    [AVISO] Servico nao estava rodando ^(primeira instalacao?^)
)

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 2 — Copiar backend
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 2/6 — Copiar backend
echo.

xcopy /E /Y /Q "%PACKAGE%\backend\*" "%APP_ROOT%\backend\" >nul
if !errorlevel! neq 0 (
    echo    [ERRO] Falha ao copiar backend
    goto :WAIT_EXIT_ERR
)
echo    [OK] Backend copiado para %APP_ROOT%\backend\

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 3 — Copiar frontend
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 3/6 — Copiar frontend ^(build estatico^)
echo.

xcopy /E /Y /Q "%PACKAGE%\frontend\*" "%APP_ROOT%\frontend\" >nul
if !errorlevel! neq 0 (
    echo    [ERRO] Falha ao copiar frontend
    goto :WAIT_EXIT_ERR
)
echo    [OK] Frontend copiado para %APP_ROOT%\frontend\

REM Scripts
if exist "%PACKAGE%\scripts" (
    xcopy /E /Y /Q "%PACKAGE%\scripts\*" "%APP_ROOT%\scripts\" >nul 2>nul
    echo    [OK] Scripts atualizados
)

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 4 — Instalar dependencias Python (offline)
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 4/6 — Instalar dependencias Python ^(offline^)
echo.

echo    Executando: pip install --no-index --find-links wheels ...
"%APP_ROOT%\venv\Scripts\pip.exe" install -r "%APP_ROOT%\backend\requirements.txt" --no-index --find-links "%PACKAGE%\wheels"
if !errorlevel! neq 0 (
    echo    [ERRO] pip install falhou ^(exit code: !errorlevel!^)
    goto :WAIT_EXIT_ERR
)
echo    [OK] Dependencias Python instaladas

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 5 — Rodar migrations
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 5/6 — Rodar Alembic migrations
echo.

REM Carregar variaveis do .env
for /f "usebackq tokens=1,* delims==" %%A in ("%APP_ROOT%\.env") do (
    set "%%A=%%B"
)
echo    Variaveis de ambiente carregadas do .env

pushd "%APP_ROOT%\backend"
echo    Executando: alembic upgrade head ...
"%APP_ROOT%\venv\Scripts\alembic.exe" upgrade head
if !errorlevel! neq 0 (
    echo    [ERRO] Alembic migrations falharam ^(exit code: !errorlevel!^)
    echo    Verifique se o PostgreSQL esta rodando e a DATABASE_URL esta correta.
    popd
    goto :WAIT_EXIT_ERR
)
popd
echo    [OK] Migrations aplicadas com sucesso

REM ══════════════════════════════════════════════════════════════════════════════
REM ETAPA 6 — Iniciar servico e health check
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ^>^> ETAPA 6/6 — Iniciar servico e health check
echo.

net start DinamicaBudget >nul 2>nul
if %errorlevel%==0 (
    echo    [OK] Servico DinamicaBudget iniciado
) else (
    echo    [AVISO] Servico DinamicaBudget nao registrado ou nao iniciou.
    echo    Execute primeiro: instalar-servico.ps1
    echo    Ou inicie manualmente:
    echo      cd %APP_ROOT%\backend
    echo      %APP_ROOT%\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
)

echo    Aguardando aplicacao inicializar ^(5s^)...
timeout /t 5 /nobreak >nul

echo    Verificando health check...
curl -s -o nul -w "   HTTP Status: %%{http_code}\n" http://localhost:8000/health 2>nul
if %errorlevel%==0 (
    curl -s http://localhost:8000/health 2>nul
    echo.
    echo    [OK] Health check executado
) else (
    echo    [AVISO] Health check falhou — a aplicacao pode levar mais tempo para iniciar.
    echo    Tente: curl http://localhost:8000/health
)

REM ── Resultado final ─────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   DEPLOY CONCLUIDO COM SUCESSO
echo ============================================================
echo.
echo   Aplicacao: %APP_ROOT%
echo   URL:       http://localhost:8000
echo   Health:    http://localhost:8000/health
echo   Logs:      %APP_ROOT%\logs\
echo.

goto :WAIT_EXIT_OK

:WAIT_EXIT_ERR
echo.
echo ============================================================
echo   ERRO — Deploy NAO concluido. Veja os erros acima.
echo ============================================================
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 1

:WAIT_EXIT_OK
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0
