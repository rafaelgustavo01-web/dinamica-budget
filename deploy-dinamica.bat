@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title ══ Dinamica Budget — Instalador Nativo v3.0 ══

REM ============================================================================
REM  DINAMICA BUDGET — Instalador Nativo para Windows Server 2022
REM  Versao: 3.0 — Abril 2026
REM  Compativel: Windows Server 2019+ / Windows 10 21H2+
REM ============================================================================
REM  * Instala AUTOMATICAMENTE: Python 3.12, PostgreSQL 16, NSSM, URL Rewrite,
REM    ARR 3.0 — sem nenhuma intervencao manual
REM  * Se versao do Python for incompativel, desinstala e reinstala 3.12.x
REM  * Cada etapa detecta se ja foi concluida e pula automaticamente
REM  * Reexecucao segura (idempotente)
REM  * Ao final gera PENDENCIAS_MANUAIS.txt com acoes restantes
REM  * Log completo em logs\deploy-<timestamp>.log
REM ============================================================================

REM ── CONFIGURACAO ────────────────────────────────────────────────────────────
set "SRC=%~dp0"
if "!SRC:~-1!"=="\" set "SRC=!SRC:~0,-1!"
set "APP=C:\DinamicaBudget"
set "IIS_ROOT=C:\inetpub\DinamicaBudget"
set "IIS_SITE=DinamicaBudget"
set "IIS_POOL=DinamicaBudgetPool"
set "SVC=DinamicaBudgetAPI"
set "API_PORT=8000"
set "HTTP_PORT=80"
set "PG_SVC=postgresql-x64-16"
set "DB_NAME=dinamica_budget"
set "APPCMD=%windir%\System32\inetsrv\appcmd.exe"

REM ── LOGGING ─────────────────────────────────────────────────────────────────
set "LOGD=!SRC!\logs"
if not exist "!LOGD!" mkdir "!LOGD!"
set "TS=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TS=!TS: =0!"
set "TS=!TS:/=!"
set "TS=!TS::=!"
set "TS=!TS:,=!"
if not defined TS set "TS=%RANDOM%_%RANDOM%"
set "LOG=!LOGD!\deploy-!TS!.log"
set "PENDF=!LOGD!\PENDENCIAS_MANUAIS_!TS!.txt"

REM ── CONTADORES ──────────────────────────────────────────────────────────────
set /a "C_OK=0, C_SKIP=0, C_WARN=0, C_FAIL=0, PEND=0"

REM ── FLAGS ───────────────────────────────────────────────────────────────────
set "HAS_NSSM=0"
set "HAS_PSQL=0"
set "HAS_PG=0"
set "HAS_REWRITE=0"
set "HAS_ARR=0"
set "NEEDS_ENV=1"
set "PSQL_BIN="
set "PY="

REM ── ANSI ESCAPE ─────────────────────────────────────────────────────────────
set "ESC="
for /f "delims=" %%a in ('echo prompt $E ^| cmd 2^>nul') do set "ESC=%%a"
if defined ESC (
    set "G=!ESC![92m" & set "C=!ESC![96m" & set "Y=!ESC![93m"
    set "R=!ESC![91m" & set "W=!ESC![97m" & set "B=!ESC![1m" & set "N=!ESC![0m"
) else (
    set "G=" & set "C=" & set "Y=" & set "R=" & set "W=" & set "B=" & set "N="
)
goto :main

REM ═══════════════════════════════════════════════════════════════════════════
REM  FUNCOES AUXILIARES
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

:info
echo   [INFO] %~1
>> "!LOG!" echo [%date% %time%] [INFO] %~1
goto :eof

:warn
set /a "C_WARN+=1"
echo   !Y![WARN]!N! %~1
>> "!LOG!" echo [%date% %time%] [WARN] %~1
goto :eof

:pend
set /a "PEND+=1"
set "P_!PEND!=%~1"
>> "!LOG!" echo [%date% %time%] [PEND] %~1
goto :eof

:write_pend
if !PEND! equ 0 goto :eof
(
echo ================================================================
echo  PENDENCIAS MANUAIS - Dinamica Budget
echo  Gerado em: %date% %time%
echo ================================================================
echo.
for /l %%i in (1,1,!PEND!) do echo  %%i. !P_%%i!
echo.
echo ================================================================
) > "!PENDF!"
goto :eof

REM ═══════════════════════════════════════════════════════════════════════════
:main
REM ═══════════════════════════════════════════════════════════════════════════

call :hdr "DINAMICA BUDGET — INSTALADOR NATIVO v3.0"
>> "!LOG!" echo Inicio: %date% %time%
>> "!LOG!" echo Origem: !SRC!
>> "!LOG!" echo Destino: !APP!
call :info "Origem:  !SRC!"
call :info "Destino: !APP!"
call :info "Log:     !LOG!"

REM ─── PREFLIGHT ──────────────────────────────────────────────────────────────
call :step "0/11" "Verificacao de pre-requisitos"

REM Admin check
net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo   !R![ERRO]!N! Execute este script como Administrador.
    echo          Clique direito no arquivo ^> Executar como administrador
    >> "!LOG!" echo [FAIL] Nao executado como Administrador
    exit /b 1
)
call :ok "Executando como Administrador"

REM OS check
set "WIN_BUILD="
for /f "tokens=3" %%b in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild 2^>nul ^| findstr CurrentBuild') do set "WIN_BUILD=%%b"
if not defined WIN_BUILD set "WIN_BUILD=0"
if !WIN_BUILD! geq 20348 (
    call :ok "Windows Server 2022 (Build !WIN_BUILD!)"
) else (
    if !WIN_BUILD! geq 17763 (
        call :warn "Build !WIN_BUILD! (Server 2019). Recomendado: Server 2022 (20348+)"
    ) else (
        call :warn "Build !WIN_BUILD! abaixo do recomendado (20348+)"
    )
)

REM Python check — instala 3.12 automaticamente se ausente ou versao incorreta
set "PY_NEED_INSTALL=0"
set "PY_VER="
where python >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
)
REM Verifica se e exatamente 3.12.x
echo !PY_VER! | findstr /r "^3\.12\." >nul 2>&1
if errorlevel 1 set "PY_NEED_INSTALL=1"
if not defined PY_VER set "PY_NEED_INSTALL=1"

if "!PY_NEED_INSTALL!"=="1" (
    if defined PY_VER (
        call :warn "Python !PY_VER! incompativel. Desinstalando e instalando Python 3.12.x..."
        REM Desinstala versao atual via registro (silencioso)
        for /f "tokens=*" %%g in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Python" 2^>nul ^| findstr /i "python 3\."') do (
            for /f "tokens=2*" %%a in ('reg query "%%g" /v UninstallString 2^>nul ^| findstr UninstallString') do (
                "%%b" /quiet /norestart >nul 2>&1
            )
        )
        for /f "tokens=*" %%g in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Python" 2^>nul ^| findstr /i "python 3\."') do (
            for /f "tokens=2*" %%a in ('reg query "%%g" /v UninstallString 2^>nul ^| findstr UninstallString') do (
                "%%b" /quiet /norestart >nul 2>&1
            )
        )
        call :info "Versao anterior desinstalada."
    ) else (
        call :info "Python nao encontrado. Instalando Python 3.12.10..."
    )
    REM Download Python 3.12.10 e instala silenciosamente
    set "PY_MSI=%TEMP%\python-3.12.10-amd64.exe"
    call :info "Baixando Python 3.12.10 (~25MB)..."
    powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '!PY_MSI!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
    if not exist "!PY_MSI!" (
        echo   !R![FAIL]!N! Nao foi possivel baixar Python 3.12.10. Verifique conexao com internet.
        >> "!LOG!" echo [FAIL] Download Python 3.12.10 falhou
        goto :abort
    )
    call :info "Instalando Python 3.12.10 (silencioso)..."
    "!PY_MSI!" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1 >> "!LOG!" 2>&1
    if errorlevel 1 (
        echo   !R![FAIL]!N! Falha ao instalar Python 3.12.10.
        >> "!LOG!" echo [FAIL] Instalacao Python 3.12.10 falhou
        goto :abort
    )
    REM Recarrega PATH para encontrar o Python recem instalado
    for /f "skip=2 tokens=3*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%a %%b"
    for /f "skip=2 tokens=3*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%a %%b"
    set "PATH=!SYS_PATH!;!USR_PATH!"
    REM Garante que Python 3.12 esta no PATH (caminhos padrao do instalador EDB)
    for %%p in ("C:\Python312" "C:\Program Files\Python312" "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312") do (
        if exist "%%~p\python.exe" (
            set "PATH=%%~p;%%~p\Scripts;!PATH!"
        )
    )
    REM Apaga venv antigo incompativel se existir
    if exist "!APP!\venv" (
        call :info "Removendo venv antigo incompativel com nova versao do Python..."
        rmdir /s /q "!APP!\venv" >> "!LOG!" 2>&1
    )
    call :ok "Python 3.12.10 instalado com sucesso"
    set "PY_VER=3.12.10"
) else (
    call :ok "Python !PY_VER!"
)

