ephemeral "infisical_secret" "cloudflare_api_token" {
  name         = "cloudflare_api_token"
  env_slug     = "prod"
  workspace_id = var.infisical_deploy_project_id
  folder_path  = "/deploy"
}
