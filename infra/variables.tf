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

variable "external_vm_instance_ocid" {
  description = "OCI instance OCID used for the VM-only backup dynamic group."
  type        = string
}

variable "oci_tenancy_ocid" {
  description = "OCI tenancy OCID; tenancy is the root compartment for IAM and backup storage."
  type        = string
}

variable "oci_region" {
  description = "OCI region for Object Storage backups."
  type        = string
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
