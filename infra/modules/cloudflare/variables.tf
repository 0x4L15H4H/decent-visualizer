variable "account_id" {
  description = "Cloudflare account ID (from dashboard or API)"
  type        = string
}

variable "zone_id" {
  description = "Cloudflare zone ID for the domain (from dash.cloudflare.com → domain → Overview → right sidebar). Leave empty if not using a custom domain."
  type        = string
  default     = ""
}


variable "backend_ip" {
  description = "Static IP of the GCE backend (used for api.example.com A record)"
  type        = string
}

variable "project_name" {
  description = "Cloudflare Pages project name (becomes <name>.pages.dev)"
  type        = string
}

# ── Optional domain ────────────────────────────────────────────────────

variable "domain" {
  description = "Root domain (e.g. example.com). Leave empty to use *.pages.dev and bare IP."
  type        = string
  default     = ""
}

variable "api_subdomain" {
  description = "Subdomain for the backend API (e.g. api → api.example.com)"
  type        = string
  default     = "api"
}