REM pip check — usa python -m pip se pip nao estiver no PATH
where pip >nul 2>&1
if errorlevel 1 (
    python -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo   !R![FAIL]!N! pip nao encontrado.
        >> "!LOG!" echo [FAIL] pip nao encontrado
        goto :abort
    )
)
call :ok "pip disponivel"

REM Node.js check — instala automaticamente se ausente
where node >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%v in ('node --version 2^>^&1') do set "NODE_VER=%%v"
    call :ok "Node.js !NODE_VER!"
) else (
    call :info "Node.js nao encontrado. Baixando Node.js 20 LTS..."
    set "NODE_MSI=%TEMP%\node-v20-lts-x64.msi"
    powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ver=(Invoke-RestMethod -Uri 'https://nodejs.org/dist/latest-v20.x/SHASUMS256.txt' -UseBasicParsing -ErrorAction Stop).Split([char]10) | Where-Object {$_ -match 'node-v[\d.]+-x64.msi'} | Select-Object -First 1; $fname=($ver -split '\s+')[1].Trim(); Invoke-WebRequest -Uri \"https://nodejs.org/dist/latest-v20.x/$fname\" -OutFile '!NODE_MSI!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
    if not exist "!NODE_MSI!" (
        REM URL fixa como fallback
        powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.19.1/node-v20.19.1-x64.msi' -OutFile '!NODE_MSI!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
    )
    if exist "!NODE_MSI!" (
        call :info "Instalando Node.js 20 LTS (silencioso)..."
        msiexec /i "!NODE_MSI!" /qn /norestart >> "!LOG!" 2>&1
        REM Recarrega PATH
        for /f "skip=2 tokens=3*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%a %%b"
        set "PATH=!SYS_PATH!;!PATH!"
        where node >nul 2>&1
        if errorlevel 1 (
            REM Adiciona path padrao manualmente
            if exist "C:\Program Files\nodejs\node.exe" set "PATH=C:\Program Files\nodejs;!PATH!"
        )
        where node >nul 2>&1
        if not errorlevel 1 (
            for /f "delims=" %%v in ('node --version 2^>^&1') do set "NODE_VER=%%v"
            call :ok "Node.js !NODE_VER! instalado automaticamente"
        ) else (
            echo   !R![FAIL]!N! Node.js instalado mas nao encontrado no PATH.
            call :pend "Reiniciar o script apos adicionar Node.js ao PATH ou reiniciar o servidor"
            goto :abort
        )
    ) else (
        echo   !R![FAIL]!N! Download do Node.js falhou. Verifique conexao com internet.
        >> "!LOG!" echo [FAIL] Download Node.js falhou
        call :pend "Instalar Node.js 20/22 LTS: https://nodejs.org/"
        goto :abort
    )
)

REM npm check
where npm >nul 2>&1
if not errorlevel 1 (
    call :ok "npm disponivel"
) else (
    REM npm vem com Node.js — adiciona caminho padrao
    if exist "C:\Program Files\nodejs\npm.cmd" (
        set "PATH=C:\Program Files\nodejs;!PATH!"
        call :ok "npm encontrado em C:\Program Files\nodejs"
    ) else (
        echo   !R![FAIL]!N! npm nao encontrado. Reinstale o Node.js.
        >> "!LOG!" echo [FAIL] npm nao encontrado
        goto :abort
    )
)

REM NSSM check — baixa automaticamente se ausente
set "NSSM_BIN="
where nssm >nul 2>&1
if not errorlevel 1 (
    set "HAS_NSSM=1"
    call :ok "NSSM disponivel no PATH"
) else (
    if exist "C:\Windows\System32\nssm.exe" (
        set "HAS_NSSM=1"
        set "NSSM_BIN=C:\Windows\System32\nssm.exe"
        call :ok "NSSM encontrado em System32"
    ) else (
        call :info "NSSM nao encontrado. Baixando NSSM 2.24..."
        powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip' -OutFile '%TEMP%\nssm.zip' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
        if exist "%TEMP%\nssm.zip" (
            powershell -NoProfile -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force" >> "!LOG!" 2>&1
            copy /y "%TEMP%\nssm\nssm-2.24-101-g897c7ad\win64\nssm.exe" "C:\Windows\System32\nssm.exe" >nul 2>&1
            if exist "C:\Windows\System32\nssm.exe" (
                set "HAS_NSSM=1"
                set "NSSM_BIN=C:\Windows\System32\nssm.exe"
                call :ok "NSSM 2.24 instalado automaticamente"
            ) else (
                set "HAS_NSSM=0"
                call :warn "NSSM nao pode ser copiado para System32. Tentando pasta do app..."
                if not exist "!APP!" mkdir "!APP!"
                copy /y "%TEMP%\nssm\nssm-2.24-101-g897c7ad\win64\nssm.exe" "!APP!\nssm.exe" >nul 2>&1
                if exist "!APP!\nssm.exe" (
                    set "HAS_NSSM=1"
                    set "NSSM_BIN=!APP!\nssm.exe"
                    call :ok "NSSM em !APP!\nssm.exe"
                ) else (
                    call :warn "NSSM nao disponivel. Servico Windows nao sera criado automaticamente."
                    call :pend "Instalar NSSM 2.24+: https://nssm.cc/download — copiar nssm.exe (win64) para C:\Windows\System32"
                )
            )
        ) else (
            set "HAS_NSSM=0"
            call :warn "Download do NSSM falhou. Servico nao sera criado."
            call :pend "Instalar NSSM 2.24+: https://nssm.cc/download — copiar nssm.exe (win64) para C:\Windows\System32"
        )
    )
)

REM IIS check — usa goto para evitar bloco parentizado com echo de parens
call :info "Verificando IIS..."
if exist "%APPCMD%" goto :iis_found
>> "!LOG!" echo [FAIL] IIS nao instalado - appcmd nao em %APPCMD%
echo   !R![FAIL]!N! IIS nao instalado. appcmd.exe nao encontrado.
echo          Execute: Install-WindowsFeature Web-Server -IncludeManagementTools
call :pend "Instalar IIS: Install-WindowsFeature Web-Server -IncludeManagementTools"
goto :abort
:iis_found
call :ok "IIS instalado"

REM URL Rewrite check
if exist "%windir%\System32\inetsrv\rewrite.dll" goto :rw_ok
call :info "URL Rewrite ausente. Instalando automaticamente..."
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://download.microsoft.com/download/1/2/8/128E2E22-C1B9-44A4-BE2A-5859ED1D4592/rewrite_amd64_en-US.msi' -OutFile '%TEMP%\urlrewrite.msi' -UseBasicParsing" >> "!LOG!" 2>&1
if exist "%TEMP%\urlrewrite.msi" msiexec /i "%TEMP%\urlrewrite.msi" /qn /norestart >> "!LOG!" 2>&1
if exist "%windir%\System32\inetsrv\rewrite.dll" goto :rw_ok
set "HAS_REWRITE=0"
call :warn "URL Rewrite 2.1 instalacao automatica falhou. Reverse proxy nao funcionara."
call :pend "Instalar URL Rewrite 2.1 manualmente: https://www.iis.net/downloads/microsoft/url-rewrite"
goto :rw_done
:rw_ok
set "HAS_REWRITE=1"
call :ok "URL Rewrite 2.1 disponivel"
:rw_done

REM ARR check — deteccao multi-ponto antes de instalar
if exist "%windir%\System32\inetsrv\requestRouter.dll" goto :arr_ok
REM Verifica via IIS modules (ARR pode estar instalado sem DLL no caminho padrao)
"%APPCMD%" list modules 2>nul | findstr /i "requestRouter" >nul 2>&1
if not errorlevel 1 goto :arr_ok
REM Verifica via registro de instalacao
reg query "HKLM\SOFTWARE\Microsoft\IIS Extensions\Application Request Routing" >nul 2>&1
if not errorlevel 1 goto :arr_ok
call :info "ARR 3.0 ausente. Instalando automaticamente..."

