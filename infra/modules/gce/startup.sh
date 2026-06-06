#!/bin/bash
# GCE startup script — provisions Docker for the decent-visualizer backend API.
# The frontend is hosted separately on Cloudflare Pages.
# Template variables are injected by Terraform's templatefile().
set -euo pipefail

NAME="${name}"
SUPABASE_URL="${supabase_url}"
SUPABASE_SERVICE_KEY="${supabase_key}"
CORS_ORIGIN="${cors_origin}"

APP_DIR="/opt/app"

log() { echo "[startup-$(date +%H:%M:%S)] $*"; }

# ── System packages ────────────────────────────────────────────────────

log "Installing base packages..."
apt-get update -qq
apt-get install -y -qq \
  ca-certificates curl gnupg apt-transport-https

# ── Docker ─────────────────────────────────────────────────────────────

log "Installing Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

log "Docker installed: $(docker --version)"
log "Docker Compose: $(docker compose version)"

# ── App user + directory ───────────────────────────────────────────────

log "Setting up $NAME user and directory..."
useradd --system --create-home --shell /bin/bash --groups docker appuser 2>/dev/null || true
mkdir -p "$APP_DIR/backend"
chown -R appuser:appuser "$APP_DIR"

# ── Backend .env (written by Terraform; deploy script skips it) ───────

log "Writing backend .env..."
cat > "$APP_DIR/backend/.env" <<ENV
SUPABASE_URL=$SUPABASE_URL
SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
CORS_ORIGINS=$CORS_ORIGIN
ENV
chown appuser:appuser "$APP_DIR/backend/.env"
chmod 600 "$APP_DIR/backend/.env"

log "Startup complete. Deploy with scripts/deploy.sh."
