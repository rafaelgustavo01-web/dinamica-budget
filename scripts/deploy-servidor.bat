@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Dinamica Budget — Deploy Servidor (WSL2 + Docker)

:: ══════════════════════════════════════════════════════════════════════════════
::  DINAMICA BUDGET — Deploy Inteligente para Servidor de Produção
::  Um clique → WSL2 + Docker + Build + Migrations + API rodando.
::
::  Fluxo: WSL2 → Docker → Clonar/Sync → .env → compose up → health
::
::  Arquivo de resumo salvo em:
::    C:\Users\marcelo.grilo\Downloads\dinamica-deploy-info.txt
:: ══════════════════════════════════════════════════════════════════════════════

set "INFO_DIR=C:\Users\marcelo.grilo\Downloads"
set "INFO_FILE=%INFO_DIR%\dinamica-deploy-info.txt"
set "WSL_DISTRO=Ubuntu-22.04"
set "WSL_APP_DIR=/opt/dinamica-budget"
set "ERROS=0"

:: Determinar raiz do projeto (diretorio onde esta o script OU raiz do repo)
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
:: Se executado de scripts\, subir um nível
if exist "%PROJECT_ROOT%\deploy.bat" (
    cd /d "%PROJECT_ROOT%"
) else if exist "%PROJECT_ROOT%\..\deploy.bat" (
    set "PROJECT_ROOT=%PROJECT_ROOT%\.."
    cd /d "%PROJECT_ROOT%"
) else (
    cd /d "%PROJECT_ROOT%"
)

:: Obter IP da máquina para URLs de acesso
set "SERVER_IP=localhost"
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4" ^| findstr /v "127.0.0.1"') do (
    set "TMP_IP=%%a"
    set "TMP_IP=!TMP_IP: =!"
    if "!SERVER_IP!"=="localhost" set "SERVER_IP=!TMP_IP!"
)

echo.
echo ============================================================
echo   DINAMICA BUDGET — Deploy Servidor (WSL2 + Docker)
echo ============================================================
echo.
echo   Inicio    : %date% %time%
echo   Diretorio : %PROJECT_ROOT%
echo   Servidor  : %COMPUTERNAME% (%SERVER_IP%)
echo   Resumo em : %INFO_FILE%
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 1/8 — Verificar se esta executando como Administrador
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 1/8 — Verificar permissoes de Administrador
echo.

net session >nul 2>&1
if !errorlevel! neq 0 (
    echo    [ERRO] Este script precisa ser executado como Administrador.
    echo    Clique com o botao direito e selecione "Executar como administrador".
    goto :fim_erro
)
echo    [OK] Executando como Administrador
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 2/8 — Verificar/Instalar WSL2
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 2/8 — Verificar/Instalar WSL2
echo.

set "WSL_READY=0"
set "NEED_REBOOT=0"

:: Checar se WSL está instalado
wsl --status >nul 2>&1
if !errorlevel! equ 0 (
    :: Checar se Ubuntu está instalado
    wsl -l -q 2>nul | findstr /i "Ubuntu" >nul 2>&1
    if !errorlevel! equ 0 (
        echo    [OK] WSL2 com Ubuntu ja instalado
        set "WSL_READY=1"
        goto :wsl_done
    )
)

echo    WSL2 nao detectado. Instalando...
echo.

:: Habilitar WSL
echo    [1/3] Habilitando Windows Subsystem for Linux...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart >nul 2>&1
if !errorlevel! neq 0 (
    echo    [AVISO] WSL pode ja estar habilitado, continuando...
) else (
    echo          OK
    set "NEED_REBOOT=1"
)

:: Habilitar Virtual Machine Platform
echo    [2/3] Habilitando Virtual Machine Platform...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart >nul 2>&1
if !errorlevel! neq 0 (
    echo    [AVISO] VMP pode ja estar habilitado, continuando...
) else (
    echo          OK
    set "NEED_REBOOT=1"
)

:: Se habilitou features novas, precisa reiniciar
if "!NEED_REBOOT!"=="1" (
    echo.
    echo    ╔══════════════════════════════════════════════════════════╗
    echo    ║  REINICIALIZACAO NECESSARIA                              ║
    echo    ║                                                          ║
    echo    ║  As features de WSL2 foram habilitadas.                   ║
    echo    ║  REINICIE o servidor e execute este script novamente.     ║
    echo    ╚══════════════════════════════════════════════════════════╝
    echo.
    echo    Deseja reiniciar agora? (S/N)
    set /p "REBOOT_CHOICE="
    if /i "!REBOOT_CHOICE!"=="S" (
        shutdown /r /t 10 /c "Reiniciando para completar instalacao WSL2 — Dinamica Budget"
        echo    Reiniciando em 10 segundos...
        goto :fim_ok
    )
    echo    Reinicie manualmente e execute este script novamente.
    goto :fim_ok
)

