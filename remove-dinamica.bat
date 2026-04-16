@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title ══ Dinamica Budget — Desinstalador v4.0 ══

REM ============================================================================
REM  DINAMICA BUDGET — Desinstalador para Windows Server 2022
REM  Versao: 4.0 — Abril 2026
REM  * Backup automatico do banco antes de qualquer acao
REM  * Cada etapa detecta se ja foi removida e pula automaticamente
REM  * Permite remover sem backup (modo rapido)
REM  * Remove entrada do hosts file (dinamica-budget.local)
REM  * Nao remove PostgreSQL nem IIS (apenas o site/pool e banco da aplicacao)
REM ============================================================================

REM ── CONFIGURACAO ────────────────────────────────────────────────────────────
set "APP=C:\DinamicaBudget"
set "IIS_ROOT=C:\inetpub\DinamicaBudget"
set "IIS_SITE=DinamicaBudget"
set "IIS_POOL=DinamicaBudgetPool"
set "SVC=DinamicaBudgetAPI"
set "DB_NAME=dinamica_budget"
set "HOSTNAME_URL=dinamica-budget.local"
set "APPCMD=%windir%\System32\inetsrv\appcmd.exe"

REM ── ANSI ESCAPE ─────────────────────────────────────────────────────────────
set "ESC="
for /f "delims=" %%a in ('echo prompt $E ^| cmd 2^>nul') do set "ESC=%%a"
if defined ESC (
    set "G=!ESC![92m" & set "C=!ESC![96m" & set "Y=!ESC![93m"
    set "R=!ESC![91m" & set "W=!ESC![97m" & set "B=!ESC![1m" & set "N=!ESC![0m"
) else (
    set "G=" & set "C=" & set "Y=" & set "R=" & set "W=" & set "B=" & set "N="
)

REM ── LOGGING ─────────────────────────────────────────────────────────────────
set "LOGD=!APP!\logs"
if not exist "!LOGD!" (
    set "LOGD=%TEMP%\DinamicaBudget_logs"
    if not exist "!LOGD!" mkdir "!LOGD!"
)
for /f "delims=" %%d in ('powershell -NoProfile -Command "Get-Date -Format ''yyyyMMdd_HHmmss''"') do set "TS=%%d"
set "LOG=!LOGD!\remove-!TS!.log"

REM ── CONTADORES ──────────────────────────────────────────────────────────────
set /a "C_OK=0, C_SKIP=0, C_WARN=0"

goto :main

REM ═══════════════════════════════════════════════════════════════════════════
REM  FUNCOES
REM ═══════════════════════════════════════════════════════════════════════════

:hdr
echo.
echo !C!════════════════════════════════════════════════════════════════!N!
echo !C!  %~1!N!
echo !C!════════════════════════════════════════════════════════════════!N!
>> "!LOG!" echo ═══ %~1
goto :eof

:step
echo.
echo  !B!!W![ETAPA %~1] %~2!N!
>> "!LOG!" echo [%date% %time%] [ETAPA %~1] %~2
goto :eof

:ok
set /a "C_OK+=1"
echo   !G![OK]!N! %~1
>> "!LOG!" echo [%date% %time%] [OK] %~1
goto :eof

:skip
set /a "C_SKIP+=1"
echo   !C![SKIP]!N! %~1
>> "!LOG!" echo [%date% %time%] [SKIP] %~1
goto :eof

:warn
set /a "C_WARN+=1"
echo   !Y![WARN]!N! %~1
>> "!LOG!" echo [%date% %time%] [WARN] %~1
goto :eof

:info
echo   [INFO] %~1
>> "!LOG!" echo [%date% %time%] [INFO] %~1
goto :eof

REM ═══════════════════════════════════════════════════════════════════════════
:main
REM ═══════════════════════════════════════════════════════════════════════════

call :hdr "DINAMICA BUDGET — DESINSTALADOR v4.0"

REM Admin check
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo   !R![ERRO]!N! Execute este script como Administrador.
    echo          Clique direito no arquivo ^> Executar como administrador
    exit /b 1
)
call :ok "Executando como Administrador"
>> "!LOG!" echo Inicio: %date% %time%

