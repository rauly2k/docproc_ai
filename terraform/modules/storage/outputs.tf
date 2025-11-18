output "uploads_bucket_name" {
  description = "Uploads bucket name"
  value       = google_storage_bucket.uploads.name
}

output "processed_bucket_name" {
  description = "Processed files bucket name"
  value       = google_storage_bucket.processed.name
}

output "embeddings_bucket_name" {
  description = "Embeddings bucket name"
  value       = google_storage_bucket.embeddings.name
}
