@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Dinamica Budget - Deploy Nativo (Windows Server 2022)

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "SRC_DIR=%SCRIPT_DIR%"
set "APP_DIR=C:\DinamicaBudget"
set "IIS_WEBROOT=C:\inetpub\DinamicaBudget"
set "IIS_SITE_NAME=DinamicaBudget"
set "IIS_APPPOOL=DinamicaBudgetPool"
set "SERVICE_NAME=DinamicaBudgetAPI"
set "SITE_PORT=80"
set "SITE_HOST="
set "API_PORT=8000"
set "PG_SERVICE=postgresql-x64-16"
set "LOG_DIR=%SRC_DIR%\logs"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
for /f "delims=" %%d in ('powershell -NoProfile -Command "Get-Date -Format ''yyyy-MM-dd_HHmmss''"') do set "TS=%%d"
set "LOG_FILE=%LOG_DIR%\deploy-native-%TS%.log"

goto :skip_log
:log
set "M=%~1"
if "%M%"=="" (echo.) else (echo %M%)
>> "%LOG_FILE%" echo [%date% %time%] %M%
goto :eof
:skip_log

call :log "============================================================"
call :log "DINAMICA BUDGET - DEPLOY NATIVO (SEM DOCKER)"
call :log "============================================================"
call :log "Inicio: %date% %time%"
call :log "Origem: %SRC_DIR%"
call :log "Destino app: %APP_DIR%"
call :log "Log: %LOG_FILE%"
call :log ""

call :step "1/10" "Verificando privilegios e SO"
net session >nul 2>&1
if errorlevel 1 (
  call :fail "Execute este script como Administrador."
)
for /f "tokens=2 delims=[]" %%v in ('ver') do set "WIN_VER=%%v"
for /f "tokens=5" %%b in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild ^| findstr /i CurrentBuild') do set "WIN_BUILD=%%b"
call :log "Windows build: %WIN_BUILD%"
if "%WIN_BUILD%"=="" call :fail "Nao foi possivel detectar a build do Windows."
if %WIN_BUILD% lss 20348 call :log "[AVISO] Build abaixo do Windows Server 2022 (20348)."

call :step "2/10" "Validando arquivos obrigatorios"
for %%f in (requirements.txt alembic.ini .env.example) do (
  if not exist "%SRC_DIR%\%%f" call :fail "Arquivo ausente: %%f"
)
if not exist "%SRC_DIR%\app\main.py" call :fail "Arquivo ausente: app\main.py"
if not exist "%SRC_DIR%\frontend\package.json" call :fail "Arquivo ausente: frontend\package.json"
if not exist "%windir%\System32\inetsrv\appcmd.exe" call :fail "IIS nao instalado. Instale o role Web-Server (IIS)."

call :check_cmd python "Python 3.12"
call :check_cmd pip "pip"
call :check_cmd node "Node.js LTS"
call :check_cmd npm "npm"
call :check_cmd nssm "NSSM"

call :step "3/10" "Preparando PostgreSQL"
sc query "%PG_SERVICE%" >nul 2>&1
if errorlevel 1 (
  call :log "[AVISO] Servico %PG_SERVICE% nao encontrado. Verifique a instalacao do PostgreSQL 16."
) else (
  for /f "tokens=3" %%s in ('sc query "%PG_SERVICE%" ^| findstr /i STATE') do set "PG_STATE=%%s"
  if /i not "%PG_STATE%"=="RUNNING" (
    call :log "Servico %PG_SERVICE% parado. Tentando iniciar..."
    net start "%PG_SERVICE%" >> "%LOG_FILE%" 2>&1
  )
)

call :step "4/10" "Sincronizando projeto para %APP_DIR%"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
robocopy "%SRC_DIR%" "%APP_DIR%" /MIR /R:2 /W:2 /NFL /NDL /NP /XD ".git" "node_modules" "venv" ".venv" "logs" "output" "__pycache__" >> "%LOG_FILE%" 2>&1
set "RC=%ERRORLEVEL%"
if %RC% gtr 7 call :fail "Falha no robocopy (codigo %RC%)."
call :log "[OK] Projeto sincronizado para %APP_DIR%"

call :step "5/10" "Criando venv e instalando dependencias Python"
if not exist "%APP_DIR%\venv\Scripts\python.exe" (
  call :log "Criando ambiente virtual..."
  python -m venv "%APP_DIR%\venv" >> "%LOG_FILE%" 2>&1
  if errorlevel 1 call :fail "Falha ao criar venv."
)
"%APP_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
"%APP_DIR%\venv\Scripts\pip.exe" install -r "%APP_DIR%\requirements.txt" >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :fail "Falha ao instalar requirements.txt"