REM Estrategia 1: WebPI ja instalado no sistema — tenta direto
set "WEBPICMD="
for %%p in ("C:\Program Files\Microsoft\Web Platform Installer\WebpiCmd-x64.exe" "C:\Program Files\Microsoft\Web Platform Installer\WebpiCmd.exe" "C:\Program Files (x86)\Microsoft\Web Platform Installer\WebpiCmd.exe") do (
    if not defined WEBPICMD if exist "%%~p" set "WEBPICMD=%%~p"
)
if not defined WEBPICMD where WebpiCmd >nul 2>&1
if not defined WEBPICMD if not errorlevel 1 set "WEBPICMD=WebpiCmd"
if defined WEBPICMD goto :arr_use_webpi

REM Estrategia 2: Baixar WebPI e instalar (aguarda conclusao real com Start-Process -Wait)
call :info "Baixando Web Platform Installer (~1.5MB)..."
set "WEBPI_MSI=%TEMP%\WebPI51.msi"
powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://download.microsoft.com/download/C/F/F/CFF3A0B8-99D4-41A2-AE1A-496C08BEB904/WebPlatformInstaller_amd64_en-US.msi' -OutFile '!WEBPI_MSI!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
if not exist "!WEBPI_MSI!" goto :arr_msi_direct
call :info "Instalando WebPI (aguardando conclusao)..."
REM Start-Process -Wait garante que msiexec termina antes de continuar
powershell -NoProfile -Command "Start-Process msiexec -ArgumentList '/i','!WEBPI_MSI!','/qn','/norestart' -Wait -NoNewWindow -PassThru | Out-Null" >> "!LOG!" 2>&1
REM Aguarda ate 45s pelo WebpiCmd aparecer no disco
set "_W=0"
:arr_wait_webpi
for %%p in ("C:\Program Files\Microsoft\Web Platform Installer\WebpiCmd-x64.exe" "C:\Program Files\Microsoft\Web Platform Installer\WebpiCmd.exe") do (
    if not defined WEBPICMD if exist "%%~p" set "WEBPICMD=%%~p"
)
if defined WEBPICMD goto :arr_use_webpi
set /a "_W+=3"
if !_W! lss 45 (
    timeout /t 3 /nobreak >nul 2>&1
    goto :arr_wait_webpi
)
goto :arr_msi_direct

:arr_use_webpi
call :info "Instalando ARR 3.0 via WebPI..."
for %%prod in (ARR ARRv3_0 IISApplicationRequestRouting3) do (
    if not exist "%windir%\System32\inetsrv\requestRouter.dll" (
        "!WEBPICMD!" /Install /Products:%%prod /AcceptEULA /SuppressReboot >> "!LOG!" 2>&1
    )
)
if exist "%windir%\System32\inetsrv\requestRouter.dll" goto :arr_ok

:arr_msi_direct
REM Estrategia 3: MSI direto
call :info "Tentando MSI direto do ARR 3.0..."
set "ARR_MSI=%TEMP%\arr3_amd64.msi"
powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://download.microsoft.com/download/E/9/8/E9849D6A-020E-47E4-9FD0-A023E99B54EB/requestRouter_amd64.msi' -OutFile '!ARR_MSI!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
if exist "!ARR_MSI!" (
    powershell -NoProfile -Command "Start-Process msiexec -ArgumentList '/i','!ARR_MSI!','/qn','/norestart' -Wait -NoNewWindow" >> "!LOG!" 2>&1
    if exist "%windir%\System32\inetsrv\requestRouter.dll" goto :arr_ok
)
set "HAS_ARR=0"
call :warn "ARR 3.0 instalacao automatica falhou. Reverse proxy nao funcionara."
call :pend "Instalar ARR 3.0 manualmente: https://www.iis.net/downloads/microsoft/application-request-routing"
goto :arr_done
:arr_ok
set "HAS_ARR=1"
call :ok "ARR 3.0 disponivel"
:arr_done

REM PostgreSQL service check
call :info "Entrando no check do PostgreSQL..."
sc query "!PG_SVC!" >nul 2>&1
if errorlevel 1 (
    REM Try other service names
    set "PG_FOUND=0"
    for %%s in (postgresql-x64-17 postgresql-x64-16 postgresql-x64-15 postgresql-x64-14) do (
        if "!PG_FOUND!"=="0" (
            sc query "%%s" >nul 2>&1
            if not errorlevel 1 (
                set "PG_SVC=%%s"
                set "PG_FOUND=1"
            )
        )
    )
    if "!PG_FOUND!"=="0" (
        call :info "PostgreSQL nao encontrado. Baixando PostgreSQL 16 (~300MB)..."

        REM Tenta winget primeiro (mais rapido)
        set "PG_INSTALLED=0"
        where winget >nul 2>&1
        if not errorlevel 1 (
            call :info "Tentando instalar via winget..."
            winget install EDB.PostgreSQL.16 --silent --accept-package-agreements --accept-source-agreements --override "/S" >> "!LOG!" 2>&1
            for %%s in (postgresql-x64-16 postgresql-x64-17 postgresql-x64-15) do (
                if "!PG_INSTALLED!"=="0" (
                    sc query "%%s" >nul 2>&1
                    if not errorlevel 1 (
                        set "PG_SVC=%%s"
                        set "PG_INSTALLED=1"
                    )
                )
            )
        )

        if "!PG_INSTALLED!"=="0" (
            REM Download instalador EDB direto
            set "PG_INST=%TEMP%\postgresql-16-installer.exe"
            call :info "Baixando instalador EDB PostgreSQL 16..."
            powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://sbp.enterprisedb.com/getfile.jsp?fileid=1258893' -OutFile '!PG_INST!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
            if not exist "!PG_INST!" (
                REM URL alternativa via get.enterprisedb.com
                powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://get.enterprisedb.com/postgresql/postgresql-16.6-1-windows-x64.exe' -OutFile '!PG_INST!' -UseBasicParsing; exit 0}catch{exit 1}" >> "!LOG!" 2>&1
            )
            if exist "!PG_INST!" (
                call :info "Instalando PostgreSQL 16 (silencioso, pode levar 2-3 min)..."
                REM Instala em modo unattended com senha 'postgres' para o superuser
                REM A senha sera sobrescrita depois pelo .env
                "!PG_INST!" --mode unattended --superpassword "PostgresSetup123!" --serverport 5432 --servicename "postgresql-x64-16" --serviceaccount "NT AUTHORITY\NetworkService" >> "!LOG!" 2>&1
                REM Aguarda servico iniciar
                timeout /t 8 /nobreak >nul 2>&1
                for %%s in (postgresql-x64-16 postgresql-x64-17 postgresql-x64-15) do (
                    if "!PG_INSTALLED!"=="0" (
                        sc query "%%s" >nul 2>&1
                        if not errorlevel 1 (
                            set "PG_SVC=%%s"
                            set "PG_INSTALLED=1"
                        )
                    )
                )
                if "!PG_INSTALLED!"=="1" (
                    call :ok "PostgreSQL 16 instalado com sucesso"
                    set "PG_FOUND=1"
                    set "PG_DEFAULT_PASS=PostgresSetup123!"
                ) else (
                    call :warn "PostgreSQL instalado mas servico nao encontrado ainda. Tentando localizar..."
                    for %%v in (17 16 15 14) do (
                        if exist "C:\Program Files\PostgreSQL\%%v\bin\pg_ctl.exe" (
                            if "!PG_INSTALLED!"=="0" (
                                set "PG_INSTALLED=1"
                                set "PG_SVC=postgresql-x64-%%v"
                                set "PG_FOUND=1"
                                set "PG_DEFAULT_PASS=PostgresSetup123!"
                                call :ok "PostgreSQL %%v encontrado em C:\Program Files\PostgreSQL\%%v"
                            )
                        )
                    )
                )
            ) else (
                call :warn "Download do PostgreSQL falhou. Verifique conexao com internet."
            )
        ) else (
            set "PG_FOUND=1"
            call :ok "PostgreSQL instalado via winget"
        )

        if "!PG_FOUND!"=="0" (
            set "HAS_PG=0"
            call :warn "PostgreSQL nao instalado. Etapas de banco serao puladas."
            call :pend "Instalar PostgreSQL 16: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads"
        ) else (
            set "HAS_PG=1"
        )
    ) else (
        set "HAS_PG=1"
    )
) else (
    set "HAS_PG=1"
)

