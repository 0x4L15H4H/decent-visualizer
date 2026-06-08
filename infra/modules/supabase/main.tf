terraform {
  required_providers {
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
  }
}

resource "supabase_project" "this" {
  organization_id   = var.org_id
  name              = var.name
  database_password = var.db_password
  region            = var.db_region
  # instance_size omitted: the provider returns null after create even when the
  # value is set, causing "inconsistent result after apply". Manage compute size
  # via the Supabase dashboard instead.

  lifecycle {
    # Never reset the DB password after initial creation.
    ignore_changes = [database_password]
  }
}

# Fetch API keys for the project
data "supabase_apikeys" "this" {
  project_ref = supabase_project.this.id
}
