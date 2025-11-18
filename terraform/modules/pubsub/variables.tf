variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cloud_run_sa_email" {
  description = "Cloud Run service account email"
  type        = string
}
