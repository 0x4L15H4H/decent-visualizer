terraform {
  required_version = ">= 1.12"

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
    infisical = {
      source  = "Infisical/infisical"
      version = "~> 0.16"
    }
  }

  backend "gcs" {
    bucket = "decent-visualizer-tfstate"
    prefix = "decent-visualizer"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

provider "supabase" {
  access_token = ephemeral.infisical_secret.supabase_admin_token.value
}

provider "cloudflare" {
  api_token = ephemeral.infisical_secret.cloudflare_api_token.value
}

provider "infisical" {
  host = "https://app.infisical.com"
  auth = {
    oidc = {
      identity_id = var.infisical_deploy_identity_id
    }
  }
}