REM ── CONFIRMACAO ─────────────────────────────────────────────────────────────
echo.
echo   !Y!ATENCAO: Este script ira remover o sistema Dinamica Budget.!N!
echo.
echo   Componentes que serao removidos:
echo     - Servico Windows (!SVC!) via NSSM
echo     - Site IIS (!IIS_SITE!) e App Pool (!IIS_POOL!)
echo     - Regras de Firewall (Dinamica Budget HTTP/HTTPS)
echo     - Diretorios: !APP! e !IIS_ROOT! (opcional)
echo     - Banco de dados: !DB_NAME! (opcional, com backup previo)
echo.
echo   !G!Componentes que NAO serao afetados:!N!
echo     - PostgreSQL (servidor e servico)
echo     - IIS (role Web-Server)
echo     - NSSM (binario)
echo     - Node.js, Python
echo.

set "CONFIRMACAO="
set /p "CONFIRMACAO=  Deseja continuar? (S/N): "
if /i not "!CONFIRMACAO!"=="S" (
    echo.
    echo   Remocao cancelada pelo usuario.
    exit /b 0
)

set "SKIP_BACKUP=N"
set /p "SKIP_BACKUP=  Pular backup e remover banco diretamente? (S/N) [N]: "
if "!SKIP_BACKUP!"=="" set "SKIP_BACKUP=N"

REM ── ETAPA 1/6: BACKUP DO BANCO ─────────────────────────────────────────────
call :step "1/7" "Backup do banco de dados"

if /i "!SKIP_BACKUP!"=="S" (
    call :skip "Backup pulado por opcao do usuario"
    goto :etapa2
)

set "PGDUMP_BIN="
for %%v in (17 16 15 14) do (
    if not defined PGDUMP_BIN if exist "C:\Program Files\PostgreSQL\%%v\bin\pg_dump.exe" (
        set "PGDUMP_BIN=C:\Program Files\PostgreSQL\%%v\bin\pg_dump.exe"
    )
)
if not defined PGDUMP_BIN (
    for /f "delims=" %%p in ('where pg_dump 2^>nul') do if not defined PGDUMP_BIN set "PGDUMP_BIN=%%p"
)

if not defined PGDUMP_BIN (
    call :warn "pg_dump nao encontrado. Backup nao sera realizado automaticamente."
    echo   !Y!Recomendacao: Faca backup manualmente via pgAdmin antes de prosseguir.!N!
    set "CONT_BK="
    set /p "CONT_BK=  Continuar sem backup? (S/N): "
    if /i not "!CONT_BK!"=="S" (
        echo   Remocao cancelada. Faca o backup e reexecute.
        exit /b 0
    )
    goto :etapa2
)

REM Check if DB exists
set "PSQL_BIN="
for %%v in (17 16 15 14) do (
    if not defined PSQL_BIN if exist "C:\Program Files\PostgreSQL\%%v\bin\psql.exe" (
        set "PSQL_BIN=C:\Program Files\PostgreSQL\%%v\bin\psql.exe"
    )
)

REM Try to get DB password from .env
set "DB_PASS="
if exist "!APP!\.env" (
    powershell -NoProfile -Command "$l=(Get-Content '!APP!\.env') | Where-Object {$_ -match '^DATABASE_URL='}; if($l -match '://[^:]+:([^@]+)@'){$Matches[1] | Out-File -NoNewline -Encoding utf8 (Join-Path $env:TEMP '_dbpass_remove.tmp')}" >nul 2>&1
    setlocal DisableDelayedExpansion
    if exist "%TEMP%\_dbpass_remove.tmp" for /f "usebackq delims=" %%p in ("%TEMP%\_dbpass_remove.tmp") do set "DB_PASS=%%p"
    endlocal & set "DB_PASS=%DB_PASS%"
    del "%TEMP%\_dbpass_remove.tmp" >nul 2>&1
)

if not defined DB_PASS (
    set /p "DB_PASS=  Senha do postgres para backup: "
)

