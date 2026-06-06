#!/usr/bin/env bash
# deploy.sh — Deploy the decent-visualizer split stack.
#
# Usage:
#   ./scripts/deploy.sh              # full deploy (backend + frontend)
#   ./scripts/deploy.sh --backend    # backend only (Docker → GCE)
#   ./scripts/deploy.sh --frontend   # frontend only (build → Cloudflare Pages)
#
# Prerequisites:
#   gcloud CLI authenticated
#   Docker running locally
#   pnpm installed locally
#   wrangler installed (npm i -g wrangler) or npx will handle it
#   VM running (terraform apply done)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ── Resolve infrastructure from Terraform outputs ──────────────────────

VM_IP="$(terraform -chdir="$INFRA_DIR" output -raw vm_external_ip)"
GCP_PROJECT="$(terraform -chdir="$INFRA_DIR" output -raw gcp_project_id)"
GCP_ZONE="$(terraform -chdir="$INFRA_DIR" output -raw gcp_zone)"
BACKEND_URL="$(terraform -chdir="$INFRA_DIR" output -raw backend_url)"
FRONTEND_URL="$(terraform -chdir="$INFRA_DIR" output -raw frontend_url)"

echo "→ Backend:  $BACKEND_URL"
echo "→ Frontend: $FRONTEND_URL"

# ── Helpers ────────────────────────────────────────────────────────────

scp_to_vm() {
  gcloud compute scp --quiet \
    --project="$GCP_PROJECT" --zone="$GCP_ZONE" \
    "$@" "appuser@decent-visualizer:"
}

ssh_vm() {
  gcloud compute ssh --quiet \
    --project="$GCP_PROJECT" --zone="$GCP_ZONE" \
    "appuser@decent-visualizer" -- "$@"
}

# ── Backend (Docker → GCE) ─────────────────────────────────────────────

deploy_backend() {
  echo ""
  echo "══ Backend ══"

  echo "→ Building Docker image..."
  docker build \
    --platform linux/amd64 \
    -t decent-visualizer-backend \
    -f "$BACKEND_DIR/Dockerfile" "$BACKEND_DIR"

  echo "→ Exporting image..."
  local archive
  archive="$(mktemp -d)/backend-image.tar.gz"
  docker save decent-visualizer-backend | gzip > "$archive"
  echo "  ($(du -h "$archive" | cut -f1))"

  echo "→ Uploading image to VM..."
  scp_to_vm "$archive" "/tmp/backend-image.tar.gz"

  echo "→ Syncing docker-compose.yml..."
  scp_to_vm "$ROOT_DIR/docker-compose.yml" "/opt/app/docker-compose.yml"

  echo "→ Loading image and restarting..."
  ssh_vm bash -s <<'REMOTE'
cd /opt/app
docker load < /tmp/backend-image.tar.gz
docker compose up -d --build --remove-orphans
docker image prune -f
rm -f /tmp/backend-image.tar.gz
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
    --project-name="decent-visualizer" \
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