call :step "6/10" "Configurando .env"
if not exist "%APP_DIR%\.env" (
  copy /y "%APP_DIR%\.env.example" "%APP_DIR%\.env" >nul
  for /f "delims=" %%k in ('"%APP_DIR%\venv\Scripts\python.exe" -c "import secrets; print(secrets.token_hex(32))"') do set "GEN_KEY=%%k"
  powershell -NoProfile -Command "(Get-Content '%APP_DIR%\.env') -replace 'SECRET_KEY=CHANGE_ME_use_secrets_token_hex_32','SECRET_KEY=%GEN_KEY%' -replace 'SENTENCE_TRANSFORMERS_HOME=./ml_models','SENTENCE_TRANSFORMERS_HOME=C:/DinamicaBudget/ml_models' -replace 'ALLOWED_ORIGINS=.*','ALLOWED_ORIGINS=[\"http://localhost\",\"http://127.0.0.1\"]' | Set-Content '%APP_DIR%\.env' -Encoding UTF8" >> "%LOG_FILE%" 2>&1
  call :log "[OK] .env criado automaticamente."
) else (
  call :log "[OK] .env existente sera mantido."
)
findstr /i "password@localhost" "%APP_DIR%\.env" >nul 2>&1
if not errorlevel 1 (
  call :log "[AVISO] DATABASE_URL ainda parece com senha padrao. Ajuste antes de producao."
)

call :step "7/10" "Rodando migracoes Alembic"
pushd "%APP_DIR%"
"%APP_DIR%\venv\Scripts\alembic.exe" upgrade head >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  popd
  call :fail "Falha ao executar alembic upgrade head."
)
popd
call :log "[OK] Migracoes aplicadas"

call :step "8/10" "Build do frontend"
pushd "%APP_DIR%\frontend"
call npm install >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  popd
  call :fail "Falha no npm install"
)
call npm run build >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  popd
  call :fail "Falha no npm run build"
)
popd
if not exist "%APP_DIR%\frontend\dist\index.html" call :fail "Build frontend nao gerou dist\index.html"
if not exist "%IIS_WEBROOT%" mkdir "%IIS_WEBROOT%"
robocopy "%APP_DIR%\frontend\dist" "%IIS_WEBROOT%" /MIR /R:2 /W:2 /NFL /NDL /NP >> "%LOG_FILE%" 2>&1
set "RC=%ERRORLEVEL%"
if %RC% gtr 7 call :fail "Falha ao copiar frontend para IIS (codigo %RC%)."

call :step "9/10" "Configurando IIS e servico NSSM"
set "APPCMD=%windir%\System32\inetsrv\appcmd.exe"

powershell -NoProfile -Command "Install-WindowsFeature Web-Server,Web-Default-Doc,Web-Static-Content,Web-Http-Logging,Web-Stat-Compression,Web-Filtering -IncludeManagementTools | Out-Null" >> "%LOG_FILE%" 2>&1

(
echo ^<?xml version="1.0" encoding="UTF-8"?^>
echo ^<configuration^>
echo   ^<system.webServer^>
echo     ^<rewrite^>
echo       ^<rules^>
echo         ^<rule name="API Reverse Proxy" stopProcessing="true"^>
echo           ^<match url="^(api/.*^|health^|docs^|redoc^|openapi.json)(.*)$" /^>
echo           ^<action type="Rewrite" url="http://127.0.0.1:%API_PORT%/{R:0}" /^>
echo         ^</rule^>
echo         ^<rule name="SPA Fallback" stopProcessing="true"^>
echo           ^<match url="(.*)" /^>
echo           ^<conditions^>
echo             ^<add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" /^>
echo             ^<add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" /^>
echo           ^</conditions^>
echo           ^<action type="Rewrite" url="/index.html" /^>
echo         ^</rule^>
echo       ^</rules^>
echo     ^</rewrite^>
echo   ^</system.webServer^>
echo ^</configuration^>
) > "%IIS_WEBROOT%\web.config"

"%APPCMD%" list apppool "%IIS_APPPOOL%" >nul 2>&1 || "%APPCMD%" add apppool /name:"%IIS_APPPOOL%" >> "%LOG_FILE%" 2>&1
"%APPCMD%" set apppool "%IIS_APPPOOL%" /managedRuntimeVersion:"" >> "%LOG_FILE%" 2>&1

"%APPCMD%" list site "Default Web Site" | findstr /i "http/*:80:" >nul 2>&1 && "%APPCMD%" stop site "Default Web Site" >> "%LOG_FILE%" 2>&1
"%APPCMD%" list site "%IIS_SITE_NAME%" >nul 2>&1 && "%APPCMD%" delete site "%IIS_SITE_NAME%" >> "%LOG_FILE%" 2>&1

