@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Dinamica Budget - Remocao Nativa (Windows Server 2022)

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "APP_DIR=C:\DinamicaBudget"
set "IIS_WEBROOT=C:\inetpub\DinamicaBudget"
set "IIS_SITE_NAME=DinamicaBudget"
set "IIS_APPPOOL=DinamicaBudgetPool"
set "SERVICE_NAME=DinamicaBudgetAPI"
set "LOG_DIR=%SCRIPT_DIR%\logs"
set "BACKUP_DIR=%SCRIPT_DIR%\backups"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
for /f "delims=" %%d in ('powershell -NoProfile -Command "Get-Date -Format ''yyyy-MM-dd_HHmmss''"') do set "TS=%%d"
set "LOG_FILE=%LOG_DIR%\remove-native-%TS%.log"
set "BACKUP_FILE=%BACKUP_DIR%\dinamica_budget_before_remove_%TS%.sql"

goto :skip_log
:log
set "M=%~1"
if "%M%"=="" (echo.) else (echo %M%)
>> "%LOG_FILE%" echo [%date% %time%] %M%
goto :eof
:skip_log

call :log "============================================================"
call :log "DINAMICA BUDGET - REMOCAO NATIVA"
call :log "============================================================"
call :log "Inicio: %date% %time%"
call :log "Log: %LOG_FILE%"
call :log ""

net session >nul 2>&1
if errorlevel 1 (
  call :fail "Execute este script como Administrador."
)

echo.
echo ATENCAO: este script remove o deploy nativo (IIS + servico API + arquivos).
echo O PostgreSQL NAO sera desinstalado.
echo.
set /p "CONFIRM=Continuar com a remocao? (S/N): "
if /i not "%CONFIRM%"=="S" (
  call :log "Remocao cancelada pelo usuario."
  goto :eof
)

call :step "1/6" "Tentando backup do banco (pg_dump)"
call :backup_db

call :step "2/6" "Parando e removendo servico NSSM"
sc query "%SERVICE_NAME%" >nul 2>&1
if errorlevel 1 (
  call :log "Servico %SERVICE_NAME% nao encontrado."
) else (
  nssm stop "%SERVICE_NAME%" >> "%LOG_FILE%" 2>&1
  nssm remove "%SERVICE_NAME%" confirm >> "%LOG_FILE%" 2>&1
  sc query "%SERVICE_NAME%" >nul 2>&1
  if errorlevel 1 (
    call :log "[OK] Servico %SERVICE_NAME% removido"
  ) else (
    call :log "[AVISO] Servico %SERVICE_NAME% ainda existe."
  )
)

call :step "3/6" "Removendo configuracao do IIS"
set "APPCMD=%windir%\System32\inetsrv\appcmd.exe"
if exist "%APPCMD%" (
  "%APPCMD%" list site "%IIS_SITE_NAME%" >nul 2>&1 && "%APPCMD%" delete site "%IIS_SITE_NAME%" >> "%LOG_FILE%" 2>&1
  "%APPCMD%" list apppool "%IIS_APPPOOL%" >nul 2>&1 && "%APPCMD%" delete apppool "%IIS_APPPOOL%" >> "%LOG_FILE%" 2>&1
  call :log "[OK] Site/app pool do Dinamica removidos (se existiam)."
) else (
  call :log "[AVISO] appcmd.exe nao encontrado (IIS possivelmente nao instalado)."
)

call :step "4/6" "Removendo regras de firewall"
netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" >nul 2>&1
netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" >nul 2>&1
call :log "[OK] Regras de firewall removidas (se existiam)."

call :step "5/6" "Removendo arquivos da aplicacao"
set /p "DEL_APP=Remover pasta da aplicacao (%APP_DIR%)? (S/N): "
if /i "%DEL_APP%"=="S" (
  if exist "%APP_DIR%" (
    rmdir /s /q "%APP_DIR%" >> "%LOG_FILE%" 2>&1
    if exist "%APP_DIR%" (
      call :log "[AVISO] Nao foi possivel remover %APP_DIR%"
    ) else (
      call :log "[OK] Pasta %APP_DIR% removida"
    )
  ) else (
    call :log "[OK] Pasta %APP_DIR% ja nao existe"
  )
) else (
  call :log "Pasta %APP_DIR% mantida por escolha do usuario."
)

