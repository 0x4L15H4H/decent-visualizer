# ── GCP ────────────────────────────────────────────────────────────────

variable "gcp_service_account" {
  description = "Email of the GCP service account used by GitHub Actions. Needs storage.objectAdmin permissions."
  type        = string
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for GCE"
  type        = string
  default     = "us-east1"

  validation {
    condition     = contains(["us-east1", "us-central1", "us-west1"], var.gcp_region)
    error_message = "Region must be one of the GCE Always Free regions: us-east1, us-central1, or us-west1."
  }
}

variable "gcp_zone" {
  description = "GCP zone for GCE"
  type        = string
  default     = "us-east1-b"
}

variable "vm_machine_type" {
  description = "VM machine type"
  type        = string
  default     = "e2-micro"

  validation {
    condition     = contains(["e2-micro", "e2-small", "e2-medium"], var.vm_machine_type)
    error_message = "Machine type must be e2-micro (free), e2-small (~$8/mo), or e2-medium (~$17/mo)."
  }
}

variable "vm_boot_disk_size_gb" {
  description = "Boot disk size in GB (Always Free allows up to 30GB standard PD)"
  type        = number
  default     = 30
}

# ── External VM ───────────────────────────────────────────────────────

variable "external_vm_host" {
  description = "Public IP address or DNS name of the externally managed deployment VM."
  type        = string
}

variable "external_vm_ssh_user" {
  description = "SSH user for the externally managed deployment VM."
  type        = string
  default     = "opc"
}

# ── Supabase ───────────────────────────────────────────────────────────

variable "supabase_org_id" {
  description = "Supabase organization slug (from dashboard URL or org settings)"
  type        = string
}

variable "supabase_db_region" {
  description = "Supabase database region (e.g. us-east-1, eu-west-1)"
  type        = string
  default     = "us-east-1"
}


# ── Cloudflare ─────────────────────────────────────────────────────────

variable "cloudflare_account_id" {
  description = "Cloudflare account ID (visible at dash.cloudflare.com sidebar or in the URL)"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for the domain (from dash.cloudflare.com → domain → Overview → right sidebar)."
  type        = string
}

variable "cloudflare_pages_project" {
  description = "Cloudflare Pages project name, which becomes <name>.pages.dev (globally unique)."
  type        = string
}

variable "domain" {
  description = "Root domain (e.g. example.com). The frontend is served at www.<domain> and the API at api.<domain> via Cloudflare Tunnel."
  type        = string
}

# ── Application ────────────────────────────────────────────────────────

variable "project_name" {
  description = "Human-readable project name (used for Supabase display name)"
  type        = string
  default     = "Decent Visualizer"
}

variable "project_slug" {
  description = "URL-safe project slug used for resource naming and the Pages site (<slug>.pages.dev)"
  type        = string
  default     = "decent-visualizer"
}

# ── Infisical ──────────────────────────────────────────────────────────

variable "infisical_deploy_identity_id" {
  description = "Infisical deploy/CI machine identity ID. Used by the Terraform provider (OIDC auth) to write backend secrets, and by CI's secrets-action to read deploy secrets."
  type        = string
}

variable "infisical_deploy_project_id" {
  description = "Infisical project (workspace) ID. Used by the deploy identity to read /deploy and write /backend secrets."
  type        = string
}
