output "pages_url" {
  description = "Default Cloudflare Pages URL (always available)"
  value       = "https://${cloudflare_pages_project.frontend.subdomain}"
}

output "api_url" {
  description = "Public API URL — https://api.<domain> if domain set, else http://<IP>"
  value       = local.api_url
}

output "has_domain" {
  description = "Whether a custom domain is configured"
  value       = local.has_domain
}
