# Provider credentials (Supabase PAT, Cloudflare API token) live in Infisical at
# /deploy (prod). These are ephemeral resources: the provider reads them at run
# time using its OIDC machine identity, and the values exist only in memory for
# that phase, so they never transit CI as a file or land in the state file. See
# the supabase and cloudflare provider blocks in providers.tf.
ephemeral "infisical_secret" "supabase_admin_token" {
  name         = "supabase_admin_token"
  env_slug     = "prod"
  workspace_id = var.infisical_deploy_project_id
  folder_path  = "/deploy"
}

ephemeral "infisical_secret" "cloudflare_api_token" {
  name         = "cloudflare_api_token"
  env_slug     = "prod"
  workspace_id = var.infisical_deploy_project_id
  folder_path  = "/deploy"
}

# Terraform-generated values the backend needs at runtime are published to
# Infisical at /backend (prod). The backend pulls them on startup via its
# Universal Auth identity, so these never transit CI or land on disk as an artifact.
resource "infisical_secret" "supabase_url" {
  name         = "supabase_url"
  value        = module.supabase.api_url
  env_slug     = "prod"
  workspace_id = var.infisical_deploy_project_id
  folder_path  = "/backend"
}

resource "infisical_secret" "supabase_service_key" {
  name             = "supabase_service_key"
  value_wo         = module.supabase.service_role_key
  value_wo_version = 1
  env_slug         = "prod"
  workspace_id     = var.infisical_deploy_project_id
  folder_path      = "/backend"
}
