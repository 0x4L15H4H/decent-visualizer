# Decent Visualizer

A split-stack app: Python/FastAPI backend on GCE, React/Vite frontend on Cloudflare Pages, Supabase for the database.

The backend is **not** exposed on a public port. A [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (`cloudflared` running on the VM) dials out to Cloudflare, which terminates TLS at the edge and routes `https://api.<domain>` to the backend over the VM's loopback. This keeps the VM's firewall closed, hides its IP, and gives the HTTPS frontend an HTTPS API to call. Responses are gzip-compressed and the shot list endpoint returns a slim summary (no measurement time-series) to stay within the GCE free-tier egress budget.

## CI/CD

A single GitHub Actions workflow, **`ci.yml`**, handles everything. It uses path filters so each job only runs when its area changed (or via the `workflow_dispatch` target input):

- **`infra`** — runs OpenTofu on changes to `infra/`. Plans on PRs, applies on merge to main.
- **`backend`** — deploys the backend (Docker → GCE) on changes to `backend/` or `docker-compose.yml`.
- **`frontend`** — builds and deploys the frontend (→ Cloudflare Pages) on changes to `frontend/`.

### GitHub Secrets

These must be added at **Settings → Secrets and variables → Actions** in the GitHub repo.

| Secret | Value |
|---|---|
| `INFISICAL_IDENTITY_ID` | Machine identity ID from Infisical (Organization Settings → Machine Identities) — set auth method to OIDC, issuer `https://token.actions.githubusercontent.com`, audience `https://github.com/YOUR_GITHUB_ORG` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full WIF provider resource name, e.g. `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | Service account email used by OpenTofu and gcloud, e.g. `terraform@my-project.iam.gserviceaccount.com` |

### Infisical

Secrets are stored in Infisical under the **`prod`** environment of the **`decent-visualizer`** project. All OpenTofu variables are prefixed with `TF_VAR_` so they are automatically picked up by OpenTofu without any extra configuration.

| Secret name | Value |
|---|---|
| `TF_VAR_supabase_admin_token` | Supabase PAT — create at supabase.com/dashboard/account/tokens |
| `TF_VAR_supabase_service_key` | Supabase service role key — Settings → API in the Supabase dashboard |
| `TF_VAR_supabase_db_password` | Database password for the Supabase project — generate one with `openssl rand -base64 32` and store it here before running `tofu apply` for the first time |
| `TF_VAR_cloudflare_api_token` | Cloudflare API token with `Account / Cloudflare Pages / Edit`, `Account / Cloudflare Tunnel / Edit`, and `Zone / DNS Settings / Edit` permissions |

### Non-secret config (`infra/terraform.tfvars`)

Non-sensitive OpenTofu variables are committed directly to `infra/terraform.tfvars`. Copy `infra/terraform.tfvars.example` to get started:

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

| Variable | Description |
|---|---|
| `gcp_project_id` | GCP project ID |
| `gcp_region` | GCP region — must be `us-east1`, `us-central1`, or `us-west1` (Always Free) |
| `gcp_zone` | GCP zone, e.g. `us-east1-b` |
| `vm_machine_type` | `e2-micro` (free), `e2-small`, or `e2-medium` |
| `vm_boot_disk_size_gb` | Boot disk size — Always Free allows up to 30GB |
| `supabase_org_id` | Supabase org slug from dashboard URL |
| `supabase_db_region` | Supabase region, e.g. `us-east-1` |
| `supabase_instance_size` | `nano`, `micro`, `small`, `medium`, `large`, or `xlarge` |
| `cloudflare_account_id` | Cloudflare account ID from the dashboard sidebar |
| `cloudflare_zone_id` | Zone ID from the domain's Overview page |
| `domain` | Root domain, e.g. `example.com` — frontend served at `www.<domain>`, API at `api.<domain>` via Cloudflare Tunnel |

### GCP Workload Identity Federation setup

One-time setup to allow GitHub Actions to authenticate to GCP without a static key. Edit `REPO` and `PROJECT_ID` at the top of the script, then run:

```bash
bash scripts/gcp-oidc-setup.sh
```

The script prints `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` at the end — add both as repository secrets.