if defined DB_PASS (
    set "PGPASSWORD=!DB_PASS!"
    set "BK_DIR=C:\DinamicaBudget_backups"
    if not exist "!BK_DIR!" mkdir "!BK_DIR!"
    set "BK_FILE=!BK_DIR!\!DB_NAME!_!TS!.sql"

    call :info "Executando pg_dump..."
    "!PGDUMP_BIN!" -U postgres -h localhost -d "!DB_NAME!" -F p -f "!BK_FILE!" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Backup falhou. Banco pode nao existir ou senha incorreta."
        echo   !Y!O banco '!DB_NAME!' pode ja ter sido removido.!N!
    ) else (
        for %%f in ("!BK_FILE!") do set "BK_SIZE=%%~zf"
        call :ok "Backup salvo: !BK_FILE! (!BK_SIZE! bytes)"
    )
    set "PGPASSWORD="
) else (
    call :warn "Sem senha — backup pulado."
)

REM ── ETAPA 2/6: PARAR E REMOVER SERVICO ─────────────────────────────────────
:etapa2
call :step "2/7" "Remover servico Windows (!SVC!)"

sc query "!SVC!" >nul 2>&1
if errorlevel 1 (
    call :skip "Servico !SVC! nao encontrado"
    goto :etapa3
)

REM Detect NSSM
set "NSSM_CMD="
where nssm >nul 2>&1
if not errorlevel 1 (
    set "NSSM_CMD=nssm"
) else (
    if exist "C:\Windows\System32\nssm.exe" set "NSSM_CMD=C:\Windows\System32\nssm.exe"
)

if defined NSSM_CMD (
    call :info "Parando servico..."
    "!NSSM_CMD!" stop "!SVC!" >> "!LOG!" 2>&1
    REM Wait a moment for service to stop
    powershell -NoProfile -Command "Start-Sleep -Seconds 3" >nul 2>&1

    call :info "Removendo servico..."
    "!NSSM_CMD!" remove "!SVC!" confirm >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "NSSM remove falhou, tentando sc delete..."
        net stop "!SVC!" >> "!LOG!" 2>&1
        sc delete "!SVC!" >> "!LOG!" 2>&1
    )
) else (
    call :info "NSSM nao encontrado. Usando sc diretamente..."
    net stop "!SVC!" >> "!LOG!" 2>&1
    sc delete "!SVC!" >> "!LOG!" 2>&1
)

REM Verify
sc query "!SVC!" >nul 2>&1
if errorlevel 1 (
    call :ok "Servico !SVC! removido"
) else (
    call :warn "Servico pode precisar de reboot para ser completamente removido"
)

REM Limpa processos residuais da aplicacao
for /f "tokens=2" %%p in ('wmic process where "Name='python.exe' and ExecutablePath like 'C:\\DinamicaBudget%%'" get ProcessId /value 2^>nul ^| find "="') do (
    taskkill /PID %%p /F >nul 2>&1
)
for /f "tokens=2" %%p in ('wmic process where "Name='node.exe' and ExecutablePath like 'C:\\DinamicaBudget%%'" get ProcessId /value 2^>nul ^| find "="') do (
    taskkill /PID %%p /F >nul 2>&1
)
call :info "Processos residuais do sistema encerrados (se existentes)"

REM ── ETAPA 3/6: REMOVER SITE IIS ────────────────────────────────────────────
:etapa3
call :step "3/7" "Remover site e app pool do IIS"

if not exist "!APPCMD!" (
    call :skip "IIS nao instalado (appcmd nao encontrado)"
    goto :etapa4
)

REM Stop and delete site
"!APPCMD!" list site "!IIS_SITE!" >nul 2>&1
if errorlevel 1 (
    call :skip "Site !IIS_SITE! nao existe"
) else (
    "!APPCMD!" stop site "!IIS_SITE!" >> "!LOG!" 2>&1
    "!APPCMD!" delete site "!IIS_SITE!" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao deletar site !IIS_SITE!"
    ) else (
        call :ok "Site !IIS_SITE! removido"
    )
)