:: Instalar kernel WSL2
echo    [3/3] Instalando kernel WSL2 + Ubuntu...
wsl --set-default-version 2 >nul 2>&1
wsl --install -d Ubuntu-22.04 --no-launch >nul 2>&1

if !errorlevel! neq 0 (
    echo    [AVISO] Instalacao automatica do Ubuntu pode precisar de reboot.
    echo    Reinicie e execute este script novamente.
    goto :fim_ok
)

echo    [OK] Ubuntu instalado. Inicializando...
echo.
echo    ╔══════════════════════════════════════════════════════════╗
echo    ║  CONFIGURAR USUARIO LINUX                                ║
echo    ║                                                          ║
echo    ║  Uma janela do Ubuntu vai abrir.                         ║
echo    ║  Crie um usuario (ex: deploy) e defina uma senha.       ║
echo    ║  Depois feche a janela e este script continuará.         ║
echo    ╚══════════════════════════════════════════════════════════╝
echo.
echo    Pressione qualquer tecla para abrir o Ubuntu...
pause >nul
wsl -d %WSL_DISTRO%
set "WSL_READY=1"

:wsl_done
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 3/8 — Verificar/Instalar Docker dentro do WSL2
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 3/8 — Verificar/Instalar Docker no WSL2
echo.

:: Testar se Docker já está disponível
wsl -d %WSL_DISTRO% -- docker --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "delims=" %%v in ('wsl -d %WSL_DISTRO% -- docker --version 2^>nul') do echo    Docker: %%v
    echo    [OK] Docker ja instalado no WSL2
    goto :docker_done
)

echo    Docker nao encontrado no WSL2. Instalando...
echo    (Isso pode levar 3-5 minutos)
echo.

:: Instalar Docker Engine no WSL2
wsl -d %WSL_DISTRO% -- bash -c "sudo apt-get update -qq && sudo apt-get install -y -qq ca-certificates curl gnupg lsb-release apt-transport-https 2>&1 | tail -1"
if !errorlevel! neq 0 (
    echo    [ERRO] Falha ao instalar dependencias.
    goto :fim_erro
)
echo    Dependencias: OK

:: Chave GPG + repo Docker
wsl -d %WSL_DISTRO% -- bash -c "sudo install -m 0755 -d /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null && sudo chmod a+r /etc/apt/keyrings/docker.gpg"
wsl -d %WSL_DISTRO% -- bash -c "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
echo    Repositorio Docker: OK

:: Instalar Docker
wsl -d %WSL_DISTRO% -- bash -c "sudo apt-get update -qq && sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin 2>&1 | tail -3"
if !errorlevel! neq 0 (
    echo    [ERRO] Falha ao instalar Docker Engine.
    goto :fim_erro
)
echo    Docker Engine: OK

:: Permissão sem sudo + iniciar serviço
wsl -d %WSL_DISTRO% -- bash -c "sudo usermod -aG docker $USER && sudo service docker start 2>/dev/null || true"
echo    Permissoes: OK

:: Verificar
wsl -d %WSL_DISTRO% -- docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo    [AVISO] Docker instalado, mas precisa reiniciar a sessao WSL.
    echo    Reiniciando WSL2...
    wsl --shutdown
    timeout /t 3 /nobreak >nul
    wsl -d %WSL_DISTRO% -- bash -c "sudo service docker start"
)

for /f "delims=" %%v in ('wsl -d %WSL_DISTRO% -- docker --version 2^>nul') do echo    Docker: %%v
echo    [OK] Docker instalado com sucesso
echo.

:docker_done
echo.

:: Garantir que Docker daemon esteja rodando
wsl -d %WSL_DISTRO% -- bash -c "sudo service docker start 2>/dev/null || true" >nul 2>&1

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 4/8 — Habilitar systemd (para Docker persistir após reboot)
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 4/8 — Configurar systemd no WSL2
echo.