if "!HAS_PG!"=="1" (
    for /f "tokens=4" %%s in ('sc query "!PG_SVC!" ^| findstr /i STATE') do set "PG_STATE=%%s"
    if /i "!PG_STATE!"=="RUNNING" (
        call :ok "PostgreSQL (!PG_SVC!) rodando"
    ) else (
        call :info "Tentando iniciar !PG_SVC!..."
        net start "!PG_SVC!" >> "!LOG!" 2>&1
        set "NET_RC=!ERRORLEVEL!"
        REM "ja foi iniciado" (NET HELPMSG 2182) retorna codigo 2 — tratar como sucesso
        if !NET_RC! equ 0 (
            call :ok "PostgreSQL (!PG_SVC!) iniciado"
        ) else if !NET_RC! equ 2 (
            call :ok "PostgreSQL (!PG_SVC!) ja estava rodando"
        ) else (
            REM Verifica o estado real antes de desistir
            for /f "tokens=4" %%s in ('sc query "!PG_SVC!" ^| findstr /i STATE') do set "PG_STATE2=%%s"
            if /i "!PG_STATE2!"=="RUNNING" (
                call :ok "PostgreSQL (!PG_SVC!) rodando (verificado)"
            ) else (
                set "HAS_PG=0"
                call :warn "Falha ao iniciar !PG_SVC! (codigo !NET_RC!). Etapas de banco serao puladas."
                call :pend "Iniciar PostgreSQL manualmente: net start !PG_SVC!"
            )
        )
    )
)

REM Find psql binary
for %%v in (17 16 15 14) do (
    if not defined PSQL_BIN if exist "C:\Program Files\PostgreSQL\%%v\bin\psql.exe" (
        set "PSQL_BIN=C:\Program Files\PostgreSQL\%%v\bin\psql.exe"
    )
)
if not defined PSQL_BIN (
    for /f "delims=" %%p in ('where psql 2^>nul') do if not defined PSQL_BIN set "PSQL_BIN=%%p"
)
if defined PSQL_BIN (
    set "HAS_PSQL=1"
    call :ok "psql encontrado"
) else (
    if "!HAS_PG!"=="1" (
        call :warn "psql nao encontrado. Banco/extensoes devem ser criados manualmente."
        call :pend "Adicionar PostgreSQL bin ao PATH ou criar banco manualmente via pgAdmin"
    )
)

REM Source files check
for %%f in (requirements.txt alembic.ini .env.example) do (
    if not exist "!SRC!\%%f" (
        echo   !R![FAIL]!N! Arquivo ausente na origem: %%f
        >> "!LOG!" echo [FAIL] Arquivo ausente: %%f
        goto :abort
    )
)
if not exist "!SRC!\app\main.py" (
    echo   !R![FAIL]!N! Arquivo ausente: app\main.py
    >> "!LOG!" echo [FAIL] app\main.py ausente
    goto :abort
)
if not exist "!SRC!\frontend\package.json" (
    echo   !R![FAIL]!N! Arquivo ausente: frontend\package.json
    >> "!LOG!" echo [FAIL] frontend\package.json ausente
    goto :abort
)
call :ok "Arquivos de origem validados"

REM Detect install mode
if exist "!APP!\venv\Scripts\python.exe" (
    call :info "Modo: ATUALIZACAO (instalacao existente detectada)"
) else (
    call :info "Modo: INSTALACAO INICIAL"
)

REM ─── ETAPA 1/11: SINCRONIZAR ARQUIVOS ──────────────────────────────────────
call :step "1/11" "Sincronizar arquivos do projeto"
if not exist "!APP!" mkdir "!APP!"
robocopy "!SRC!" "!APP!" /MIR /R:2 /W:2 /NFL /NDL /NP /XD ".git" "node_modules" "venv" ".venv" "logs" "output" "__pycache__" ".mypy_cache" ".pytest_cache" >> "!LOG!" 2>&1
set "RC=!ERRORLEVEL!"
if !RC! gtr 7 (
    call :warn "Robocopy retornou codigo !RC! (possivel falha parcial)"
    call :pend "Verificar sincronizacao de arquivos em !APP! — robocopy codigo !RC!"
) else (
    call :ok "Projeto sincronizado para !APP!"
)

REM ─── ETAPA 2/11: AMBIENTE VIRTUAL PYTHON ───────────────────────────────────
call :step "2/11" "Ambiente virtual Python e dependencias"

REM Verifica se venv existente e compativel com Python 3.12
set "VENV_OK=0"
if exist "!APP!\venv\Scripts\python.exe" (
    for /f "tokens=2" %%v in ('"!APP!\venv\Scripts\python.exe" --version 2^>^&1') do set "VENV_PY=%%v"
    echo !VENV_PY! | findstr /r "^3\.12\." >nul 2>&1
    if not errorlevel 1 set "VENV_OK=1"
)

if "!VENV_OK!"=="1" (
    call :skip "venv ja existe e e compativel (Python !VENV_PY!)"
) else (
    if exist "!APP!\venv" (
        call :info "Removendo venv incompativel..."
        rmdir /s /q "!APP!\venv" >> "!LOG!" 2>&1
    )
    call :info "Criando ambiente virtual Python 3.12..."
    python -m venv "!APP!\venv" >> "!LOG!" 2>&1
    if errorlevel 1 (
        echo   !R![FAIL]!N! Falha ao criar venv.
        >> "!LOG!" echo [FAIL] python -m venv falhou
        goto :abort
    )
    call :ok "Ambiente virtual criado"
)

set "PY=!APP!\venv\Scripts\python.exe"
set "PIP=!APP!\venv\Scripts\pip.exe"

call :info "Atualizando pip..."
"!PY!" -m pip install --upgrade pip >> "!LOG!" 2>&1

REM Certificar que o pip do venv funciona — fallback para python -m pip
if not exist "!PIP!" set "PIP=!PY! -m pip"

REM Instalar torch primeiro (separado para controlar versao por Python)
call :info "Instalando torch CPU para Python !PY_VER!..."
for /f "tokens=2 delims=." %%m in ("!PY_VER!") do set "PY_MINOR=%%m"
if !PY_MINOR! geq 13 (
    "!APP!\venv\Scripts\pip.exe" install "torch>=2.9.0" --index-url https://download.pytorch.org/whl/cpu >> "!LOG!" 2>&1
) else (
    "!APP!\venv\Scripts\pip.exe" install "torch>=2.5.1" --index-url https://download.pytorch.org/whl/cpu >> "!LOG!" 2>&1
)

REM Instalar dependencias por grupo para melhor controle de erros
call :info "Instalando dependencias Python (pode levar 5-10 min na 1a vez)..."

REM Grupo 1: core sem compilacao
"!APP!\venv\Scripts\pip.exe" install ^
    fastapi==0.115.5 ^
    "uvicorn[standard]==0.32.1" ^
    python-multipart==0.0.12 ^
    "sqlalchemy[asyncio]==2.0.36" ^
    alembic==1.14.0 ^
    pgvector==0.3.6 ^
    "pydantic==2.10.3" ^
    "pydantic-settings==2.6.1" ^
    "pydantic[email]==2.10.3" ^
    "passlib[bcrypt]==1.7.4" ^
    "bcrypt==4.0.1" ^
    "python-jose[cryptography]==3.3.0" ^
    slowapi==0.1.9 ^
    "sentence-transformers==3.3.1" ^
    structlog==24.4.0 ^
    python-dotenv==1.0.1 ^
    pytest==8.3.4 ^
    pytest-asyncio==0.24.0 ^
    httpx==0.28.1 ^
    pytest-cov==6.0.0 >> "!LOG!" 2>&1
set "RC1=!ERRORLEVEL!"

REM asyncpg: tenta wheel pre-compilado, senao compila
"!APP!\venv\Scripts\pip.exe" install asyncpg==0.30.0 >> "!LOG!" 2>&1
if errorlevel 1 (
    call :warn "asyncpg 0.30.0 falhou. Tentando versao mais recente..."
    "!APP!\venv\Scripts\pip.exe" install asyncpg >> "!LOG!" 2>&1
)

REM rapidfuzz: prefere wheel, nunca compila da fonte em ambiente restrito
call :info "Instalando rapidfuzz (wheel pre-compilado)..."
"!APP!\venv\Scripts\pip.exe" install "rapidfuzz>=3.10.0" --prefer-binary >> "!LOG!" 2>&1
if errorlevel 1 (
    call :warn "rapidfuzz preferred-binary falhou. Tentando versao sem restricao..."
    "!APP!\venv\Scripts\pip.exe" install rapidfuzz --prefer-binary >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "rapidfuzz nao instalado. Busca fuzzy ficara indisponivel."
        call :pend "Instalar rapidfuzz manualmente: venv\Scripts\pip install rapidfuzz --prefer-binary"
    ) else (
        call :ok "rapidfuzz instalado (versao mais recente)"
    )
) else (
    call :ok "rapidfuzz instalado"
)

REM pgcli: opcional, pode falhar sem C compiler
"!APP!\venv\Scripts\pip.exe" install pgcli==4.4.0 --prefer-binary >> "!LOG!" 2>&1
if errorlevel 1 (
    call :warn "pgcli nao instalado (opcional). Nao afeta funcionamento."
)

