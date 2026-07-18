#!/usr/bin/env bash
# deploy.sh — Deploy the decent-visualizer split stack.
#
# Usage:
#   ./scripts/deploy.sh              # full deploy (backend + frontend)
#   ./scripts/deploy.sh --backend    # backend only (Docker → external VM)
#   ./scripts/deploy.sh --frontend   # frontend only (build → Cloudflare Pages)
#
# Prerequisites:
#   OCI_SSH_KEY pointing to the private deployment SSH key
#   Docker running locally
#   pnpm installed locally
#   wrangler installed (npm i -g wrangler) or npx will handle it
#   VM running (tofu apply done)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
INFRA_CONFIG="$ROOT_DIR/config/prod/infra.json"

# ── Resolve infrastructure from Terraform outputs ──────────────────────

VM_IP="$(jq -r '.external_vm.host' "$INFRA_CONFIG")"
VM_USER="$(jq -r '.external_vm.ssh_user' "$INFRA_CONFIG")"
OCI_SSH_KEY="${OCI_SSH_KEY:?Set OCI_SSH_KEY to the private OCI deployment SSH key}"
PAGES_PROJECT="$(jq -r '.cloudflare.pages_project' "$INFRA_CONFIG")"
BACKEND_URL="$(tofu -chdir="$INFRA_DIR" output -raw backend_url)"
FRONTEND_URL="$(tofu -chdir="$INFRA_DIR" output -raw frontend_url)"

echo "→ Backend:  $BACKEND_URL"
echo "→ Frontend: $FRONTEND_URL"

# ── Helpers ────────────────────────────────────────────────────────────

scp_to_vm() {
  local src="$1" dest="$2"
  scp -i "$OCI_SSH_KEY" -o BatchMode=yes \
    "$src" "${VM_USER}@${VM_IP}:$dest"
}

ssh_vm() {
  ssh -i "$OCI_SSH_KEY" -o BatchMode=yes \
    "${VM_USER}@${VM_IP}" "$@"
}

# ── Backend (Docker → external VM) ─────────────────────────────────────

deploy_backend() {
  echo ""
  echo "══ Backend ══"

  echo "→ Building Docker image..."
  docker build \
    --platform linux/arm64 \
    -t decent-visualizer-backend \
    -f "$BACKEND_DIR/Dockerfile" "$ROOT_DIR"

  echo "→ Exporting image..."
  local archive
  archive="$(mktemp -d)/backend-image.tar.gz"
  docker save decent-visualizer-backend | gzip > "$archive"
  echo "  ($(du -h "$archive" | cut -f1))"

  echo "→ Uploading image to VM..."
  scp_to_vm "$archive" "/tmp/backend-image.tar.gz"

  echo "→ Syncing docker-compose.yml..."
  scp_to_vm "$ROOT_DIR/docker-compose.yml" "/tmp/docker-compose.yml"

  echo "→ Loading image and restarting..."
  ssh_vm bash -s <<'REMOTE'
cd /opt/decent-visualizer
install -m 644 /tmp/docker-compose.yml docker-compose.yml
docker load < /tmp/backend-image.tar.gz
docker compose --env-file runtime.env up -d --remove-orphans
docker image prune -f
rm -f /tmp/backend-image.tar.gz /tmp/docker-compose.yml
REMOTE

  ssh_vm "docker compose -f /opt/app/docker-compose.yml ps"
  echo "✓ Backend deployed → $BACKEND_URL"
}

# ── Frontend (build local → Cloudflare Pages) ─────────────────────────

deploy_frontend() {
  echo ""
  echo "══ Frontend ══"

  echo "→ Building frontend (VITE_API_URL=$BACKEND_URL)..."
  cd "$FRONTEND_DIR"
  pnpm install --frozen-lockfile
  VITE_API_URL="$BACKEND_URL" pnpm build

  echo "→ Deploying to Cloudflare Pages..."
  npx wrangler pages deploy "$FRONTEND_DIR/dist" \
    --project-name="$PAGES_PROJECT" \
    --branch=main

  echo "✓ Frontend deployed → $FRONTEND_URL"
}

# ── Main ───────────────────────────────────────────────────────────────

cd "$ROOT_DIR"

case "${1:-}" in
  --backend)
    deploy_backend
    ;;
  --frontend)
    deploy_frontend
    ;;
  *)
    deploy_backend
    deploy_frontend
    ;;
esac

echo ""
echo "✓ Deploy complete"
echo "  Backend API:  $BACKEND_URL/api/health"
echo "  Frontend:     $FRONTEND_URL"
