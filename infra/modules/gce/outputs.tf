output "external_ip" {
  description = "External IP of the GCE instance"
  value       = google_compute_address.static.address
}

output "instance_name" {
  description = "Name of the GCE instance"
  value       = google_compute_instance.app.name
}

output "instance_zone" {
  description = "Zone of the GCE instance"
  value       = var.zone
}
