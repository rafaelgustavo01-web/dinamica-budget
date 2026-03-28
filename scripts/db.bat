@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  db.bat — Abre o pgcli conectado ao banco dinamica_budget
REM
REM  Uso:
REM    scripts\db.bat              → conecta com DATABASE_URL do .env
REM    scripts\db.bat prod         → conecta com DATABASE_URL_PROD do .env
REM    scripts\db.bat --help       → mostra ajuda do pgcli
REM ─────────────────────────────────────────────────────────────────────────────

setlocal

REM Lê DATABASE_URL do .env se não estiver no ambiente
if "%DATABASE_URL%"=="" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if "%%A"=="DATABASE_URL" set DATABASE_URL=%%B
    )
)

REM Fallback para conexão padrão de desenvolvimento
if "%DATABASE_URL%"=="" (
    set DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dinamica_budget
)

REM pgcli usa URL no formato postgresql:// (sem +asyncpg)
set PGCLI_URL=%DATABASE_URL:postgresql+asyncpg://=postgresql://%

echo [pgcli] Conectando em: %PGCLI_URL%
echo [pgcli] Dica: \dt  lista tabelas  ^|  \d tabela  descreve  ^|  \q  sai
echo.

.venv\Scripts\pgcli.exe %PGCLI_URL% %*

endlocal
