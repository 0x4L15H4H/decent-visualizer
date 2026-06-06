resource "supabase_project" "this" {
  organization_id   = var.org_id
  name              = var.name
  database_password = var.db_password
  region            = var.db_region
  instance_size     = var.instance_size

  lifecycle {
    # Never reset the DB password after initial creation
    ignore_changes = [database_password]
  }
}

# Fetch API keys for the project
data "supabase_apikeys" "this" {
  project_ref = supabase_project.this.id
}