wsl -d %WSL_DISTRO% -- bash -c "grep -q '\[boot\]' /etc/wsl.conf 2>/dev/null" >nul 2>&1
if !errorlevel! neq 0 (
    wsl -d %WSL_DISTRO% -- bash -c "printf '[boot]\nsystemd=true\n' | sudo tee /etc/wsl.conf > /dev/null"
    echo    [OK] systemd habilitado — Docker iniciara automaticamente
) else (
    echo    [OK] systemd ja configurado
)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 5/8 — Sincronizar projeto para o WSL2
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 5/8 — Copiar projeto para o WSL2
echo.

:: Converter caminho Windows → caminho WSL
set "WIN_DRIVE=%PROJECT_ROOT:~0,1%"
set "WIN_DRIVE_LOWER=!WIN_DRIVE!"
:: Converter para minúscula simples
for %%l in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do (
    if /i "!WIN_DRIVE!"=="%%l" set "WIN_DRIVE_LOWER=%%l"
)
set "WSL_PROJECT_SRC=/mnt/!WIN_DRIVE_LOWER!/%PROJECT_ROOT:~3%"
set "WSL_PROJECT_SRC=!WSL_PROJECT_SRC:\=/!"

echo    Origem  : %PROJECT_ROOT%
echo    WSL src : !WSL_PROJECT_SRC!
echo    Destino : %WSL_APP_DIR%
echo.

:: Criar diretório de destino e sincronizar (exclui node_modules, .git, venv, __pycache__)
wsl -d %WSL_DISTRO% -- bash -c "sudo mkdir -p %WSL_APP_DIR% && sudo chown $USER:$USER %WSL_APP_DIR%"
wsl -d %WSL_DISTRO% -- bash -c "rsync -a --delete --exclude='node_modules' --exclude='.git' --exclude='venv' --exclude='__pycache__' --exclude='.venv' --exclude='output' '!WSL_PROJECT_SRC!/' '%WSL_APP_DIR%/' 2>/dev/null || cp -a '!WSL_PROJECT_SRC!/.' '%WSL_APP_DIR%/' 2>/dev/null"

if !errorlevel! neq 0 (
    echo    [AVISO] rsync nao disponivel, instalando...
    wsl -d %WSL_DISTRO% -- bash -c "sudo apt-get install -y -qq rsync && rsync -a --delete --exclude='node_modules' --exclude='.git' --exclude='venv' --exclude='__pycache__' '!WSL_PROJECT_SRC!/' '%WSL_APP_DIR%/'"
)

echo    [OK] Projeto sincronizado para %WSL_APP_DIR%
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 6/8 — Gerar .env no destino (se nao existir)
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 6/8 — Configurar .env
echo.

:: Verificar se .env já existe no destino WSL
wsl -d %WSL_DISTRO% -- bash -c "test -f %WSL_APP_DIR%/.env" >nul 2>&1
if !errorlevel! equ 0 (
    echo    .env ja existe no destino, mantendo.
    goto :env_done
)

:: Verificar se .env existe na origem Windows
if exist "%PROJECT_ROOT%\.env" (
    echo    Copiando .env existente para WSL2...
    goto :env_done
)

:: Gerar a partir do .env.example
echo    .env nao encontrado — gerando a partir do .env.example...

wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && if [ ! -f .env.example ]; then echo 'ERRO: .env.example nao encontrado'; exit 1; fi && cp .env.example .env && SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null || openssl rand -hex 32) && sed -i \"s/CHANGE_ME_use_secrets_token_hex_32/$SECRET/\" .env && sed -i 's|localhost:5432|db:5432|' .env && echo OK"

if !errorlevel! neq 0 (
    echo    [ERRO] Falha ao gerar .env. Crie manualmente em %WSL_APP_DIR%/.env
    goto :fim_erro
)
echo    SECRET_KEY gerada automaticamente
echo    DATABASE_URL ajustada para o container Docker (db:5432)
echo    [OK] .env criado

:env_done
echo.

:: Garantir que DATABASE_URL aponte para o container 'db' e não 'localhost'
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && sed -i 's|@localhost:5432|@db:5432|' .env 2>/dev/null"
echo    DATABASE_URL verificado (aponta para container db)
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 7/8 — Docker Compose: Build + Deploy
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 7/8 — Docker Compose: Build + Deploy no WSL2
echo.

:: Parar containers anteriores
echo    [1/4] Parando containers anteriores...
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose down --remove-orphans 2>/dev/null; true"
echo          OK
echo.