REM Delete app pool
"!APPCMD!" list apppool "!IIS_POOL!" >nul 2>&1
if errorlevel 1 (
    call :skip "App pool !IIS_POOL! nao existe"
) else (
    "!APPCMD!" stop apppool "!IIS_POOL!" >> "!LOG!" 2>&1
    "!APPCMD!" delete apppool "!IIS_POOL!" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao deletar app pool !IIS_POOL!"
    ) else (
        call :ok "App pool !IIS_POOL! removido"
    )
)

REM ── ETAPA 4/7: REMOVER FIREWALL ────────────────────────────────────────────
:etapa4
call :step "4/7" "Remover regras de Firewall"

netsh advfirewall firewall show rule name="Dinamica Budget HTTP" >nul 2>&1
if errorlevel 1 (
    call :skip "Regra HTTP nao existe"
) else (
    netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" >nul 2>&1
    call :ok "Regra 'Dinamica Budget HTTP' removida"
)

netsh advfirewall firewall show rule name="Dinamica Budget HTTPS" >nul 2>&1
if errorlevel 1 (
    call :skip "Regra HTTPS nao existe"
) else (
    netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" >nul 2>&1
    call :ok "Regra 'Dinamica Budget HTTPS' removida"
)

REM ── ETAPA 5/7: REMOVER HOSTNAME DO HOSTS FILE ─────────────────────────────
call :step "5/7" "Remover hostname do hosts file"

set "HOSTS_FILE=%windir%\System32\drivers\etc\hosts"
findstr /i "dinamica-budget" "!HOSTS_FILE!" >nul 2>&1
if errorlevel 1 (
    call :skip "Nenhuma entrada dinamica-budget no hosts file"
) else (
    powershell -NoProfile -Command ^
        "$h=Get-Content '!HOSTS_FILE!' -Encoding ASCII -ErrorAction SilentlyContinue;" ^
        "$h=$h | Where-Object { $_ -notmatch 'dinamica-budget\\.local' -and $_ -notmatch '# Dinamica Budget' };" ^
        "$txt=''; if($h){$txt=[string]::Join([Environment]::NewLine,$h)}; [System.IO.File]::WriteAllText('!HOSTS_FILE!',$txt + [Environment]::NewLine,[System.Text.Encoding]::ASCII); ipconfig /flushdns | Out-Null" >> "!LOG!" 2>&1
    call :ok "Entrada '!HOSTNAME_URL!' removida do hosts file"
)

REM ── ETAPA 6/7: REMOVER DIRETORIOS ──────────────────────────────────────────
call :step "6/7" "Remover diretorios da aplicacao"

echo.
echo   Diretorios que podem ser removidos:
if exist "!APP!" echo     1. !APP! (aplicacao principal)
if exist "!IIS_ROOT!" echo     2. !IIS_ROOT! (frontend IIS)
echo.

set "RM_DIRS="
set /p "RM_DIRS=  Remover diretorios acima? (S=Sim, N=Manter, B=Manter backup+logs): "

if /i "!RM_DIRS!"=="S" (
    if exist "!IIS_ROOT!" (
        rmdir /s /q "!IIS_ROOT!" >> "!LOG!" 2>&1
        if exist "!IIS_ROOT!" (
            call :warn "Falha ao remover !IIS_ROOT! — arquivos podem estar em uso"
        ) else (
            call :ok "!IIS_ROOT! removido"
        )
    )
    if exist "!APP!" (
        rmdir /s /q "!APP!" >> "!LOG!" 2>&1
        if exist "!APP!" (
            call :warn "Falha ao remover !APP! — arquivos podem estar em uso"
        ) else (
            call :ok "!APP! removido"
        )
    )
) else if /i "!RM_DIRS!"=="B" (
    if exist "!IIS_ROOT!" (
        rmdir /s /q "!IIS_ROOT!" >> "!LOG!" 2>&1
        if not exist "!IIS_ROOT!" call :ok "!IIS_ROOT! removido"
    )
    if exist "!APP!" (
        REM Keep logs and .env, remove the rest
        call :info "Preservando !APP!\logs\ e !APP!\.env"
        for /d %%d in ("!APP!\*") do (
            set "DN=%%~nxd"
            if /i not "!DN!"=="logs" (
                rmdir /s /q "%%d" >> "!LOG!" 2>&1
            )
        )
        for %%f in ("!APP!\*") do (
            set "FN=%%~nxf"
            if /i not "!FN!"==".env" (
                del /q "%%f" >> "!LOG!" 2>&1
            )
        )
        call :ok "!APP! limpo (logs e .env preservados)"
    )
) else (
    call :skip "Diretorios mantidos por decisao do usuario"
)

