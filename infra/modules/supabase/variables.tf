variable "org_id" {
  description = "Supabase organization slug"
  type        = string
}

variable "name" {
  description = "Project display name"
  type        = string
}

variable "db_region" {
  description = "Supabase database region"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

