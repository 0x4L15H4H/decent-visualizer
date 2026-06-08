variable "account_id" {
  description = "Cloudflare account ID (from dashboard or API)"
  type        = string
}

variable "zone_id" {
  description = "Cloudflare zone ID for the domain (from dash.cloudflare.com → domain → Overview → right sidebar)."
  type        = string
}

variable "backend_port" {
  description = "Port the backend listens on, reached by cloudflared over the VM's loopback"
  type        = number
  default     = 80
}

variable "project_name" {
  description = "Cloudflare Pages project name (becomes <name>.pages.dev)"
  type        = string
}

# ── Optional domain ────────────────────────────────────────────────────

variable "domain" {
  description = "Root domain (e.g. example.com)."
  type        = string
}

variable "api_subdomain" {
  description = "Subdomain for the backend API (e.g. api → api.example.com)"
  type        = string
  default     = "api"
}
