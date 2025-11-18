output "api_gateway_url" {
  description = "API Gateway Cloud Run URL"
  value       = module.cloud_run.api_gateway_url
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = module.cloud_sql.connection_name
  sensitive   = true
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = module.cloud_sql.private_ip_address
  sensitive   = true
}

output "uploads_bucket" {
  description = "GCS bucket for uploads"
  value       = module.storage.uploads_bucket_name
}

output "processed_bucket" {
  description = "GCS bucket for processed files"
  value       = module.storage.processed_bucket_name
}

output "pubsub_topics" {
  description = "Pub/Sub topic names"
  value       = module.pubsub.topic_names
}

output "cloud_run_service_account" {
  description = "Cloud Run service account email"
  value       = module.iam.cloud_run_sa_email
}

output "worker_services" {
  description = "Worker Cloud Run service URLs"
  value       = module.cloud_run.worker_urls
}