REM ── ETAPA 7/7: REMOVER BANCO (OPCIONAL) ────────────────────────────────────
call :step "7/7" "Remover banco de dados (opcional)"

set "RM_DB="
set /p "RM_DB=  Deseja REMOVER o banco '!DB_NAME!' do PostgreSQL? (S/N) [N]: "
if /i not "!RM_DB!"=="S" (
    call :skip "Banco !DB_NAME! mantido por decisao do usuario"
    goto :final
)

if not defined PSQL_BIN (
    for %%v in (17 16 15 14) do (
        if not defined PSQL_BIN if exist "C:\Program Files\PostgreSQL\%%v\bin\psql.exe" (
            set "PSQL_BIN=C:\Program Files\PostgreSQL\%%v\bin\psql.exe"
        )
    )
)

if not defined PSQL_BIN (
    call :warn "psql nao encontrado. Remova o banco manualmente via pgAdmin."
    goto :final
)

if not defined DB_PASS (
    set /p "DB_PASS=  Senha do postgres: "
)

if defined DB_PASS (
    set "PGPASSWORD=!DB_PASS!"

    set "DB_EXISTS="
    for /f "delims=" %%d in ('"!PSQL_BIN!" -U postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname = ''!DB_NAME!'';" 2^>nul') do set "DB_EXISTS=%%d"
    set "DB_EXISTS=!DB_EXISTS: =!"
    if not "!DB_EXISTS!"=="1" (
        call :skip "Banco !DB_NAME! nao existe"
        set "PGPASSWORD="
        goto :final
    )

    REM Terminate active connections
    "!PSQL_BIN!" -U postgres -h localhost -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '!DB_NAME!' AND pid ^<^> pg_backend_pid();" >> "!LOG!" 2>&1

    REM Drop database
    "!PSQL_BIN!" -U postgres -h localhost -c "DROP DATABASE IF EXISTS !DB_NAME!;" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao remover banco !DB_NAME!"
    ) else (
        call :ok "Banco !DB_NAME! removido"
    )

    set "PGPASSWORD="
) else (
    call :warn "Sem senha — banco nao removido"
)

REM ── RESUMO FINAL ────────────────────────────────────────────────────────────
:final
echo.
call :hdr "REMOCAO CONCLUIDA"
echo.
echo   !G!Removidos: !C_OK!!N!    !C!Pulados: !C_SKIP!!N!    !Y!Alertas: !C_WARN!!N!
echo.

if defined BK_FILE (
    if exist "!BK_FILE!" (
        echo   !G!BACKUP DO BANCO:!N!  !BK_FILE!
        echo.
    )
)

echo   !W!COMPONENTES PRESERVADOS:!N!
echo   - PostgreSQL (servidor e servico)
echo   - IIS (role Web-Server)
echo   - NSSM, Node.js, Python (binarios)
if exist "C:\DinamicaBudget_backups" echo   - Backups em C:\DinamicaBudget_backups\
echo.
echo   Log: !LOG!
echo.
echo !C!════════════════════════════════════════════════════════════════!N!

>> "!LOG!" echo.
>> "!LOG!" echo === REMOCAO CONCLUIDA: OK=!C_OK! SKIP=!C_SKIP! WARN=!C_WARN! ===
>> "!LOG!" echo Fim: %date% %time%

endlocal
exit /b 0
