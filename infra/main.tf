# ── Cloudflare Pages + DNS + Tunnel ───────────────────────────────────

module "cloudflare" {
  source = "./modules/cloudflare"

  account_id   = var.cloudflare_account_id
  zone_id      = var.cloudflare_zone_id
  domain       = var.domain
  project_name = var.cloudflare_pages_project
}
