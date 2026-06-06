# Set properties
REPO="enervator/decent-visualizer"
PROJECT_ID="decent-visualizer"

# Derived properties
PROJECT_NUM="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')"
SA="terraform@${PROJECT_ID}.iam.gserviceaccount.com"

# Create the workload identity pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="$PROJECT_ID" --location="global"

# Add GitHub as an OIDC provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="$PROJECT_ID" --location="global" \
  --workload-identity-pool="github-pool" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == '${REPO}'"

# Create Terraform service account
gcloud iam service-accounts create "terraform" \
  --project="$PROJECT_ID" \
  --display-name="OpenTofu / GitHub Actions"

# Allow this repo to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}"

# Grant IAM roles needed by OpenTofu and the deploy workflow
ROLES=(
  roles/compute.admin
  roles/iam.serviceAccountUser
)

for ROLE in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA}" \
    --role="$ROLE"
done

echo ""
echo "GCP_WORKLOAD_IDENTITY_PROVIDER=projects/${PROJECT_NUM}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
echo "GCP_SERVICE_ACCOUNT=${SA}"
