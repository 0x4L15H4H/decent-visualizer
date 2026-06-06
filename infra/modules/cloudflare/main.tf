locals {
  has_domain = var.domain != "" && var.zone_id != ""
  api_url = local.has_domain ? "https://${var.api_subdomain}.${var.domain}" : "http://${var.backend_ip}"
}

# ── Pages project ─────────────────────────────────────────────────────

resource "cloudflare_pages_project" "frontend" {
  account_id        = var.account_id
  name              = var.project_name
}

# ── DNS records (only if a domain is set) ─────────────────────────────

# Backend API: api.example.com → GCE static IP, Cloudflare-proxied (free HTTPS)
resource "cloudflare_record" "api" {
  count   = local.has_domain ? 1 : 0
  zone_id = var.zone_id
  name    = var.api_subdomain
  type    = "A"
  content = var.backend_ip
  proxied = true
  ttl     = 1 # automatic
}

# Frontend: www.example.com → Cloudflare Pages CNAME (proxied for cert)
resource "cloudflare_record" "www" {
  count   = local.has_domain ? 1 : 0
  zone_id = var.zone_id
  name    = "www"
  type    = "CNAME"
  content = cloudflare_pages_project.frontend.subdomain
  proxied = true
  ttl     = 1
}

# Link www custom domain to the Pages project (triggers cert provisioning)
resource "cloudflare_pages_domain" "www" {
  count        = local.has_domain ? 1 : 0
  account_id   = var.account_id
  project_name = cloudflare_pages_project.frontend.id
  domain       = "www.${var.domain}"
  depends_on   = [cloudflare_record.www]
}

# ── Page Rules: redirect bare domain → www ───────────────────────────
# (Pages cannot host a proxied A record for the bare domain.
#  The bare domain's A record points to Cloudflare's edge; this page
#  rule redirects <domain>/* → www.<domain>/* with a 301.)

resource "cloudflare_page_rule" "redirect_bare_to_www" {
  count    = local.has_domain ? 1 : 0
  zone_id  = var.zone_id
  target   = "${var.domain}/*"
  priority = 1
  actions {
    forwarding_url {
      url         = "https://www.${var.domain}/$1"
      status_code = 301
    }
  }
}
