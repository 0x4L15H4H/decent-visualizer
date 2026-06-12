output "gcp_project_id" {
  description = "GCP project ID (used by scripts/deploy.sh)"
  value       = var.gcp_project_id
}

output "gcp_zone" {
  description = "GCP zone of the backend VM (used by scripts/deploy.sh)"
  value       = var.gcp_zone
}

output "vm_external_ip" {
  description = "External IP of the GCE backend API"
  value       = module.gce.external_ip
}

output "vm_ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "gcloud compute ssh ${var.project_slug} --zone=${var.gcp_zone} --project=${var.gcp_project_id}"
}

output "backend_url" {
  description = "URL to the backend API (https://api.<domain> with domain, else http://<IP>)"
  value       = module.cloudflare.api_url
}

output "frontend_url" {
  description = "Cloudflare Pages URL for the frontend"
  value       = module.cloudflare.pages_url
}

output "supabase_project_ref" {
  description = "Supabase project reference (use in dashboard: supabase.com/dashboard/project/<ref>)"
  value       = module.supabase.project_ref
}

output "supabase_api_url" {
  description = "Supabase REST API URL"
  value       = module.supabase.api_url
}

output "supabase_dashboard_url" {
  description = "Supabase dashboard URL for the project"
  value       = "https://supabase.com/dashboard/project/${module.supabase.project_ref}"
}

output "supabase_db_password" {
  description = "Generated Postgres password for the Supabase project"
  sensitive   = true
  value       = random_password.supabase_db.result
}
