variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "zone" {
  description = "GCP zone"
  type        = string
}

variable "name" {
  description = "Resource name prefix"
  type        = string
}

variable "machine_type" {
  description = "GCE machine type (e2-micro, e2-small, e2-medium)"
  type        = string
  default     = "e2-micro"
}

variable "disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 30
}

variable "supabase_url" {
  description = "Supabase REST API URL"
  type        = string
}

variable "supabase_service_key" {
  description = "Supabase service role key"
  type        = string
  sensitive   = true
}

variable "cors_origin" {
  description = "Allowed CORS origin for the backend"
  type        = string
  default     = "*"
}
