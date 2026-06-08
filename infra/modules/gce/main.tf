# ── Networking ────────────────────────────────────────────────────────
# No inbound HTTP rule: the backend is reached only through the Cloudflare
# Tunnel (cloudflared dials out), so no public port is exposed. SSH for
# deploys is covered by the default network's allow-ssh rule.

# Static external IP for the VM (used for SSH / deploys)
resource "google_compute_address" "static" {
  name   = "${var.name}-ip"
  region = var.region
}

# ── GCE Instance ──────────────────────────────────────────────────────

resource "google_compute_instance" "app" {
  name         = var.name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = var.disk_size_gb
      type  = "pd-standard" # Always Free = pd-standard; pd-ssd costs extra
    }
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip = google_compute_address.static.address
    }
  }

  metadata = {
    startup-script = templatefile("${path.module}/startup.sh", {
      name              = var.name
      supabase_url      = var.supabase_url
      supabase_key      = var.supabase_service_key
      cors_origin       = var.cors_origin
      cloudflared_token = var.cloudflared_token
    })
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  allow_stopping_for_update = true
}
