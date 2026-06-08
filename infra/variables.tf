# ── GCP ────────────────────────────────────────────────────────────────

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

# ── Supabase ───────────────────────────────────────────────────────────

variable "supabase_org_id" {
  description = "Supabase organization slug (from dashboard URL or org settings)"
  type        = string
}

variable "supabase_admin_token" {
  description = "Supabase PAT for Terraform (create at supabase.com/dashboard/account/tokens)"
  type        = string
  sensitive   = true
}

variable "supabase_db_region" {
  description = "Supabase database region (e.g. us-east-1, eu-west-1)"
  type        = string
  default     = "us-east-1"
}

variable "supabase_db_password" {
  description = "Database password for the Supabase project"
  type        = string
  sensitive   = true
}

variable "supabase_instance_size" {
  description = "Supabase compute instance size (nano = 0.25 CPU, micro = 0.5 CPU, small = 1 CPU, medium = 2 CPU)"
  type        = string
  default     = "nano"

  validation {
    condition     = contains(["nano", "micro", "small", "medium", "large", "xlarge"], var.supabase_instance_size)
    error_message = "Instance size must be one of: nano, micro, small, medium, large, xlarge."
  }
}

# ── Cloudflare ─────────────────────────────────────────────────────────

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Pages + DNS Edit permission. Create at dash.cloudflare.com/profile/api-tokens."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID (visible at dash.cloudflare.com sidebar or in the URL)"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for the domain (from dash.cloudflare.com → domain → Overview → right sidebar)."
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
