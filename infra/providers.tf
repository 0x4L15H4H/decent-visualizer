terraform {
  required_version = ">= 1.12"

  required_providers {
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
    oci = {
      source  = "oracle/oci"
      version = "~> 8.0"
    }
  }

  # OCI Object Storage pre-authenticated URL is supplied at init time as an
  # address backend setting. Keeping it out of source control prevents the
  # bearer URL from being persisted in this repository.
  backend "http" {
    update_method = "PUT"
  }
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

provider "oci" {
  auth                = "SecurityToken"
  config_file_profile = "GITHUB_WIF"
  region              = var.oci_region
}
