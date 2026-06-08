#!/bin/bash
# GCE startup script — provisions Docker for the decent-visualizer backend API.
# The frontend is hosted separately on Cloudflare Pages.
# Template variables are injected by Terraform's templatefile().
set -euo pipefail

NAME="${name}"
SUPABASE_URL="${supabase_url}"
SUPABASE_SERVICE_KEY="${supabase_key}"
CORS_ORIGIN="${cors_origin}"
CLOUDFLARED_TOKEN="${cloudflared_token}"

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

# ── Cloudflare Tunnel (cloudflared) ─────────────────────────────────────
# Exposes the backend (bound to localhost) to Cloudflare's edge over an
# outbound connection — no inbound ports required.

log "Installing cloudflared..."
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
  -o /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
https://pkg.cloudflare.com/cloudflared $(. /etc/os-release && echo "$VERSION_CODENAME") main" \
  > /etc/apt/sources.list.d/cloudflared.list
apt-get update -qq
apt-get install -y -qq cloudflared

log "Registering cloudflared service..."
cloudflared service install "$CLOUDFLARED_TOKEN"

# ── Cloud Ops Agent (logging + agent metrics) ───────────────────────────
# Standard GCE metrics (CPU/disk/network) are free without an agent. The Ops
# Agent adds memory + log visibility. We trim its config to drop the agent's
# own self-metrics, the largest avoidable ingestion, to stay well within the
# free tier (50 GiB/mo logging; standard metrics are free).

log "Installing Cloud Ops Agent..."
curl -fsSL https://dl.google.com/cloudagents/add-google-cloud-ops-agent.sh \
  | bash -s -- --also-install

cat > /etc/google-cloud-ops-agent/config.yaml <<'OPSCFG'
logging:
  receivers:
    syslog:
      type: files
      include_paths:
        - /var/log/syslog
        - /var/log/messages
  service:
    pipelines:
      default_pipeline:
        receivers: [syslog]
metrics:
  receivers:
    hostmetrics:
      type: hostmetrics
      collection_interval: 60s
  processors:
    # Drop the agent's own self-metrics — the largest avoidable ingestion.
    exclude_agent:
      type: exclude_metrics
      metrics_pattern:
        - agent.googleapis.com/agent/*
  service:
    pipelines:
      default_pipeline:
        receivers: [hostmetrics]
        processors: [exclude_agent]
OPSCFG
systemctl restart google-cloud-ops-agent

log "Startup complete. Deploy with scripts/deploy.sh."