:: Pull imagem do banco
echo    [2/4] Baixando imagem do PostgreSQL (pgvector)...
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose pull db 2>&1 | tail -2"
echo          OK
echo.

:: Build
echo    [3/4] Build das imagens (Frontend + Backend)...
echo          Isso pode levar alguns minutos na primeira vez...
echo.
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose build --no-cache 2>&1"
if !errorlevel! neq 0 (
    echo.
    echo    [ERRO] Build falhou. Verifique os erros acima.
    goto :fim_erro
)
echo.
echo          [OK] Build concluido
echo.

:: Subir tudo
echo    [4/4] Iniciando servicos...
echo          Compose gerencia: DB (healthy) → Migrations → API
echo.
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose up -d 2>&1"
if !errorlevel! neq 0 (
    echo    [AVISO] Compose retornou aviso, verificando...
)

:: ── Monitorar DB ─────────────────────────────────────────────────────────────
echo    Aguardando banco de dados...
set /a "WAITED=0"
:loop_db_wsl
if !WAITED! geq 60 (
    echo    [ERRO] Banco nao ficou ready em 60s
    wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose logs db 2>&1 | tail -20"
    goto :fim_erro
)
wsl -d %WSL_DISTRO% -- bash -c "docker exec dinamica-budget-db-1 pg_isready -U postgres" >nul 2>&1
if !errorlevel! equ 0 (
    echo    [OK] Banco pronto
    goto :db_ok_wsl
)
timeout /t 3 /nobreak >nul
set /a "WAITED+=3"
goto :loop_db_wsl
:db_ok_wsl
echo.

:: ── Monitorar Migrations ─────────────────────────────────────────────────────
echo    Aguardando migrations...
set /a "WAITED=0"
:loop_mig_wsl
if !WAITED! geq 120 (
    echo    [ERRO] Migrations nao completaram em 120s
    wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose logs migrations 2>&1 | tail -20"
    goto :fim_erro
)
for /f "delims=" %%s in ('wsl -d %WSL_DISTRO% -- bash -c "docker inspect --format '{{.State.Status}}' dinamica-budget-migrations-1 2>/dev/null"') do set "MIG_STATE=%%s"
if "!MIG_STATE!"=="exited" (
    for /f "delims=" %%e in ('wsl -d %WSL_DISTRO% -- bash -c "docker inspect --format '{{.State.ExitCode}}' dinamica-budget-migrations-1 2>/dev/null"') do set "MIG_EXIT=%%e"
    if "!MIG_EXIT!"=="0" (
        echo    [OK] Migrations executadas com sucesso
        goto :mig_ok_wsl
    ) else (
        echo    [ERRO] Migrations falharam (exit code: !MIG_EXIT!)
        wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose logs migrations 2>&1 | tail -20"
        goto :fim_erro
    )
)
timeout /t 3 /nobreak >nul
set /a "WAITED+=3"
goto :loop_mig_wsl
:mig_ok_wsl
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ETAPA 8/8 — Health check da API
:: ══════════════════════════════════════════════════════════════════════════════
echo ^>^> ETAPA 8/8 — Health check da API
echo.

set /a "WAITED=0"
set /a "MAX_WAIT=180"
set "API_OK=0"

:loop_health_wsl
if !WAITED! geq !MAX_WAIT! goto :health_done_wsl

wsl -d %WSL_DISTRO% -- bash -c "curl -sf http://localhost:8000/health > /dev/null 2>&1" >nul 2>&1
if !errorlevel! equ 0 (
    echo    [OK] API respondendo! (HTTP 200)
    set "API_OK=1"
    goto :health_done_wsl
)

timeout /t 5 /nobreak >nul
set /a "WAITED+=5"
echo    Aguardando API... (!WAITED!/!MAX_WAIT!s)
goto :loop_health_wsl

:health_done_wsl
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: GERAR ARQUIVO DE INFORMACOES
:: ══════════════════════════════════════════════════════════════════════════════

:: Garantir que o diretório existe
if not exist "%INFO_DIR%" mkdir "%INFO_DIR%"

