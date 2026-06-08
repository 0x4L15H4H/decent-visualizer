# ── Terraform state bucket ────────────────────────────────────────────
# The bucket is pre-created by the GCP setup script so the GCS backend works
# on the very first `tofu init`. The import block below adopts it into state
# automatically on the first apply; it's a no-op once the resource is managed.

import {
  to = google_storage_bucket.tfstate
  id = "decent-visualizer-tfstate"
}

resource "google_storage_bucket" "tfstate" {
  project                     = var.gcp_project_id
  name                        = "decent-visualizer-tfstate"
  location                    = "US"
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

resource "google_storage_bucket_iam_member" "tfstate_deployer" {
  bucket = google_storage_bucket.tfstate.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.gcp_service_account}"
}

locals {
  # Explicit CORS allow-list (credentialed CORS forbids a wildcard).
  cors_origin = join(",", [
    "https://${var.domain}",
    "https://www.${var.domain}",
    "https://${var.project_slug}.pages.dev",
  ])
}

# ── Supabase ───────────────────────────────────────────────────────────

# Generated, not stored externally: only tofu consumes it (the backend uses the
# service-role key). Retrieve with `tofu output -raw supabase_db_password`.
resource "random_password" "supabase_db" {
  length           = 32
  override_special = "!#$%&*()-_=+"
}

module "supabase" {
  source = "./modules/supabase"

  org_id      = var.supabase_org_id
  name        = var.project_name
  db_region   = var.supabase_db_region
  db_password = random_password.supabase_db.result
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

  cloudflared_token = module.cloudflare.tunnel_token
}

# ── Cloudflare Pages + DNS + Tunnel ───────────────────────────────────

module "cloudflare" {
  source = "./modules/cloudflare"

  account_id   = var.cloudflare_account_id
  zone_id      = var.cloudflare_zone_id
  domain       = var.domain
  project_name = var.project_slug
}