set /p "DEL_IIS=Remover pasta publica do IIS (%IIS_WEBROOT%)? (S/N): "
if /i "%DEL_IIS%"=="S" (
  if exist "%IIS_WEBROOT%" (
    rmdir /s /q "%IIS_WEBROOT%" >> "%LOG_FILE%" 2>&1
    if exist "%IIS_WEBROOT%" (
      call :log "[AVISO] Nao foi possivel remover %IIS_WEBROOT%"
    ) else (
      call :log "[OK] Pasta %IIS_WEBROOT% removida"
    )
  ) else (
    call :log "[OK] Pasta %IIS_WEBROOT% ja nao existe"
  )
) else (
  call :log "Pasta %IIS_WEBROOT% mantida por escolha do usuario."
)

call :step "6/6" "Resumo"
call :log "Remocao concluida."
call :log "Backup DB (se executado com sucesso): %BACKUP_FILE%"
call :log "Log completo: %LOG_FILE%"
echo.
echo [OK] Remocao finalizada. Log: %LOG_FILE%
goto :eof

:backup_db
set "ENV_FILE=%APP_DIR%\.env"
if not exist "%ENV_FILE%" (
  call :log "[AVISO] .env nao encontrado em %APP_DIR%. Pulando backup automatico."
  goto :eof
)

set "DB_USER="
set "DB_PASS="
set "DB_HOST="
set "DB_NAME="
for /f "tokens=1-4 delims=|" %%a in ('powershell -NoProfile -Command "$line=(Get-Content ''%ENV_FILE%'' | Where-Object { $_ -match ''^DATABASE_URL='' } | Select-Object -First 1); if(-not $line){exit 1}; $url=$line.Split(''='',2)[1]; if($url -match ''postgresql\+asyncpg://([^:]+):([^@]+)@([^:/]+):\d+/([^?]+)''){Write-Output ($matches[1] + ''|'' + $matches[2] + ''|'' + $matches[3] + ''|'' + $matches[4])} else {exit 1}"') do (
  set "DB_USER=%%a"
  set "DB_PASS=%%b"
  set "DB_HOST=%%c"
  set "DB_NAME=%%d"
)
if "%DB_USER%"=="" (
  call :log "[AVISO] Nao foi possivel parsear DATABASE_URL. Pulando backup automatico."
  goto :eof
)

set "PG_DUMP="
for %%p in ("C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe") do (
  if exist "%%~p" set "PG_DUMP=%%~p"
)
if "%PG_DUMP%"=="" (
  for /f "delims=" %%p in ('where pg_dump 2^>nul') do if "%PG_DUMP%"=="" set "PG_DUMP=%%p"
)
if "%PG_DUMP%"=="" (
  call :log "[AVISO] pg_dump nao encontrado. Pulando backup automatico."
  goto :eof
)

set "PGPASSWORD=%DB_PASS%"
"%PG_DUMP%" -U "%DB_USER%" -h "%DB_HOST%" "%DB_NAME%" > "%BACKUP_FILE%" 2>> "%LOG_FILE%"
set "BKP_RC=%ERRORLEVEL%"
set "PGPASSWORD="
if "%BKP_RC%"=="0" (
  for %%f in ("%BACKUP_FILE%") do set "BKP_SIZE=%%~zf"
  if not "%BKP_SIZE%"=="" if %BKP_SIZE% gtr 100 (
    call :log "[OK] Backup do banco concluido: %BACKUP_FILE%"
  ) else (
    call :log "[AVISO] Backup gerado, mas pequeno (%BKP_SIZE% bytes)."
  )
) else (
  call :log "[AVISO] pg_dump falhou (codigo %BKP_RC%)."
)
goto :eof

:step
call :log "[ETAPA %~1] %~2"
goto :eof

:fail
call :log "[ERRO] %~1"
echo.
echo [ERRO] %~1
echo Verifique o log: %LOG_FILE%
exit /b 1
