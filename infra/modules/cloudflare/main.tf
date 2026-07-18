terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

locals {
  api_url = "https://${var.api_subdomain}.${var.domain}"
}

# ── Pages project ─────────────────────────────────────────────────────

resource "cloudflare_pages_project" "frontend" {
  account_id        = var.account_id
  name              = var.project_name
  production_branch = "main"
}

# ── Cloudflare Tunnel for the backend API ─────────────────────────────
# Instead of exposing the VM's IP and opening a public port, cloudflared
# runs on the VM and dials *out* to Cloudflare. TLS is terminated at the
# edge; the origin firewall stays closed and the IP stays private.

# 32-byte base64 secret that identifies the tunnel.
resource "random_id" "tunnel_secret" {
  byte_length = 32
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "api" {
  account_id = var.account_id
  name       = "${var.project_name}-api"
  secret     = random_id.tunnel_secret.b64_std
  config_src = "cloudflare" # remotely-managed config (set below)
}

# Ingress: route the API hostname to the backend service on the private Docker
# network. cloudflared runs as a sidecar in the same Compose project.
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "api" {
  account_id = var.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.api.id

  config {
    ingress_rule {
      hostname = "${var.api_subdomain}.${var.domain}"
      service  = "http://backend:${var.backend_port}"
    }
    ingress_rule {
      service = "http_status:404"
    }
  }
}

# Backend API: api.example.com → tunnel (proxied CNAME, free HTTPS)
resource "cloudflare_record" "api" {
  zone_id          = var.zone_id
  name             = var.api_subdomain
  type             = "CNAME"
  content          = "${cloudflare_zero_trust_tunnel_cloudflared.api.id}.cfargotunnel.com"
  proxied          = true
  ttl              = 1 # automatic
  allow_overwrite  = true
}

# Frontend: www.example.com → Cloudflare Pages CNAME (proxied for cert)
resource "cloudflare_record" "www" {
  zone_id         = var.zone_id
  name            = "www"
  type            = "CNAME"
  content         = cloudflare_pages_project.frontend.subdomain
  proxied         = true
  ttl             = 1
  allow_overwrite = true
}

# Link www custom domain to the Pages project (triggers cert provisioning)
resource "cloudflare_pages_domain" "www" {
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
