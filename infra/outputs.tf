output "vm_external_ip" {
  description = "External host of the managed backend VM"
  value       = var.external_vm_host
}

output "vm_ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh -i <deploy-key> ${var.external_vm_ssh_user}@${var.external_vm_host}"
}

output "cloudflare_tunnel_token" {
  description = "Tunnel token used by the cloudflared Compose sidecar."
  sensitive   = true
  value       = module.cloudflare.tunnel_token
}

output "backend_url" {
  description = "URL to the backend API (https://api.<domain> with domain, else http://<IP>)"
  value       = module.cloudflare.api_url
}

output "frontend_url" {
  description = "Cloudflare Pages URL for the frontend"
  value       = module.cloudflare.pages_url
}

output "oci_backup_bucket" {
  description = "Private Object Storage bucket used for SQLite backups."
  value       = oci_objectstorage_bucket.sqlite_backups.name
}

output "oci_object_storage_namespace" {
  description = "Object Storage namespace used by the SQLite backup uploader."
  value       = data.oci_objectstorage_namespace.current.namespace
}