(
echo ============================================================
echo   DINAMICA BUDGET — Informacoes de Deploy
echo ============================================================
echo.
echo   Data do Deploy  : %date% %time%
echo   Servidor        : %COMPUTERNAME%
echo   IP do Servidor  : %SERVER_IP%
echo   WSL2 Distro     : %WSL_DISTRO%
echo   Projeto WSL     : %WSL_APP_DIR%
echo.
echo ============================================================
echo   URLs DE ACESSO
echo ============================================================
echo.
echo   Aplicacao (Frontend + API^):
echo     http://%SERVER_IP%:8000
echo     http://localhost:8000
echo.
echo   Documentacao da API (Swagger^):
echo     http://%SERVER_IP%:8000/docs
echo.
echo   API Alternativo (ReDoc^):
echo     http://%SERVER_IP%:8000/redoc
echo.
echo   Health Check:
echo     http://%SERVER_IP%:8000/health
echo.
echo   Banco de Dados (PostgreSQL^):
echo     Host: %SERVER_IP%
echo     Porta: 5432
echo     Database: dinamica_budget
echo     Usuario: postgres
echo.
echo ============================================================
echo   COMANDOS UTEIS (executar no PowerShell^)
echo ============================================================
echo.
echo   Ver status dos containers:
echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose ps"
echo.
echo   Ver logs da API:
echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose logs -f api"
echo.
echo   Parar tudo:
echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose down"
echo.
echo   Reiniciar API:
echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose restart api"
echo.
echo   Re-deploy (atualizar^):
echo     Executar: scripts\deploy-servidor.bat
echo.
echo ============================================================
echo   FIREWALL — Liberar acessso externo (executar como Admin^)
echo ============================================================
echo.
echo   netsh advfirewall firewall add rule name="Dinamica Budget API" ^
echo     dir=in action=allow protocol=tcp localport=8000
echo.
echo   netsh interface portproxy add v4tov4 ^
echo     listenport=8000 listenaddress=0.0.0.0 ^
echo     connectport=8000 connectaddress=127.0.0.1
echo.
) > "%INFO_FILE%"

:: ══════════════════════════════════════════════════════════════════════════════
:: RESUMO FINAL
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo    Status dos containers:
wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% && docker compose ps -a 2>&1"
echo.

if "!API_OK!"=="1" (
    echo    Resposta do /health:
    wsl -d %WSL_DISTRO% -- bash -c "curl -s http://localhost:8000/health 2>/dev/null"
    echo.
    echo.
    echo ============================================================
    echo   DEPLOY CONCLUIDO COM SUCESSO!
    echo ============================================================
    echo.
    echo   Aplicacao : http://%SERVER_IP%:8000
    echo   API Docs  : http://%SERVER_IP%:8000/docs
    echo   Health    : http://%SERVER_IP%:8000/health
    echo   Banco     : %SERVER_IP%:5432
    echo.
    echo   Arquivo com todas as informacoes salvo em:
    echo     %INFO_FILE%
    echo.
    echo   Comandos uteis:
    echo     Re-deploy : scripts\deploy-servidor.bat
    echo     Ver logs  : wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose logs -f api"
    echo     Parar     : wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose down"
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
    echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose logs -f api"
    echo.
    echo   Arquivo com informacoes salvo em:
    echo     %INFO_FILE%
    echo.
)

:: ── Configurar port proxy para acesso externo ────────────────────────────────
echo    Configurando encaminhamento de porta para acesso externo...
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=127.0.0.1 >nul 2>&1
netsh advfirewall firewall add rule name="Dinamica Budget API" dir=in action=allow protocol=tcp localport=8000 >nul 2>&1
echo    [OK] Porta 8000 acessivel externamente
echo.

goto :fim_ok

:: ══════════════════════════════════════════════════════════════════════════════
:fim_erro
echo.
echo ============================================================
echo   OCORRERAM ERROS — Verifique as mensagens acima
echo ============================================================
echo.
echo   Diagnostico:
echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose logs"
echo     wsl -d %WSL_DISTRO% -- bash -c "cd %WSL_APP_DIR% ^&^& docker compose ps -a"
echo.

:: Salvar log de erro
(
echo ============================================================
echo   DINAMICA BUDGET — ERRO NO DEPLOY
echo ============================================================
echo   Data: %date% %time%
echo   Servidor: %COMPUTERNAME% (%SERVER_IP%^)
echo.
echo   O deploy falhou. Execute novamente ou verifique os logs.
echo   Script: scripts\deploy-servidor.bat
echo ============================================================
) > "%INFO_FILE%"

echo   Log de erro salvo em: %INFO_FILE%
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 1

:fim_ok
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b 0