if "%SITE_HOST%"=="" (
  "%APPCMD%" add site /name:"%IIS_SITE_NAME%" /bindings:"http/*:%SITE_PORT%:" /physicalPath:"%IIS_WEBROOT%" >> "%LOG_FILE%" 2>&1
) else (
  "%APPCMD%" add site /name:"%IIS_SITE_NAME%" /bindings:"http/*:%SITE_PORT%:%SITE_HOST%" /physicalPath:"%IIS_WEBROOT%" >> "%LOG_FILE%" 2>&1
)
"%APPCMD%" set app "%IIS_SITE_NAME%/" /applicationPool:"%IIS_APPPOOL%" >> "%LOG_FILE%" 2>&1
"%APPCMD%" start site "%IIS_SITE_NAME%" >> "%LOG_FILE%" 2>&1

"%APPCMD%" set config -section:system.webServer/proxy /enabled:"True" /commit:apphost >> "%LOG_FILE%" 2>&1

if not exist "%APP_DIR%\logs" mkdir "%APP_DIR%\logs"
set "PY_EXE=%APP_DIR%\venv\Scripts\python.exe"
set "PY_ARGS=-m uvicorn app.main:app --host 127.0.0.1 --port %API_PORT% --workers 2"
sc query "%SERVICE_NAME%" >nul 2>&1
if errorlevel 1 (
  nssm install "%SERVICE_NAME%" "%PY_EXE%" %PY_ARGS% >> "%LOG_FILE%" 2>&1
) else (
  nssm set "%SERVICE_NAME%" Application "%PY_EXE%" >> "%LOG_FILE%" 2>&1
  nssm set "%SERVICE_NAME%" AppParameters "%PY_ARGS%" >> "%LOG_FILE%" 2>&1
)
nssm set "%SERVICE_NAME%" AppDirectory "%APP_DIR%" >> "%LOG_FILE%" 2>&1
nssm set "%SERVICE_NAME%" DisplayName "Dinamica Budget API" >> "%LOG_FILE%" 2>&1
nssm set "%SERVICE_NAME%" Description "FastAPI backend Dinamica Budget" >> "%LOG_FILE%" 2>&1
nssm set "%SERVICE_NAME%" Start SERVICE_AUTO_START >> "%LOG_FILE%" 2>&1
nssm set "%SERVICE_NAME%" AppStdout "%APP_DIR%\logs\stdout.log" >> "%LOG_FILE%" 2>&1
nssm set "%SERVICE_NAME%" AppStderr "%APP_DIR%\logs\stderr.log" >> "%LOG_FILE%" 2>&1
nssm set "%SERVICE_NAME%" AppEnvironmentExtra "SENTENCE_TRANSFORMERS_HOME=C:\DinamicaBudget\ml_models" >> "%LOG_FILE%" 2>&1
nssm restart "%SERVICE_NAME%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 nssm start "%SERVICE_NAME%" >> "%LOG_FILE%" 2>&1

netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" >nul 2>&1
netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" >nul 2>&1
netsh advfirewall firewall add rule name="Dinamica Budget HTTP" dir=in action=allow protocol=TCP localport=80 >nul 2>&1
netsh advfirewall firewall add rule name="Dinamica Budget HTTPS" dir=in action=allow protocol=TCP localport=443 >nul 2>&1

call :step "10/10" "Validando saude da API"
powershell -NoProfile -Command "$ok=$false; 1..20 | ForEach-Object { try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:%API_PORT%/health' -TimeoutSec 5; if ($r.status -eq 'ok') { $ok=$true; break } } catch {}; Start-Sleep -Seconds 2 }; if ($ok) { exit 0 } else { exit 1 }" >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :fail "Health check local falhou em http://127.0.0.1:%API_PORT%/health"

powershell -NoProfile -Command "$ok=$false; 1..10 | ForEach-Object { try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1/health' -TimeoutSec 5; if ($r.status -eq 'ok') { $ok=$true; break } } catch {}; Start-Sleep -Seconds 2 }; if ($ok) { exit 0 } else { exit 1 }" >> "%LOG_FILE%" 2>&1
if errorlevel 1 call :log "[AVISO] Health via IIS (/health) nao respondeu. Verifique URL Rewrite/ARR."

call :log ""
call :log "DEPLOY NATIVO CONCLUIDO COM SUCESSO"
call :log "Aplicacao: %APP_DIR%"
call :log "Site IIS: %IIS_SITE_NAME% em %IIS_WEBROOT%"
call :log "Servico API: %SERVICE_NAME%"
call :log "Health local: http://127.0.0.1:%API_PORT%/health"
call :log "Health IIS:   http://127.0.0.1/health"
call :log ""
echo.
echo [OK] Deploy concluido. Consulte o log: %LOG_FILE%
goto :eof

:step
call :log "[ETAPA %~1] %~2"
goto :eof

:check_cmd
where %~1 >nul 2>&1
if errorlevel 1 call :fail "%~2 nao encontrado no PATH."
goto :eof

:fail
call :log "[ERRO] %~1"
echo.
echo [ERRO] %~1
echo Verifique o log: %LOG_FILE%
exit /b 1