if !RC1! neq 0 (
    call :warn "Alguns pacotes core falharam. Tentando instalar tudo de uma vez como fallback..."
    "!APP!\venv\Scripts\pip.exe" install -r "!APP!\requirements.txt" --prefer-binary >> "!LOG!" 2>&1
    if errorlevel 1 (
        >> "!LOG!" echo [FAIL] pip install requirements.txt falhou
        echo   !R![FAIL]!N! Falha ao instalar dependencias Python.
        echo          Verifique conexao com internet e o log: !LOG!
        goto :abort
    )
)
call :ok "Dependencias Python instaladas"

REM ─── ETAPA 3/11: CONFIGURACAO .env ─────────────────────────────────────────
call :step "3/11" "Configuracao do arquivo .env"

REM Check if .env already configured
set "NEEDS_ENV=1"
if exist "!APP!\.env" (
    findstr "CHANGE_ME_use_secrets_token_hex_32" "!APP!\.env" >nul 2>&1
    if errorlevel 1 (
        set "NEEDS_ENV=0"
    ) else (
        call :info ".env existe mas contem SECRET_KEY padrao. Reconfigurando..."
    )
)

if "!NEEDS_ENV!"=="0" (
    call :skip ".env ja configurado"

    REM Valida campos obrigatorios e corrige senha placeholder automaticamente
    powershell -NoProfile -Command ^
      "$envFile='!APP!\.env'; $lines=Get-Content $envFile -Encoding UTF8; $changed=$false;" ^
      "$required=@('DATABASE_URL','SECRET_KEY','ROOT_USER_EMAIL','ROOT_USER_PASSWORD');" ^
      "foreach($k in $required){ $l=$lines|Where-Object{$_ -match '^'+$k+'='}; if(-not $l){ Write-Host '[WARN] Campo ausente no .env: '+$k } elseif(($l -split'=',2)[1] -match 'CHANGE_ME|your_password|placeholder'){ Write-Host '[WARN] '+$k+' tem valor placeholder.' } };" ^
      "$dbLine=$lines|Where-Object{$_ -match '^DATABASE_URL='};" ^
      "if($dbLine -and $dbLine -match '://[^:]+:(password|your_password)@' -and '!PG_DEFAULT_PASS!'){ $newLine=$dbLine -replace ':(password|your_password)@',':!PG_DEFAULT_PASS!@'; $lines=$lines -replace [regex]::Escape($dbLine),$newLine; Set-Content $envFile $lines -Encoding UTF8; Write-Host '[OK] Senha placeholder corrigida no .env ($newLine)'; $changed=$true };" ^
      "if(-not $changed){ Write-Host '[OK] .env validado' }" >> "!LOG!" 2>&1

    REM Parse DB password — usa arquivo temp para preservar caracteres especiais (ex: ! no final)
    powershell -NoProfile -Command "$c=(Get-Content '!APP!\.env') | Where-Object {$_ -match '^DATABASE_URL='}; if($c -match '://[^:]+:([^@]+)@'){$Matches[1] | Out-File -NoNewline -Encoding utf8 (Join-Path $env:TEMP '_dbp.tmp')}" >> "!LOG!" 2>&1
    setlocal DisableDelayedExpansion
    set "DB_PASS="
    if exist "%TEMP%\_dbp.tmp" for /f "usebackq delims=" %%x in ("%TEMP%\_dbp.tmp") do set "DB_PASS=%%x"
    endlocal & set "DB_PASS=%DB_PASS%"
    del "%TEMP%\_dbp.tmp" >nul 2>&1
    goto :etapa4
)

REM Copy template if .env doesn't exist
if not exist "!APP!\.env" (
    copy /y "!APP!\.env.example" "!APP!\.env" >nul 2>&1
)

echo.
echo   ============================================================
echo    CONFIGURACAO INTERATIVA DO SISTEMA
echo    Pressione ENTER para aceitar o valor padrao entre colchetes
echo   ============================================================
echo.

REM Prompt: PostgreSQL password
:prompt_pg
set "PG_PASS="
REM Se PostgreSQL foi instalado automaticamente, usa a senha padrao do instalador
if defined PG_DEFAULT_PASS (
    set "PG_PASS=!PG_DEFAULT_PASS!"
    call :info "Usando senha padrao do PostgreSQL instalado automaticamente."
    call :info "Voce pode alterar depois via pgAdmin ou ALTER USER postgres PASSWORD '...';"
) else (
    set /p "PG_PASS=  Senha do usuario 'postgres' no PostgreSQL: "
    if "!PG_PASS!"=="" (
        echo   A senha nao pode ser vazia.
        goto :prompt_pg
    )
)

REM Prompt: Admin email
set "ADMIN_EMAIL="
set /p "ADMIN_EMAIL=  Email do administrador [admin@empresa.local]: "
if "!ADMIN_EMAIL!"=="" set "ADMIN_EMAIL=admin@empresa.local"

REM Prompt: Admin password
:prompt_adm
set "ADMIN_PASS="
set /p "ADMIN_PASS=  Senha do administrador (min 8 caracteres): "
if "!ADMIN_PASS!"=="" (
    echo   A senha nao pode ser vazia.
    goto :prompt_adm
)

REM Prompt: Admin name
set "ADMIN_NAME="
set /p "ADMIN_NAME=  Nome do administrador [Administrador]: "
if "!ADMIN_NAME!"=="" set "ADMIN_NAME=Administrador"

REM Detect server IPs
set "SERVER_IP=127.0.0.1"
for /f "delims=" %%i in ('powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -First 1 -ExpandProperty IPAddress"') do set "SERVER_IP=%%i"

set "ACCESS_HOST="
set /p "ACCESS_HOST=  Hostname/IP para acesso dos usuarios [!SERVER_IP!]: "
if "!ACCESS_HOST!"=="" set "ACCESS_HOST=!SERVER_IP!"

REM Generate SECRET_KEY
for /f "delims=" %%k in ('"!PY!" -c "import secrets; print(secrets.token_hex(32))"') do set "SECRET_KEY=%%k"

call :info "Gerando .env..."
set "DB_PASS=!PG_PASS!"

REM Write .env file using PowerShell to handle special characters safely
powershell -NoProfile -Command ^
  "$content = @'" & echo. & ^
  echo # --- Database --- & ^
  echo DATABASE_URL=postgresql+asyncpg://postgres:!PG_PASS!@127.0.0.1:5432/dinamica_budget & ^
  echo DATABASE_POOL_SIZE=10 & ^
  echo DATABASE_MAX_OVERFLOW=20 & ^
  echo. & ^
  echo # --- JWT --- & ^
  echo SECRET_KEY=!SECRET_KEY! & ^
  echo ALGORITHM=HS256 & ^
  echo ACCESS_TOKEN_EXPIRE_MINUTES=30 & ^
  echo REFRESH_TOKEN_EXPIRE_DAYS=7 & ^
  echo. & ^
  echo # --- ML / Embeddings --- & ^
  echo EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2 & ^
  echo SENTENCE_TRANSFORMERS_HOME=C:/DinamicaBudget/ml_models & ^
  echo FUZZY_THRESHOLD=0.85 & ^
  echo SEMANTIC_THRESHOLD=0.65 & ^
  echo. & ^
  echo # --- App --- & ^
  echo API_V1_PREFIX=/api/v1 & ^
  echo DEBUG=false & ^
  echo LOG_LEVEL=INFO & ^
  echo APP_HOST=0.0.0.0 & ^
  echo APP_PORT=8000 & ^
  echo. & ^
  echo # --- Root User (auto-created on first startup) --- & ^
  echo ROOT_USER_EMAIL=!ADMIN_EMAIL! & ^
  echo ROOT_USER_PASSWORD=!ADMIN_PASS! & ^
  echo ROOT_USER_NAME=!ADMIN_NAME! & ^
  echo. & ^
  echo # --- CORS --- & ^
  echo ALLOWED_ORIGINS=["http://!ACCESS_HOST!","http://localhost","http://127.0.0.1"] & ^
  echo '@ & ^
  echo $content ^| Set-Content -Path '!APP!\.env' -Encoding UTF8 -Force" >> "!LOG!" 2>&1

