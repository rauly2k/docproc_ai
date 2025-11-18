variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "docai-mvp-prod"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "database_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "POSTGRES_15"
}

variable "database_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "allowed_cors_origins" {
  description = "Allowed CORS origins for API Gateway"
  type        = list(string)
  default     = ["https://docproc-ai.vercel.app", "http://localhost:5173"]
}
