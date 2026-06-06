output "project_ref" {
  description = "Supabase project reference used in all API calls"
  value       = supabase_project.this.id
}

output "api_url" {
  description = "Supabase REST API base URL"
  value       = "https://${supabase_project.this.id}.supabase.co"
}

output "service_role_key" {
  description = "Service role API key (server-only, bypasses RLS)"
  value       = data.supabase_apikeys.this.service_role_key
  sensitive   = true
}