if not exist "!APP!\.env" (
    REM Fallback: write .env line by line
    > "!APP!\.env" echo # --- Database ---
    >> "!APP!\.env" echo DATABASE_URL=postgresql+asyncpg://postgres:!PG_PASS!@127.0.0.1:5432/dinamica_budget
    >> "!APP!\.env" echo DATABASE_POOL_SIZE=10
    >> "!APP!\.env" echo DATABASE_MAX_OVERFLOW=20
    >> "!APP!\.env" echo.
    >> "!APP!\.env" echo # --- JWT ---
    >> "!APP!\.env" echo SECRET_KEY=!SECRET_KEY!
    >> "!APP!\.env" echo ALGORITHM=HS256
    >> "!APP!\.env" echo ACCESS_TOKEN_EXPIRE_MINUTES=30
    >> "!APP!\.env" echo REFRESH_TOKEN_EXPIRE_DAYS=7
    >> "!APP!\.env" echo.
    >> "!APP!\.env" echo # --- ML / Embeddings ---
    >> "!APP!\.env" echo EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
    >> "!APP!\.env" echo SENTENCE_TRANSFORMERS_HOME=C:/DinamicaBudget/ml_models
    >> "!APP!\.env" echo FUZZY_THRESHOLD=0.85
    >> "!APP!\.env" echo SEMANTIC_THRESHOLD=0.65
    >> "!APP!\.env" echo.
    >> "!APP!\.env" echo # --- App ---
    >> "!APP!\.env" echo API_V1_PREFIX=/api/v1
    >> "!APP!\.env" echo DEBUG=false
    >> "!APP!\.env" echo LOG_LEVEL=INFO
    >> "!APP!\.env" echo APP_HOST=0.0.0.0
    >> "!APP!\.env" echo APP_PORT=8000
    >> "!APP!\.env" echo.
    >> "!APP!\.env" echo # --- Root User ---
    >> "!APP!\.env" echo ROOT_USER_EMAIL=!ADMIN_EMAIL!
    >> "!APP!\.env" echo ROOT_USER_PASSWORD=!ADMIN_PASS!
    >> "!APP!\.env" echo ROOT_USER_NAME=!ADMIN_NAME!
    >> "!APP!\.env" echo.
    >> "!APP!\.env" echo # --- CORS ---
    >> "!APP!\.env" echo ALLOWED_ORIGINS=["http://!ACCESS_HOST!","http://localhost","http://127.0.0.1"]
)

call :ok ".env criado com SECRET_KEY gerada e credenciais configuradas"

REM ─── ETAPA 4/11: POSTGRESQL BANCO E EXTENSOES ──────────────────────────────
:etapa4
call :step "4/11" "PostgreSQL: banco de dados e extensoes"

if "!HAS_PG!"=="0" (
    call :skip "PostgreSQL nao disponivel. Configuracao manual necessaria."
    call :pend "Criar banco 'dinamica_budget' no PostgreSQL via pgAdmin"
    call :pend "Executar no banco: CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;"
    goto :etapa5
)

if "!HAS_PSQL!"=="0" (
    call :skip "psql nao encontrado. Banco e extensoes devem ser criados manualmente."
    call :pend "Criar banco 'dinamica_budget' via pgAdmin (owner: postgres)"
    call :pend "Executar no banco: CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;"
    goto :etapa5
)

REM Chama script PowerShell dedicado que le o .env diretamente
REM (evita problemas com ! @ # em senhas em variaveis batch)
REM O script tambem detecta e corrige automaticamente senha errada no .env
set "PG_SETUP_PS1=!SRC!\scripts\pg_setup.ps1"
if not exist "!PG_SETUP_PS1!" set "PG_SETUP_PS1=!APP!\scripts\pg_setup.ps1"

powershell -NoProfile -ExecutionPolicy Bypass -File "!PG_SETUP_PS1!" -EnvFile "!APP!\.env" -PsqlBin "!PSQL_BIN!" -DbName "!DB_NAME!" -SvcName "!PG_SVC!" >> "!LOG!" 2>&1
set "PG4_RC=!ERRORLEVEL!"

REM Relata resultado baseado nas linhas escritas no log
for /f "tokens=*" %%l in ('findstr /i "\[OK\]\|\[SKIP\]\|\[WARN\]\|\[FAIL\]\|\[PEND\]\|\[INFO\]" "%TEMP%\__ " 2^>nul') do rem
powershell -NoProfile -Command "$l=Get-Content '!LOG!' -Tail 20; $l | Where-Object {$_ -match '\[(OK|SKIP|WARN|FAIL|INFO|PEND)\]'} | ForEach-Object {Write-Host $_ }" 2>nul

if !PG4_RC! neq 0 (
    call :warn "Configuracao do banco falhou (codigo !PG4_RC!). Verifique o log."
    call :pend "Executar manualmente: powershell -File '!SRC!\scripts\pg_setup.ps1' -EnvFile '!APP!\.env'"
) else (
    call :ok "PostgreSQL: banco e extensoes configurados"
)

REM ─── pgvector: instala extensao de busca vetorial ───────────────────────────
REM Detecta se vector.control ja existe antes de tentar compilar
set "PG_CTRL=!PSQL_BIN:psql.exe=..!\share\extension\vector.control"
if not exist "!PG_CTRL!" set "PG_CTRL=C:\Program Files\PostgreSQL\16\share\extension\vector.control"

set "PGVEC_PS1=!SRC!\scripts\install-pgvector.ps1"
if not exist "!PGVEC_PS1!" set "PGVEC_PS1=!APP!\scripts\install-pgvector.ps1"

if exist "!PGVEC_PS1!" (
    call :info "Instalando/verificando pgvector (pode demorar se precisar compilar)..."
    powershell -NoProfile -ExecutionPolicy Bypass -File "!PGVEC_PS1!" ^
        -PgRoot "C:\Program Files\PostgreSQL\16" ^
        -DbName "!DB_NAME!" ^
        -EnvFile "!APP!\.env" ^
        -DeployDir "!APP!" >> "!LOG!" 2>&1
    set "PGV_RC=!ERRORLEVEL!"
    if !PGV_RC! neq 0 (
        call :warn "pgvector nao instalado (codigo !PGV_RC!). Busca vetorial sera desativada."
        call :pend "Executar apos deploy: powershell -File '!SRC!\scripts\install-pgvector.ps1'"
    ) else (
        call :ok "pgvector configurado (busca vetorial ativa)"
    )
) else (
    call :warn "install-pgvector.ps1 nao encontrado. Busca vetorial desativada."
    call :pend "Copiar scripts\install-pgvector.ps1 e executar manualmente."
)

REM ─── ETAPA 5/11: MIGRACOES ALEMBIC ─────────────────────────────────────────
:etapa5
call :step "5/11" "Migracoes de banco (Alembic)"

pushd "!APP!"
REM Usa o executavel alembic do venv diretamente (mais confiavel que python -m alembic)
set "ALEMBIC_EXE=!APP!\venv\Scripts\alembic.exe"
if not exist "!ALEMBIC_EXE!" set "ALEMBIC_EXE=!APP!\venv\Scripts\alembic"
"!ALEMBIC_EXE!" upgrade head >> "!LOG!" 2>&1
set "ARC=!ERRORLEVEL!"
popd

if !ARC! neq 0 (
    call :warn "Alembic upgrade head falhou (codigo !ARC!)."
    call :info "Causas comuns: PostgreSQL parado, banco nao criado, extensoes ausentes."
    call :pend "Executar manualmente: cd !APP! ^&^& venv\Scripts\alembic.exe upgrade head"
) else (
    call :ok "Migracoes aplicadas com sucesso"
)

REM ─── ETAPA 6/11: MODELO ML ─────────────────────────────────────────────────
call :step "6/11" "Modelo de Machine Learning"

set "ML_DIR=!APP!\ml_models"
set "ML_MODEL_DIR=!ML_DIR!\models--sentence-transformers--all-MiniLM-L6-v2"

if exist "!ML_MODEL_DIR!\snapshots" (
    call :skip "Modelo all-MiniLM-L6-v2 ja presente em ml_models/"
    goto :etapa7
)

REM Check if model dir has any content (might be partially downloaded)
if exist "!ML_MODEL_DIR!" (
    call :info "Diretorio do modelo existe mas pode estar incompleto"
)

REM Check internet connectivity
set "HAS_NET=0"
powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;$null=Invoke-WebRequest -Uri 'https://huggingface.co' -TimeoutSec 5 -UseBasicParsing;exit 0}catch{exit 1}" >nul 2>&1
if !ERRORLEVEL! equ 0 set "HAS_NET=1"

if "!HAS_NET!"=="1" (
    call :info "Internet disponivel. Baixando modelo ML (~90MB, pode levar alguns minutos)..."
    if not exist "!ML_DIR!" mkdir "!ML_DIR!"
    "!PY!" -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('all-MiniLM-L6-v2',cache_folder=r'!ML_DIR!'); print('OK')" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Download do modelo ML falhou."
        call :pend "Baixar modelo ML em maquina com internet e copiar para !ML_DIR! (ver secao 6.5 do manual)"
    ) else (
        call :ok "Modelo ML baixado com sucesso"
    )
) else (
    call :warn "Sem acesso a internet. Modelo ML nao pode ser baixado automaticamente."
    call :pend "MODELO ML: Em maquina com internet, executar: python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2',cache_folder='./ml_models')\""
    call :pend "MODELO ML: Copiar pasta ml_models/ para !ML_DIR!"
)

