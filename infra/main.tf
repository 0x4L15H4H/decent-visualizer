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

# ── Cloudflare Pages + DNS + Tunnel ───────────────────────────────────

module "cloudflare" {
  source = "./modules/cloudflare"

  account_id   = var.cloudflare_account_id
  zone_id      = var.cloudflare_zone_id
  domain       = var.domain
  project_name = var.cloudflare_pages_project
}
