#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  FASE 2 — Setup interno WSL2: Docker + GitHub Actions Runner
#  Chamado automaticamente pelo script fase2-configurar-deploy.ps1
#  NÃO execute este arquivo manualmente.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

RUNNER_TOKEN="__RUNNER_TOKEN__"   # substituído pelo script PS
REPO_URL="__REPO_URL__"           # substituído pelo script PS
RUNNER_NAME="__RUNNER_NAME__"     # substituído pelo script PS

RUNNER_DIR="$HOME/actions-runner"

echo ""
echo "=== [1/5] Atualizando pacotes ==="
sudo apt-get update -q

echo ""
echo "=== [2/5] Instalando Docker Engine ==="
# Remover versões antigas se existirem
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Dependências
sudo apt-get install -y -q \
    ca-certificates curl gnupg lsb-release apt-transport-https

# Chave GPG oficial Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Repositório Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -q
sudo apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Permite rodar docker sem sudo
sudo usermod -aG docker "$USER"

echo "✅ Docker instalado: $(docker --version 2>/dev/null || echo 'precisa reiniciar sessão')"

echo ""
echo "=== [3/5] Habilitando systemd no WSL2 (para runner como serviço) ==="
WSL_CONF="/etc/wsl.conf"
if ! grep -q "\[boot\]" "$WSL_CONF" 2>/dev/null; then
    printf '[boot]\nsystemd=true\n' | sudo tee "$WSL_CONF"
    echo "✅ systemd habilitado em $WSL_CONF"
else
    echo "✅ systemd já configurado."
fi

echo ""
echo "=== [4/5] Instalando GitHub Actions Runner ==="
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Obter versão mais recente
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest \
    | grep '"tag_name"' | sed 's/.*"v\([^"]*\)".*/\1/')
echo "Baixando runner v${RUNNER_VERSION}..."

curl -sL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
    | tar -xz

echo "Configurando runner..."
./config.sh \
    --url  "$REPO_URL" \
    --token "$RUNNER_TOKEN" \
    --name  "$RUNNER_NAME" \
    --labels "self-hosted,Linux,producao" \
    --work  "_work" \
    --unattended

echo ""
echo "=== [5/5] Instalando runner como serviço systemd ==="
sudo ./svc.sh install "$USER"
sudo ./svc.sh start

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP WSL2 CONCLUÍDO                                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Runner instalado em: $RUNNER_DIR"
echo "Status do serviço:"
sudo ./svc.sh status || true
