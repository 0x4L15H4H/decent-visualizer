# Decent Visualizer

A split-stack app: Python/FastAPI backend on GCE, React/Vite frontend on Cloudflare Pages, Supabase for the database.

## Architecture

```
Browser
  │
  ├─ https://www.example.com ──► Cloudflare Pages (React/Vite, CDN-hosted)
  │                                      │
  │                                      │ API calls
  │                                      ▼
  └─ https://api.example.com ──► Cloudflare Edge
                                         │
                                         │ Cloudflare Tunnel (cloudflared dials out)
                                         ▼
                                  GCE VM e2-micro (FastAPI)
                                         │
                                         │ Supabase client (service role key)
                                         ▼
                                  Supabase (Postgres + REST API)
```

- **Frontend**: React/Vite SPA deployed to Cloudflare Pages, served from Cloudflare's CDN with no origin server.
- **Backend**: Python/FastAPI running in Docker on a GCE `e2-micro` VM (GCP Always Free tier). Not exposed on any public port.
- **Tunnel**: `cloudflared` runs on the VM and dials out to Cloudflare, which routes `api.<domain>` to `localhost` on the VM. The VM firewall stays fully closed and its IP is never public.
- **Database**: Supabase (managed Postgres). The backend connects using the service role key; the frontend never touches the database directly.

## Deployment

CI/CD runs on GitHub Actions. The `infra` job runs OpenTofu on every push to provision infrastructure. The `backend` and `frontend` jobs deploy when their respective files change.

### Prerequisites

- GCP project with billing enabled
- Cloudflare account with your domain added
- Supabase account with an org created
- Infisical project

### 1. GCP Setup

Run the one-time setup script to enable APIs, create the Workload Identity pool, create the Terraform service account, and bootstrap the GCS state bucket. Edit `REPO` and `PROJECT_ID` at the top of the script first:

```bash
bash scripts/gcp-setup.sh
```

The script prints `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` at the end. You will need them in step 3.

### 2. Infisical Secrets

Add the following secrets to Infisical under the `prod` environment:

| Secret | Value |
|---|---|
| `SUPABASE_ADMIN_TOKEN` | Supabase PAT. Create one at supabase.com/dashboard/account/tokens. |
| `SUPABASE_SERVICE_KEY` | Supabase service role key. Find it under Settings → API in the Supabase dashboard. |
| `SUPABASE_DB_PASSWORD` | Database password for the Supabase project. Generate with `openssl rand -base64 32` and store it before the first `tofu apply`. |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with `Account / Cloudflare Pages / Edit`, `Account / Zero Trust / Edit`, `Account / Cloudflare Tunnel / Edit`, `Zone / DNS / Edit`, and `Zone / Page Rules / Edit` permissions. |

### 3. GitHub Secrets

Add the following at **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `INFISICAL_IDENTITY_ID` | Machine identity ID from Infisical (Organization Settings → Machine Identities). Set auth method to OIDC, issuer `https://token.actions.githubusercontent.com`, audience `https://github.com/YOUR_GITHUB_ORG`. |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Printed by `gcp-setup.sh`, e.g. `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`. |
| `GCP_SERVICE_ACCOUNT` | Printed by `gcp-setup.sh`, e.g. `terraform@my-project.iam.gserviceaccount.com`. |

### 4. Non-Secret Config

Copy the example tfvars file and fill in your values:

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

| Variable | Description |
|---|---|
| `gcp_project_id` | GCP project ID. |
| `gcp_region` | GCP region. Must be `us-east1`, `us-central1`, or `us-west1` (Always Free). |
| `gcp_zone` | GCP zone, e.g. `us-east1-b`. |
| `vm_machine_type` | `e2-micro` (free), `e2-small`, or `e2-medium`. |
| `vm_boot_disk_size_gb` | Boot disk size in GB. Always Free allows up to 30 GB. |
| `supabase_org_id` | Supabase org slug from the dashboard URL. |
| `supabase_db_region` | Supabase region, e.g. `us-east-1`. |
| `cloudflare_account_id` | Cloudflare account ID from the dashboard sidebar. |
| `cloudflare_zone_id` | Zone ID from the domain's Overview page. |
| `domain` | Root domain, e.g. `example.com`. The frontend is served at `www.<domain>` and the API at `api.<domain>`. |

### 5. First deploy

Push to `main` or trigger the workflow manually from the Actions tab. On first run, OpenTofu will provision all infrastructure. Subsequent pushes deploy only what changed.