REM ─── ETAPA 7/11: BUILD DO FRONTEND ─────────────────────────────────────────
:etapa7
call :step "7/11" "Build do frontend React"

REM Create frontend .env.production
> "!APP!\frontend\.env.production" echo VITE_API_URL=/api/v1
call :ok "frontend/.env.production criado"

pushd "!APP!\frontend"

call :info "Instalando dependencias npm..."
call npm install >> "!LOG!" 2>&1
if errorlevel 1 (
    popd
    call :warn "npm install falhou."
    call :pend "Executar manualmente: cd !APP!\frontend && npm install && npm run build"
    goto :etapa8
)
call :ok "npm install concluido"

call :info "Gerando build de producao..."
call npm run build >> "!LOG!" 2>&1
if errorlevel 1 (
    popd
    call :warn "npm run build falhou."
    call :pend "Executar manualmente: cd !APP!\frontend && npm run build"
    goto :etapa8
)
popd

if not exist "!APP!\frontend\dist\index.html" (
    call :warn "Build nao gerou dist/index.html"
    call :pend "Verificar build do frontend: cd !APP!\frontend && npm run build"
    goto :etapa8
)
call :ok "Build de producao gerado"

REM Copy to IIS webroot
if not exist "!IIS_ROOT!" mkdir "!IIS_ROOT!"
robocopy "!APP!\frontend\dist" "!IIS_ROOT!" /MIR /R:2 /W:2 /NFL /NDL /NP >> "!LOG!" 2>&1
set "RC=!ERRORLEVEL!"
if !RC! gtr 7 (
    call :warn "Falha ao copiar frontend para IIS (robocopy !RC!)"
    call :pend "Copiar manualmente: robocopy !APP!\frontend\dist !IIS_ROOT! /MIR"
) else (
    call :ok "Frontend copiado para !IIS_ROOT!"
)

REM ─── ETAPA 8/11: CONFIGURACAO DO IIS ───────────────────────────────────────
:etapa8
call :step "8/11" "Configuracao do IIS"

REM Ensure IIS features installed
powershell -NoProfile -Command "Install-WindowsFeature Web-Server,Web-Default-Doc,Web-Static-Content,Web-Http-Logging,Web-Stat-Compression,Web-Filtering -IncludeManagementTools -ErrorAction SilentlyContinue | Out-Null" >> "!LOG!" 2>&1

REM Create app pool (skip if exists)
"!APPCMD!" list apppool "!IIS_POOL!" >nul 2>&1
if errorlevel 1 (
    "!APPCMD!" add apppool /name:"!IIS_POOL!" >> "!LOG!" 2>&1
    "!APPCMD!" set apppool "!IIS_POOL!" /managedRuntimeVersion:"" >> "!LOG!" 2>&1
    call :ok "App pool !IIS_POOL! criado (No Managed Code)"
) else (
    call :skip "App pool !IIS_POOL! ja existe"
)

REM Stop Default Web Site if bound to port 80
"!APPCMD!" list site "Default Web Site" 2>nul | findstr /i "http/*:80:" >nul 2>&1
if not errorlevel 1 (
    "!APPCMD!" stop site "Default Web Site" >> "!LOG!" 2>&1
    call :info "Default Web Site parado (porta 80 liberada)"
)

REM Create or update site
"!APPCMD!" list site "!IIS_SITE!" >nul 2>&1
if errorlevel 1 (
    "!APPCMD!" add site /name:"!IIS_SITE!" /bindings:"http/*:!HTTP_PORT!:" /physicalPath:"!IIS_ROOT!" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao criar site IIS. Porta !HTTP_PORT! pode estar em uso."
        call :pend "Criar site !IIS_SITE! manualmente no IIS Manager (porta !HTTP_PORT!, path !IIS_ROOT!)"
    ) else (
        call :ok "Site !IIS_SITE! criado (porta !HTTP_PORT!)"
    )
) else (
    call :skip "Site !IIS_SITE! ja existe"
)
"!APPCMD!" set app "!IIS_SITE!/" /applicationPool:"!IIS_POOL!" >> "!LOG!" 2>&1
"!APPCMD!" start site "!IIS_SITE!" >> "!LOG!" 2>&1

REM Generate web.config with proper escaping via PowerShell
powershell -NoProfile -Command ^
  "$xml = @'`n<?xml version=\"1.0\" encoding=\"UTF-8\"?>`n<configuration>`n  <system.webServer>`n    <rewrite>`n      <rules>`n        <rule name=\"API Reverse Proxy\" stopProcessing=\"true\">`n          <match url=\"^(api/.*|health|docs|redoc|openapi.json)(.*)$\" />`n          <action type=\"Rewrite\" url=\"http://127.0.0.1:!API_PORT!/{R:0}\" />`n        </rule>`n        <rule name=\"SPA Fallback\" stopProcessing=\"true\">`n          <match url=\"(.*)\" />`n          <conditions>`n            <add input=\"{REQUEST_FILENAME}\" matchType=\"IsFile\" negate=\"true\" />`n            <add input=\"{REQUEST_FILENAME}\" matchType=\"IsDirectory\" negate=\"true\" />`n          </conditions>`n          <action type=\"Rewrite\" url=\"/index.html\" />`n        </rule>`n      </rules>`n    </rewrite>`n  </system.webServer>`n</configuration>`n'@; $xml | Set-Content -Path '!IIS_ROOT!\web.config' -Encoding UTF8 -Force" >> "!LOG!" 2>&1

REM Verify web.config was created
if not exist "!IIS_ROOT!\web.config" (
    REM Fallback: create web.config using echo
    (
    echo ^<?xml version="1.0" encoding="UTF-8"?^>
    echo ^<configuration^>
    echo   ^<system.webServer^>
    echo     ^<rewrite^>
    echo       ^<rules^>
    echo         ^<rule name="API Reverse Proxy" stopProcessing="true"^>
    echo           ^<match url="^^(api/.*^|health^|docs^|redoc^|openapi.json)(.*^)$" /^>
    echo           ^<action type="Rewrite" url="http://127.0.0.1:!API_PORT!/{R:0}" /^>
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
    ) > "!IIS_ROOT!\web.config"
)
call :ok "web.config gerado (API Proxy + SPA Fallback)"

REM Enable ARR proxy
if "!HAS_ARR!"=="1" (
    "!APPCMD!" set config -section:system.webServer/proxy /enabled:"True" /commit:apphost >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao habilitar ARR proxy."
        call :pend "No IIS Manager: servidor > Application Request Routing > Server Proxy Settings > Enable proxy"
    ) else (
        call :ok "ARR proxy habilitado"
    )
) else (
    call :info "ARR nao instalado — proxy sera habilitado apos instalacao manual do ARR"
)

REM ─── ETAPA 9/11: SERVICO WINDOWS (NSSM) ───────────────────────────────────
call :step "9/11" "Servico Windows (NSSM)"

if "!HAS_NSSM!"=="0" (
    call :skip "NSSM nao disponivel. Servico nao sera criado."
    call :pend "Apos instalar NSSM, executar:"
    call :pend "  nssm install !SVC! \"!APP!\venv\Scripts\python.exe\" \"-m uvicorn app.main:app --host 127.0.0.1 --port !API_PORT! --workers 2\""
    call :pend "  nssm set !SVC! AppDirectory \"!APP!\""
    call :pend "  nssm set !SVC! Start SERVICE_AUTO_START"
    call :pend "  nssm start !SVC!"
    goto :etapa10
)

set "NSSM_CMD=nssm"
if defined NSSM_BIN set "NSSM_CMD=!NSSM_BIN!"

REM Create logs directory
if not exist "!APP!\logs" mkdir "!APP!\logs"

REM Install or update service
sc query "!SVC!" >nul 2>&1
if errorlevel 1 (
    call :info "Instalando servico !SVC!..."
    "!NSSM_CMD!" install "!SVC!" "!APP!\venv\Scripts\python.exe" "-m uvicorn app.main:app --host 127.0.0.1 --port !API_PORT! --workers 2" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao instalar servico via NSSM."
        call :pend "Instalar servico manualmente: nssm install !SVC!"
        goto :etapa10
    )
    call :ok "Servico !SVC! instalado"
) else (
    call :skip "Servico !SVC! ja existe, atualizando configuracao..."
    "!NSSM_CMD!" set "!SVC!" Application "!APP!\venv\Scripts\python.exe" >> "!LOG!" 2>&1
    "!NSSM_CMD!" set "!SVC!" AppParameters "-m uvicorn app.main:app --host 127.0.0.1 --port !API_PORT! --workers 2" >> "!LOG!" 2>&1
)

