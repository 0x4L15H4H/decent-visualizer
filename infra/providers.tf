terraform {
  required_version = ">= 1.12"

  required_providers {
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
