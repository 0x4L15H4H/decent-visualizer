output "pages_url" {
  description = "Default Cloudflare Pages URL (always available)"
  value       = "https://${cloudflare_pages_project.frontend.subdomain}"
}

output "api_url" {
  description = "Public API URL (https://api.<domain>)"
  value       = local.api_url
}

output "tunnel_token" {
  description = "Token used by cloudflared on the VM to run the API tunnel"
  value       = cloudflare_tunnel.api.tunnel_token
  sensitive   = true
}
