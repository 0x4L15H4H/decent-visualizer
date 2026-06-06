terraform {
  required_version = ">= 1.8"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Optional: use GCS to store state remotely (recommended for teams)
  # backend "gcs" {
  #   bucket = "<your-state-bucket>"
  #   prefix = "decent-visualizer"
  # }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

provider "supabase" {
  access_token = var.supabase_admin_token
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
