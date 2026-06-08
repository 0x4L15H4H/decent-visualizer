locals {
  # Explicit CORS allow-list (credentialed CORS forbids a wildcard).
  cors_origin = join(",", [
    "https://${var.domain}",
    "https://www.${var.domain}",
    "https://${var.project_slug}.pages.dev",
  ])
}

# ── Supabase ───────────────────────────────────────────────────────────

module "supabase" {
  source = "./modules/supabase"

  org_id        = var.supabase_org_id
  name          = var.project_name
  db_region     = var.supabase_db_region
  db_password   = var.supabase_db_password
  instance_size = var.supabase_instance_size
}

# ── GCE Backend (API) ────────────────────────────────────────────

module "gce" {
  source = "./modules/gce"

  project_id   = var.gcp_project_id
  region       = var.gcp_region
  zone         = var.gcp_zone
  name         = var.project_slug
  machine_type = var.vm_machine_type
  disk_size_gb = var.vm_boot_disk_size_gb

  supabase_url         = module.supabase.api_url
  supabase_service_key = module.supabase.service_role_key
  cors_origin          = local.cors_origin
  cloudflared_token    = module.cloudflare.tunnel_token
}

# ── Cloudflare Pages + DNS + Tunnel ───────────────────────────────────

module "cloudflare" {
  source = "./modules/cloudflare"

  account_id   = var.cloudflare_account_id
  zone_id      = var.cloudflare_zone_id
  domain       = var.domain
  project_name = var.project_slug
}
