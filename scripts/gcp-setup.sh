#!/usr/bin/env bash
set -euo pipefail

# Set properties
REPO="0x4L15H4H/decent-visualizer"
PROJECT_ID="decent-visualizer"

# Derived properties
PROJECT_NUM="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SA="terraform@${PROJECT_ID}.iam.gserviceaccount.com"

step() { echo "==> $*" >&2; }

# Run a gcloud command and treat "already exists" as success.
ensure() {
  local output
  if ! output=$("$@" 2>&1); then
    if grep -qiE "ALREADY_EXISTS|already exists|you already own it" <<< "$output"; then
      echo "    (already exists, skipping)" >&2
    else
      echo "$output" >&2
      return 1
    fi
  fi
}

step "Enabling required GCP APIs (this can take ~60s)..."
gcloud services enable \
  iamcredentials.googleapis.com \
  iam.googleapis.com \
  compute.googleapis.com \
  storage.googleapis.com \
  --project="$PROJECT_ID"
echo "    done." >&2

step "Creating Workload Identity pool..."
ensure gcloud iam workload-identity-pools create "github-pool" \
  --project="$PROJECT_ID" --location="global"

step "Adding GitHub OIDC provider..."
ensure gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="$PROJECT_ID" --location="global" \
  --workload-identity-pool="github-pool" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${REPO}' && assertion.ref == 'refs/heads/main'"

step "Creating Terraform service account..."
ensure gcloud iam service-accounts create "terraform" \
  --project="$PROJECT_ID" \
  --display-name="OpenTofu / GitHub Actions"

step "Granting Workload Identity User to repo..."
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}"

step "Granting IAM roles to service account..."
ROLES=(
  roles/compute.admin
  roles/iam.serviceAccountUser
  roles/storage.admin
)

for ROLE in "${ROLES[@]}"; do
  echo "    $ROLE" >&2
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA}" \
    --role="$ROLE"
done

step "Bootstrapping GCS state bucket..."
STATE_BUCKET="${PROJECT_ID}-tfstate"
ensure gcloud storage buckets create "gs://${STATE_BUCKET}" \
  --project="$PROJECT_ID" \
  --location=US \
  --uniform-bucket-level-access
gcloud storage buckets update "gs://${STATE_BUCKET}" --versioning

echo "" >&2
step "Done. Add these as GitHub Actions secrets:"
echo ""
echo "GCP_WORKLOAD_IDENTITY_PROVIDER=projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
echo "GCP_SERVICE_ACCOUNT=${SA}"