REM Configure service parameters
"!NSSM_CMD!" set "!SVC!" AppDirectory "!APP!" >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" DisplayName "Dinamica Budget API" >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" Description "FastAPI backend - Sistema de Orcamentacao Dinamica Budget" >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" Start SERVICE_AUTO_START >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppStdout "!APP!\logs\stdout.log" >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppStderr "!APP!\logs\stderr.log" >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppRotateFiles 1 >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppRotateBytes 10485760 >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppEnvironmentExtra "SENTENCE_TRANSFORMERS_HOME=!APP!\ml_models" >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppExit Default Restart >> "!LOG!" 2>&1
"!NSSM_CMD!" set "!SVC!" AppRestartDelay 5000 >> "!LOG!" 2>&1
call :ok "Servico configurado (auto-start, log rotation, auto-restart em 5s)"

REM Start/restart service
"!NSSM_CMD!" restart "!SVC!" >> "!LOG!" 2>&1
if errorlevel 1 (
    "!NSSM_CMD!" start "!SVC!" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao iniciar servico !SVC!. Verifique logs em !APP!\logs"
        call :pend "Iniciar servico manualmente: nssm start !SVC! — verificar !APP!\logs\stderr.log"
    ) else (
        call :ok "Servico !SVC! iniciado"
    )
) else (
    call :ok "Servico !SVC! reiniciado"
)

REM ─── ETAPA 10/11: REGRAS DE FIREWALL ───────────────────────────────────────
:etapa10
call :step "10/11" "Regras de Firewall"

REM Remove old rules first (idempotent)
netsh advfirewall firewall delete rule name="Dinamica Budget HTTP" >nul 2>&1
netsh advfirewall firewall delete rule name="Dinamica Budget HTTPS" >nul 2>&1

netsh advfirewall firewall add rule name="Dinamica Budget HTTP" dir=in action=allow protocol=TCP localport=!HTTP_PORT! >nul 2>&1
if errorlevel 1 (
    call :warn "Falha ao criar regra HTTP (porta !HTTP_PORT!)"
) else (
    call :ok "Firewall: porta !HTTP_PORT! (HTTP) liberada"
)

netsh advfirewall firewall add rule name="Dinamica Budget HTTPS" dir=in action=allow protocol=TCP localport=443 >nul 2>&1
if errorlevel 1 (
    call :warn "Falha ao criar regra HTTPS (porta 443)"
) else (
    call :ok "Firewall: porta 443 (HTTPS) liberada"
)

REM ─── ETAPA 11/11: VALIDACAO ─────────────────────────────────────────────────
call :step "11/11" "Validacao e Health Check"

REM Health check — API direct (wait up to 60s)
call :info "Aguardando API iniciar (ate 60s)..."
powershell -NoProfile -Command "$ok=$false; 1..30 | ForEach-Object { try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1:!API_PORT!/health' -TimeoutSec 3; if($r.status -eq 'ok'){$ok=$true; break} } catch {}; Start-Sleep -Seconds 2 }; if($ok){exit 0}else{exit 1}" >nul 2>&1
if errorlevel 1 (
    call :warn "API nao respondeu em http://127.0.0.1:!API_PORT!/health (timeout 60s)"
    call :info "Causas comuns: servico nao iniciado, erro no .env, modelo ML nao encontrado"
    call :pend "Verificar health da API: curl http://127.0.0.1:!API_PORT!/health"
    call :pend "Verificar logs: type !APP!\logs\stderr.log"
) else (
    call :ok "API respondendo em http://127.0.0.1:!API_PORT!/health"
    REM Check embedder status
    for /f "delims=" %%e in ('powershell -NoProfile -Command "try{$r=Invoke-RestMethod -Uri 'http://127.0.0.1:!API_PORT!/health' -TimeoutSec 5; Write-Output $r.embedder_ready}catch{Write-Output 'unknown'}"') do set "EMB=%%e"
    if /i "!EMB!"=="True" (
        call :ok "Motor de busca semantica (embedder) ativo"
    ) else (
        call :warn "embedder_ready=!EMB! — modelo ML pode nao estar carregado"
        call :pend "Verificar se ml_models/ contem o modelo all-MiniLM-L6-v2 e reiniciar: nssm restart !SVC!"
    )
)

REM Health check — via IIS proxy
call :info "Testando acesso via IIS..."
powershell -NoProfile -Command "$ok=$false; 1..10 | ForEach-Object { try { $r=Invoke-RestMethod -Uri 'http://127.0.0.1/health' -TimeoutSec 3; if($r.status -eq 'ok'){$ok=$true; break} } catch {}; Start-Sleep -Seconds 2 }; if($ok){exit 0}else{exit 1}" >nul 2>&1
if errorlevel 1 (
    call :warn "IIS proxy nao respondeu em http://127.0.0.1/health"
    call :info "Verifique: URL Rewrite + ARR instalados, ARR proxy habilitado, web.config correto"
) else (
    call :ok "IIS proxy funcionando (http://127.0.0.1/health)"
)

REM Frontend check
powershell -NoProfile -Command "try{$r=Invoke-WebRequest -Uri 'http://127.0.0.1/' -TimeoutSec 5 -UseBasicParsing; if($r.StatusCode -eq 200 -and $r.Content -match 'html'){exit 0}else{exit 1}}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
    call :warn "Frontend nao respondeu em http://127.0.0.1/"
) else (
    call :ok "Frontend acessivel em http://127.0.0.1/"
)

REM ─── RESUMO FINAL ──────────────────────────────────────────────────────────

REM Detect access URL
set "ACCESS_URL=http://127.0.0.1"
if defined ACCESS_HOST if not "!ACCESS_HOST!"=="127.0.0.1" set "ACCESS_URL=http://!ACCESS_HOST!"

call :write_pend
echo.
echo !C!════════════════════════════════════════════════════════════════!N!
echo !C!  RESUMO DO DEPLOY!N!
echo !C!════════════════════════════════════════════════════════════════!N!
echo.
echo   !G!Concluidos: !C_OK!!N!    !C!Pulados: !C_SKIP!!N!    !Y!Alertas: !C_WARN!!N!
echo.

if !PEND! gtr 0 (
    echo   !Y!PENDENCIAS MANUAIS (!PEND!):!N!
    echo   ────────────────────────────────────────────
    for /l %%i in (1,1,!PEND!) do echo    %%i. !P_%%i!
    echo.
    echo   Arquivo de pendencias: !PENDF!
) else (
    echo   !G!INSTALACAO 100%% AUTOMATIZADA — nenhuma pendencia!!N!
)

echo.
echo   !W!ACESSO AO SISTEMA:!N!
echo   API (local):   http://127.0.0.1:!API_PORT!/health
echo   Frontend:      !ACCESS_URL!
echo   Swagger:       !ACCESS_URL!/docs
echo   Admin login:   !ACCESS_URL! (usar credenciais configuradas no .env)
echo.
echo   !W!LOGS:!N!
echo   Deploy:        !LOG!
echo   API stdout:    !APP!\logs\stdout.log
echo   API stderr:    !APP!\logs\stderr.log
echo   IIS:           C:\inetpub\logs\LogFiles\
echo.
echo   !W!COMANDOS UTEIS:!N!
echo   Reiniciar API: nssm restart !SVC!
echo   Status API:    nssm status !SVC!
echo   IIS Reset:     iisreset
echo.
echo !C!════════════════════════════════════════════════════════════════!N!

>> "!LOG!" echo.
>> "!LOG!" echo === DEPLOY CONCLUIDO: OK=!C_OK! SKIP=!C_SKIP! WARN=!C_WARN! PEND=!PEND! ===
>> "!LOG!" echo Fim: %date% %time%

endlocal
exit /b 0

REM ═══════════════════════════════════════════════════════════════════════════
:abort
REM ═══════════════════════════════════════════════════════════════════════════
echo.
echo   !R!DEPLOY INTERROMPIDO — erro critico encontrado.!N!
echo   Corrija o problema acima e reexecute o script.
if !PEND! gtr 0 (
    echo.
    echo   !Y!PENDENCIAS MANUAIS (!PEND!):!N!
    for /l %%i in (1,1,!PEND!) do echo    %%i. !P_%%i!
    echo.
    echo   Arquivo de pendencias: !PENDF!
)
echo.
echo   Log: !LOG!
>> "!LOG!" echo [ABORT] Deploy interrompido. OK=!C_OK! SKIP=!C_SKIP! WARN=!C_WARN! PEND=!PEND!
>> "!LOG!" echo Fim: %date% %time%
endlocal
exit /b 1