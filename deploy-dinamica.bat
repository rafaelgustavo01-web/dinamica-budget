@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>&1
title ══ Dinamica Budget — Instalador Nativo v2.0 ══

REM ============================================================================
REM  DINAMICA BUDGET — Instalador Nativo para Windows Server 2022
REM  Versao: 2.0 — Abril 2026
REM  Compativel: Windows Server 2019+ / Windows 10 21H2+
REM ============================================================================
REM  * Cada etapa detecta se ja foi concluida e pula automaticamente
REM  * Reexecucao segura (idempotente)
REM  * Ao final gera PENDENCIAS_MANUAIS.txt com acoes de intervencao manual
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
for /f "delims=" %%d in ('powershell -NoProfile -Command "(Get-Date).ToString(''yyyyMMdd_HHmmss'')"') do set "TS=%%d"
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

call :hdr "DINAMICA BUDGET — INSTALADOR NATIVO v2.0"
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
) else if !WIN_BUILD! geq 17763 (
    call :warn "Build !WIN_BUILD! (Server 2019). Recomendado: Server 2022 (20348+)"
) else (
    call :warn "Build !WIN_BUILD! abaixo do recomendado (20348+)"
)

REM Python check
where python >nul 2>&1
if errorlevel 1 (
    echo   !R![FAIL]!N! Python nao encontrado no PATH.
    echo          Instale Python 3.12.x: https://www.python.org/downloads/
    echo          MARQUE: [x] Add python.exe to PATH
    >> "!LOG!" echo [FAIL] Python nao encontrado
    call :pend "Instalar Python 3.12.x com 'Add to PATH': https://www.python.org/downloads/"
    goto :abort
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo !PY_VER! | findstr /r "^3\.12\." >nul 2>&1
if errorlevel 1 (
    call :warn "Python !PY_VER! detectado. Recomendado: 3.12.x"
) else (
    call :ok "Python !PY_VER!"
)

REM pip check
where pip >nul 2>&1
if errorlevel 1 (
    echo   !R![FAIL]!N! pip nao encontrado no PATH.
    >> "!LOG!" echo [FAIL] pip nao encontrado
    goto :abort
)
call :ok "pip disponivel"

REM Node.js check
where node >nul 2>&1
if errorlevel 1 (
    echo   !R![FAIL]!N! Node.js nao encontrado no PATH.
    echo          Instale Node.js LTS: https://nodejs.org/
    >> "!LOG!" echo [FAIL] Node.js nao encontrado
    call :pend "Instalar Node.js 20/22 LTS: https://nodejs.org/"
    goto :abort
)
for /f "delims=" %%v in ('node --version 2^>^&1') do set "NODE_VER=%%v"
call :ok "Node.js !NODE_VER!"

REM npm check
where npm >nul 2>&1
if errorlevel 1 (
    echo   !R![FAIL]!N! npm nao encontrado no PATH.
    >> "!LOG!" echo [FAIL] npm nao encontrado
    goto :abort
)
call :ok "npm disponivel"

REM NSSM check
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
        set "HAS_NSSM=0"
        call :warn "NSSM nao encontrado. Servico Windows nao sera criado automaticamente."
        call :pend "Instalar NSSM 2.24+: https://nssm.cc/download — copiar nssm.exe (win64) para C:\Windows\System32"
    )
)

REM IIS check
if not exist "!APPCMD!" (
    echo   !R![FAIL]!N! IIS nao instalado (appcmd.exe nao encontrado).
    echo          Instale o role Web-Server via Server Manager ou:
    echo          Install-WindowsFeature Web-Server -IncludeManagementTools
    >> "!LOG!" echo [FAIL] IIS nao instalado
    call :pend "Instalar IIS: Install-WindowsFeature Web-Server -IncludeManagementTools"
    goto :abort
)
call :ok "IIS instalado"

REM URL Rewrite check
if exist "%windir%\System32\inetsrv\rewrite.dll" (
    set "HAS_REWRITE=1"
    call :ok "URL Rewrite 2.1 detectado"
) else (
    set "HAS_REWRITE=0"
    call :warn "URL Rewrite 2.1 NAO detectado. Reverse proxy nao funcionara."
    call :pend "Instalar URL Rewrite 2.1: https://www.iis.net/downloads/microsoft/url-rewrite"
)

REM ARR check
if exist "%windir%\System32\inetsrv\requestRouter.dll" (
    set "HAS_ARR=1"
    call :ok "ARR 3.0 detectado"
) else (
    set "HAS_ARR=0"
    call :warn "ARR 3.0 NAO detectado. Reverse proxy nao funcionara."
    call :pend "Instalar ARR 3.0: https://www.iis.net/downloads/microsoft/application-request-routing"
)

