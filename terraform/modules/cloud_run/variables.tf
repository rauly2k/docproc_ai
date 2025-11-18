variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "database_connection_name" {
  description = "Cloud SQL connection name"
  type        = string
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  sensitive   = true
}

variable "gcs_bucket_uploads" {
  description = "GCS bucket for uploads"
  type        = string
}

variable "gcs_bucket_processed" {
  description = "GCS bucket for processed files"
  type        = string
}

variable "pubsub_topics" {
  description = "Pub/Sub topic names"
  type = object({
    invoice_processing = string
    ocr_processing     = string
    summarization      = string
    rag_ingestion      = string
    document_filling   = string
  })
}

variable "cloud_run_sa_email" {
  description = "Cloud Run service account email"
  type        = string
}
