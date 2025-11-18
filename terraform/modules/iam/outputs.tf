output "cloud_run_sa_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}

output "cloud_run_sa_id" {
  description = "Cloud Run service account ID"
  value       = google_service_account.cloud_run.id
}
