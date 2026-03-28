#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  db.sh — Abre o pgcli conectado ao banco dinamica_budget
#
#  Uso:
#    ./scripts/db.sh              → conecta com DATABASE_URL do .env
#    ./scripts/db.sh --help       → mostra ajuda do pgcli
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Carrega DATABASE_URL do .env se não estiver no ambiente
if [[ -z "${DATABASE_URL:-}" ]]; then
    if [[ -f ".env" ]]; then
        export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
    fi
fi

# Fallback para conexão padrão de desenvolvimento
DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/dinamica_budget}"

# pgcli usa URL no formato postgresql:// (sem +asyncpg)
PGCLI_URL="${DATABASE_URL/postgresql+asyncpg:\/\//postgresql://}"

echo "[pgcli] Conectando em: $PGCLI_URL"
echo "[pgcli] Dica: \dt  lista tabelas | \d tabela  descreve | \q  sai"
echo

.venv/bin/pgcli "$PGCLI_URL" "$@"