REM PostgreSQL service check
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
        set "HAS_PG=0"
        call :warn "Servico PostgreSQL nao encontrado. Etapas de banco serao puladas."
        call :pend "Instalar PostgreSQL 16: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads"
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
        if errorlevel 1 (
            set "HAS_PG=0"
            call :warn "Falha ao iniciar !PG_SVC!. Etapas de banco serao puladas."
            call :pend "Iniciar PostgreSQL manualmente: net start !PG_SVC!"
        ) else (
            call :ok "PostgreSQL (!PG_SVC!) iniciado"
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

if exist "!APP!\venv\Scripts\python.exe" (
    call :skip "venv ja existe"
) else (
    call :info "Criando ambiente virtual..."
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

call :info "Instalando dependencias (pode levar 5-10 minutos na primeira vez)..."
"!PIP!" install -r "!APP!\requirements.txt" >> "!LOG!" 2>&1
if errorlevel 1 (
    call :warn "pip install falhou com requirements.txt direto. Tentando fallback..."
    "!PIP!" install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu >> "!LOG!" 2>&1
    "!PIP!" install -r "!APP!\requirements.txt" >> "!LOG!" 2>&1
    if errorlevel 1 (
        echo   !R![FAIL]!N! Falha ao instalar dependencias Python.
        echo          Verifique conexao com internet e o log: !LOG!
        >> "!LOG!" echo [FAIL] pip install requirements.txt falhou
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
    REM Parse DB password from existing .env for later use
    for /f "delims=" %%p in ('powershell -NoProfile -Command "$l=^(Get-Content '!APP!\.env' ^| Where-Object {$_ -match '^DATABASE_URL='}^); if^($l -match '://[^:]+:^([^@]+^)@'^){$Matches[1]}"') do set "DB_PASS=%%p"
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
set /p "PG_PASS=  Senha do usuario 'postgres' no PostgreSQL: "
if "!PG_PASS!"=="" (
    echo   A senha nao pode ser vazia.
    goto :prompt_pg
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
  echo DATABASE_URL=postgresql+asyncpg://postgres:!PG_PASS!@localhost:5432/dinamica_budget & ^
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
    >> "!APP!\.env" echo DATABASE_URL=postgresql+asyncpg://postgres:!PG_PASS!@localhost:5432/dinamica_budget
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

if not defined DB_PASS (
    call :warn "Senha do PostgreSQL nao disponivel. Pulando operacoes de banco."
    call :pend "Criar banco 'dinamica_budget' manualmente via pgAdmin"
    goto :etapa5
)

set "PGPASSWORD=!DB_PASS!"

REM Check if database exists
"!PSQL_BIN!" -U postgres -h localhost -tc "SELECT 1 FROM pg_database WHERE datname = '!DB_NAME!'" 2>nul | findstr "1" >nul 2>&1
if errorlevel 1 (
    call :info "Criando banco !DB_NAME!..."
    "!PSQL_BIN!" -U postgres -h localhost -c "CREATE DATABASE !DB_NAME!" >> "!LOG!" 2>&1
    if errorlevel 1 (
        call :warn "Falha ao criar banco. Verifique a senha do postgres."
        call :pend "Criar banco '!DB_NAME!' manualmente via pgAdmin (owner: postgres)"
        set "PGPASSWORD="
        goto :etapa5
    )
    call :ok "Banco !DB_NAME! criado"
) else (
    call :skip "Banco !DB_NAME! ja existe"
)

REM Create extensions
"!PSQL_BIN!" -U postgres -h localhost -d "!DB_NAME!" -c "CREATE EXTENSION IF NOT EXISTS vector;" >> "!LOG!" 2>&1
if errorlevel 1 (
    call :warn "Falha ao criar extensao pgvector. Verifique se pgvector esta instalado."
    call :pend "Instalar pgvector para PostgreSQL: https://github.com/pgvector/pgvector/releases"
    call :pend "Executar no banco: CREATE EXTENSION IF NOT EXISTS vector;"
) else (
    call :ok "Extensao pgvector ativa"
)

"!PSQL_BIN!" -U postgres -h localhost -d "!DB_NAME!" -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" >> "!LOG!" 2>&1
if errorlevel 1 (
    call :warn "Falha ao criar extensao pg_trgm."
) else (
    call :ok "Extensao pg_trgm ativa"
)

set "PGPASSWORD="

REM ─── ETAPA 5/11: MIGRACOES ALEMBIC ─────────────────────────────────────────
:etapa5
call :step "5/11" "Migracoes de banco (Alembic)"

pushd "!APP!"
"!PY!" -m alembic upgrade head >> "!LOG!" 2>&1
set "ARC=!ERRORLEVEL!"
popd

if !ARC! neq 0 (
    call :warn "Alembic upgrade head falhou (codigo !ARC!)."
    call :info "Causas comuns: PostgreSQL parado, banco nao criado, extensoes ausentes."
    call :pend "Executar manualmente: cd !APP! && venv\Scripts\python -m alembic upgrade head"
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
call :write_pend
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
